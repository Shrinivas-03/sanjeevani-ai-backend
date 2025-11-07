import os
import traceback
import together
from langchain_pinecone import PineconeVectorStore
from langchain_together import TogetherEmbeddings
from pinecone import Pinecone


def get_env(key: str, required: bool = True) -> str:
    """Safely get environment variable with error handling."""
    value = os.getenv(key)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


class RAGSystem:
    def __init__(self):
        print("[INFO] 🧠 Initializing RAG System...")

        # ✅ Load environment variables
        self.pinecone_api_key = get_env("pinecone_api_key")
        self.pinecone_environment = get_env("pinecone_environment")
        self.pinecone_index_name = get_env("pinecone_index_name")
        self.together_api_key = get_env(
            "TOGETHER_AI_API_KEY", required=False
        ) or get_env("together_api_key", required=False)

        # ✅ Configure Together API globally
        if self.together_api_key:
            os.environ["TOGETHER_API_KEY"] = self.together_api_key
            print("[INFO] ✅ Together API key configured.")

        # ✅ Initialize embeddings
        try:
            print("[INFO] Initializing Together embeddings...")
            self.embeddings = TogetherEmbeddings(
                model="togethercomputer/m2-bert-80M-8k-retrieval"
            )
            print("[INFO] ✅ Together embeddings initialized.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize embeddings: {e}")

        # ✅ Initialize Pinecone client (Serverless 3.x)
        try:
            print(
                f"[INFO] Connecting to Pinecone environment: {self.pinecone_environment}"
            )
            self.pinecone_client = Pinecone(
                api_key=self.pinecone_api_key, environment=self.pinecone_environment
            )

            # Get list of available indexes
            available_indexes = [i.name for i in self.pinecone_client.list_indexes()]
            print(f"[INFO] Available indexes: {available_indexes}")

            if self.pinecone_index_name not in available_indexes:
                raise ValueError(
                    f"Index '{self.pinecone_index_name}' not found in Pinecone. Available: {available_indexes}"
                )

            print(f"[INFO] ✅ Connected to Pinecone. Index: {self.pinecone_index_name}")

            # ✅ Create VectorStore (NO API key args)
            self.vectorstore = PineconeVectorStore.from_existing_index(
                index_name=self.pinecone_index_name, embedding=self.embeddings
            )

            self.retriever = self.vectorstore.as_retriever()
            print("[INFO] ✅ Pinecone retriever ready.")

        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Pinecone initialization failed: {e}")

        print("[INFO] ✅ RAG system fully initialized.\n")

    # -------------------------------------------------------------------------

    def get_response(self, query: str) -> str:
        """Retrieve context from Pinecone and generate Together AI response."""
        try:
            print(f"[INFO] 🔍 Processing query: {query}")
            docs = self.retriever.invoke(query)

            if not docs:
                print("[WARN] ⚠️ No documents found in Pinecone.")
                return "No relevant Ayurvedic knowledge found for your query."

            # Combine docs into context
            context = "\n".join([doc.page_content for doc in docs])
            prompt = f"""
            You are an Ayurvedic doctor. Use the context below to suggest safe and effective remedies.

            📚 Context:
            {context}

            ❓ User Query:
            {query}

            🧘 Provide concise, home-based Ayurvedic remedies.
            """

            response = together.chat.completions.create(
                model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                messages=[{"role": "user", "content": prompt}],
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[ERROR] ❌ Retrieval or response generation failed: {e}")
            traceback.print_exc()
            return f"Error fetching or generating response: {e}"
