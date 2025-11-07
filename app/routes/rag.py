import os
import traceback
import uuid
from datetime import datetime

import chromadb
from flask import Blueprint, jsonify, request
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from together import Together

rag_bp = Blueprint("rag", __name__, url_prefix="/api/rag")

# ==============================
# 🔧 ENVIRONMENT VARIABLES
# ==============================
PINECONE_API_KEY = os.getenv("pinecone_api_key")
PINECONE_INDEX_HOST = os.getenv("pinecone_host")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# ==============================
# 🧠 INITIALIZE CLIENTS
# ==============================
# Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(host=PINECONE_INDEX_HOST)

# ChromaDB (Local VectorDB for memory)
client = chromadb.PersistentClient(path="./flask_memory_store")
collection = client.get_or_create_collection("chat_history")

# Embedding model
EMBED_MODEL_NAME = os.getenv(
    "EMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)
embedder = SentenceTransformer(EMBED_MODEL_NAME)

# Together AI client
together_client = Together(api_key=TOGETHER_API_KEY)


# ==============================
# 🧩 MEMORY HANDLERS
# ==============================
def save_message(email, conversation_id, role, message_text, timestamp=None):
    """Store each message with embeddings and metadata by user email and conversation."""
    try:
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()
        embedding = embedder.encode([message_text])[0].tolist()
        doc_id = f"{email}-{conversation_id}-{timestamp}-{role}"
        collection.add(
            documents=[message_text],
            embeddings=[embedding],
            metadatas=[
                {
                    "email": email,
                    "timestamp": timestamp,
                    "role": role,
                    "conversation_id": conversation_id,
                }
            ],
            ids=[doc_id],
        )
    except Exception as e:
        print(f"[WARN] Failed to save message: {e}")


def get_conversation_history(email, conversation_id, limit=50):
    """Retrieve all messages for a given conversation."""
    try:
        results = collection.get(
            where={"$and": [{"email": email}, {"conversation_id": conversation_id}]}
        )
        if not results or not results["documents"]:
            return []

        msgs = sorted(
            zip(results["metadatas"], results["documents"]),
            key=lambda x: x[0].get("timestamp"),
        )
        return [{"role": meta["role"], "message": doc} for meta, doc in msgs[-limit:]]
    except Exception as e:
        print(f"[WARN] Failed to fetch conversation history: {e}")
        return []


def get_user_conversations(email):
    """Return list of unique conversation IDs for a given user."""
    try:
        results = collection.get(where={"email": email})
        if not results or not results["metadatas"]:
            return []
        convo_ids = list(
            {
                m["conversation_id"]
                for m in results["metadatas"]
                if "conversation_id" in m
            }
        )
        return convo_ids
    except Exception as e:
        print(f"[WARN] Failed to fetch conversations: {e}")
        return []


def get_short_memory(email, conversation_id, limit=10):
    """Retrieve last N messages for short-term context."""
    try:
        results = collection.get(
            where={"$and": [{"email": email}, {"conversation_id": conversation_id}]}
        )
        if not results or not results["documents"]:
            return []
        msgs = sorted(
            zip(results["metadatas"], results["documents"]),
            key=lambda x: x[0].get("timestamp"),
            reverse=True,
        )
        return [msg for meta, msg in msgs[:limit]]
    except Exception as e:
        print(f"[WARN] Failed to fetch short memory: {e}")
        return []


def get_long_memory(email, search_text=None):
    """Retrieve semantically relevant long-term memory across all conversations."""
    try:
        if search_text:
            query_embedding = embedder.encode([search_text])[0].tolist()
            results = collection.query(
                query_embeddings=[query_embedding],
                where={"email": email},
                n_results=5,
            )
            # Flatten nested lists from results["documents"]
            if results and "documents" in results:
                return [doc for sublist in results["documents"] for doc in sublist]
            return []
        else:
            results = collection.get(where={"email": email})
            return results["documents"] if results else []
    except Exception as e:
        print(f"[WARN] Failed to fetch long memory: {e}")
        return []


# ==============================
# 🔍 SEMANTIC SEARCH (Pinecone)
# ==============================
def semantic_search(query, top_k=3):
    try:
        query_embedding = embedder.encode(
            [query], convert_to_numpy=True, normalize_embeddings=False
        )[0].tolist()

        search_response = index.query(
            vector=query_embedding, top_k=top_k, include_metadata=True
        )

        results = []
        matches = (
            search_response.get("matches", [])
            if isinstance(search_response, dict)
            else getattr(search_response, "matches", [])
        )
        for match in matches:
            metadata = (
                match.get("metadata", {})
                if isinstance(match, dict)
                else getattr(match, "metadata", {}) or {}
            )
            results.append(
                {
                    "context": metadata.get("text") or metadata.get("context", ""),
                    "reference": metadata.get("source") or "Unknown Source",
                }
            )
        return results
    except Exception as e:
        print(f"[ERROR] ❌ Pinecone semantic search failed: {e}")
        traceback.print_exc()
        return []


# ==============================
# 🆕 ROUTE: START NEW CONVERSATION
# ==============================
@rag_bp.route("/start-conversation", methods=["POST"])
def start_conversation():
    data = request.get_json(force=True)
    email = data.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    conversation_id = str(uuid.uuid4())
    save_message(email, conversation_id, "system", "Conversation started")
    return jsonify({"conversation_id": conversation_id}), 200


# ==============================
# 📜 ROUTE: LIST USER CONVERSATIONS
# ==============================
@rag_bp.route("/conversations", methods=["GET"])
def list_conversations():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    convo_ids = get_user_conversations(email)
    summaries = []
    for cid in convo_ids:
        msgs = get_conversation_history(email, cid, limit=1)
        preview = msgs[-1]["message"][:80] + "..." if msgs else "Empty conversation"
        summaries.append({"conversation_id": cid, "preview": preview})

    return jsonify({"conversations": summaries}), 200


# ==============================
# 💬 ROUTE: GET SPECIFIC CONVERSATION
# ==============================
@rag_bp.route("/conversation/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    history = get_conversation_history(email, conversation_id)
    return jsonify({"messages": history}), 200


# ==============================
# 🤖 MAIN CHAT ENDPOINT
# ==============================
@rag_bp.route("/ai-remedy", methods=["POST"])
def ai_remedy():
    try:
        data = request.get_json(force=True)
        query = data.get("query")
        email = data.get("email")
        conversation_id = data.get("conversation_id")

        if not query or not email:
            return jsonify({"error": "Missing query or email"}), 400

        # If no conversation provided, start a new one automatically
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Save user message
        save_message(email, conversation_id, "user", query)

        # Retrieve memory context
        short_memory = get_short_memory(email, conversation_id, limit=10)
        long_memory = get_long_memory(email, search_text=query)

        # RAG (Pinecone)
        results = semantic_search(query, top_k=3)
        context_text = "\n---\n".join([r["context"] for r in results if r["context"]])
        references = [r["reference"] for r in results]

        # Flatten memory lists safely
        flat_short_memory = [m if isinstance(m, str) else str(m) for m in short_memory]
        flat_long_memory = [m if isinstance(m, str) else str(m) for m in long_memory]

        memory_context = "\n".join(flat_short_memory + flat_long_memory)
        combined_context = f"{memory_context}\n{context_text}".strip()

        prompt = f"""You are an Ayurvedic doctor with 10+ years of experience.
Use the context below (memory + Ayurvedic data) to give the best natural remedy.

Context:
{combined_context}

User Query:
{query}
"""

        response = together_client.chat.completions.create(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[
                {"role": "system", "content": "You are an Ayurvedic assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )

        reply = response.choices[0].message.content.strip()

        # Save assistant reply
        save_message(email, conversation_id, "assistant", reply)

        return jsonify(
            {
                "conversation_id": conversation_id,
                "query": query,
                "response": reply,
                "references": references,
            }
        ), 200

    except Exception as e:
        print(f"[ERROR] ❌ Exception in /ai-remedy: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error", "details": str(e)}), 500


@rag_bp.route("/conversation/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400
    try:
        # Remove all messages for this conversation_id and email
        results = collection.get(
            where={"$and": [{"email": email}, {"conversation_id": conversation_id}]}
        )
        if results and results.get("ids"):
            collection.delete(ids=results["ids"])
        return jsonify({"success": True, "message": "Conversation deleted."}), 200
    except Exception as e:
        print(f"[ERROR] ❌ Could not delete conversation: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error", "details": str(e)}), 500


# ==============================
# 🗑️ DELETE ALL CHAT HISTORY FOR USER
# ==============================
@rag_bp.route("/conversations", methods=["DELETE"])
def delete_all_conversations():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400
    try:
        # Remove all documents for this email
        results = collection.get(where={"email": email})
        if results and results.get("ids"):
            collection.delete(ids=results["ids"])
        return jsonify(
            {"success": True, "message": "All chat history deleted for user."}
        ), 200
    except Exception as e:
        print(f"[ERROR] ❌ Could not delete all conversations: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error", "details": str(e)}), 500
