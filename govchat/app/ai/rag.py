import os
import chromadb
from openai import OpenAI

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")
COLLECTION_NAME = "energy_data"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma_client = chromadb.PersistentClient(path=os.path.abspath(CHROMA_PATH))


def get_collection():
    return chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def search(query: str, n_results: int = 3) -> str:
    collection = get_collection()
    query_embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    if not results["documents"][0]:
        return "No relevant energy data found."

    chunks = results["documents"][0]
    return "\n\n---\n\n".join(chunks)
