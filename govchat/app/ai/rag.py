import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma_client = chromadb.PersistentClient(path=os.path.abspath(CHROMA_PATH))


def get_collection():
    return chroma_client.get_or_create_collection(name="energy_data")


def get_road_safety_collection():
    return chroma_client.get_or_create_collection(name="road_safety_data")


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


def search_road_safety(query: str, n_results: int = 3) -> str:
    collection = get_road_safety_collection()
    query_embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    if not results["documents"][0]:
        return "No relevant road safety data found."

    chunks = results["documents"][0]
    return "\n\n---\n\n".join(chunks)
