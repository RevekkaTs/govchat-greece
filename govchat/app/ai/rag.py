"""Embeds text with OpenAI and runs similarity search against the three ChromaDB collections (energy, road safety, fires)."""

import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY")
client = OpenAI(api_key=api_key) if api_key else None
chroma_client = chromadb.PersistentClient(path=os.path.abspath(CHROMA_PATH))


def _get_client() -> OpenAI:
    """Lazily create the OpenAI client on first use, so importing this module doesn't require an API key to already be set."""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing OpenAI API key. Set OPENAI_API_KEY or OPENAI_ADMIN_KEY before using AI features."
            )
        client = OpenAI(api_key=api_key)
    return client


def get_collection():
    """Get (or create) the ChromaDB collection holding the energy data."""
    return chroma_client.get_or_create_collection(name="energy_data")


def get_road_safety_collection():
    """Get (or create) the ChromaDB collection holding the road safety data."""
    return chroma_client.get_or_create_collection(name="road_safety_data")


def get_fire_collection():
    """Get (or create) the ChromaDB collection holding the fire data."""
    return chroma_client.get_or_create_collection(name="fire_data")


def embed_text(text: str) -> list[float]:
    """Turn text into an embedding vector using OpenAI's text-embedding-3-small model."""
    response = _get_client().embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return response.data[0].embedding


def search(query: str, n_results: int = 3) -> str:
    """Embed the query and return the top matching energy_data documents, joined into one string."""
    collection = get_collection()
    query_embedding = embed_text(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    if not results["documents"][0]:
        return "No relevant energy data found."

    chunks = results["documents"][0]
    return "\n\n---\n\n".join(chunks)


def search_road_safety(query: str, n_results: int = 3) -> str:
    """Embed the query and return the top matching road_safety_data documents, joined into one string."""
    collection = get_road_safety_collection()
    query_embedding = embed_text(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    if not results["documents"][0]:
        return "No relevant road safety data found."

    chunks = results["documents"][0]
    return "\n\n---\n\n".join(chunks)


def search_fires(query: str, n_results: int = 3) -> str:
    """Embed the query and return the top matching fire_data documents, joined into one string."""
    collection = get_fire_collection()
    query_embedding = embed_text(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    if not results["documents"][0]:
        return "No relevant fire data found."

    chunks = results["documents"][0]
    return "\n\n---\n\n".join(chunks)
