import chromadb
from sentence_transformers import SentenceTransformer

# Initialize
client = chromadb.Client()
collection = client.get_or_create_collection(name="communications")

model = SentenceTransformer("all-MiniLM-L6-v2")


def store_message(lead_id, message):
    embedding = model.encode(message).tolist()

    collection.add(
        documents=[message],
        embeddings=[embedding],
        metadatas=[{"lead_id": str(lead_id)}],
        ids=[f"{lead_id}_{hash(message)}"]
    )


def retrieve_similar(lead_id, query):
    embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )

    return results["documents"]