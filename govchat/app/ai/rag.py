"""RAG layer: embeds text with OpenAI and runs similarity search against the three
ChromaDB collections (energy_data, road_safety_data, fire_data).

Used two ways: the scripts/seed_*.py scripts call embed_text() once per document when (re)populating a collection; the search_*() functions
below embed an incoming question and return its top-3 most similar stored documents, joined into one string, for the matching tool in
tools.py to pass on as context. The OpenAI client is created lazily (see _get_client()) so importing this module doesn't require an API
key to already be set.
"""

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


def get_energy_collection():
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


def _search(
    collection, domain_label: str, query: str, year: int | None, n_results: int
) -> str:
    """Embed the query and return the top matching documents from collection, joined
    into one string. When year is given, restricts the search to documents whose
    "year" metadata matches exactly, rather than relying on the embedding to happen
    to favor the right year's document.
    """
    query_embedding = embed_text(query)
    where = {"year": year} if year is not None else None
    results = collection.query(
        query_embeddings=[query_embedding], n_results=n_results, where=where
    )
    documents = results.get("documents") or []
    if not documents or not documents[0]:
        if year is not None:
            return f"No {domain_label} data available for {year}."
        return f"No relevant {domain_label} data found."

    chunks = documents[0]
    return "\n\n---\n\n".join(chunks)


def search_energy(query: str, year: int | None = None, n_results: int = 3) -> str:
    """Search the energy_data collection, optionally restricted to an exact year."""
    return _search(get_energy_collection(), "energy", query, year, n_results)


def search_road_safety(query: str, year: int | None = None, n_results: int = 3) -> str:
    """Search the road_safety_data collection, optionally restricted to an exact year."""
    return _search(get_road_safety_collection(), "road safety", query, year, n_results)


def search_fires(query: str, year: int | None = None, n_results: int = 3) -> str:
    """Search the fire_data collection, optionally restricted to an exact year."""
    return _search(get_fire_collection(), "fire", query, year, n_results)
