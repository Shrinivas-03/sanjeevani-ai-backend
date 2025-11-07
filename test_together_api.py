import chromadb
from sentence_transformers import SentenceTransformer

# connect local DB
client = chromadb.PersistentClient(path="./flask_memory_store")
collection = client.get_or_create_collection("chat_history")

# embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# store one chat message
msg = "Home remedies for fever include tulsi tea and proper rest."
embedding = embedder.encode([msg])[0].tolist()

collection.add(ids=["msg1"], documents=[msg], embeddings=[embedding])

# retrieve it
query = "natural treatment for fever"
q_emb = embedder.encode([query])[0].tolist()

results = collection.query(query_embeddings=[q_emb], n_results=1)
print("🔎 Retrieved:", results["documents"][0])
