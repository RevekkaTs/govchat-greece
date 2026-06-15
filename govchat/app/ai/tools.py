from app.ai.rag import search as rag_search, search_road_safety


def road_safety_tool(year: int | None = None) -> str:
    """Search road accident statistics from Greek police data (2021-2025)."""
    query = f"road accidents Greece {year}" if year else "road accidents Greece"
    return search_road_safety(query)


def fires_tool(year: int | None = None) -> str:
    """Search forest fire data for Greece."""
    return "Forest fire data is not yet available."


def energy_tool(query: str) -> str:
    """Search ADMIE energy balance data using RAG"""
    context = rag_search(query)
    return f"Relevant energy data found:\n\n{context}"
