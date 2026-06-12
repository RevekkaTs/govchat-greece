import httpx
from app.ai.rag import search as rag_search

DATA_GOV_BASE = "https://data.gov.gr/api/v1/query"


def road_safety_tool(year: int | None = None) -> str:
    """Fetch road accident data from data.gov.gr"""
    params = {"resource_id": "road_accidents"}
    if year:
        params["filters"] = f'{{"year": {year}}}'

    try:
        response = httpx.get(DATA_GOV_BASE, params=params, timeout=10)
        data = response.json()
        if not data:
            return "No road accident data found."
        total = len(data)
        return f"Found {total} road accident records. Sample data: {data[:3]}"
    except Exception as e:
        return f"Error fetching road safety data: {str(e)}"


def fires_tool(year: int | None = None) -> str:
    """Fetch forest fire data from data.gov.gr"""
    params = {"resource_id": "forest_fires"}
    if year:
        params["filters"] = f'{{"year": {year}}}'

    try:
        response = httpx.get(DATA_GOV_BASE, params=params, timeout=10)
        data = response.json()
        if not data:
            return "No forest fire data found."
        total = len(data)
        return f"Found {total} forest fire records. Sample data: {data[:3]}"
    except Exception as e:
        return f"Error fetching forest fire data: {str(e)}"


def energy_tool(query: str) -> str:
    """Search ADMIE energy balance data using RAG"""
    context = rag_search(query)
    return f"Relevant energy data found:\n\n{context}"
