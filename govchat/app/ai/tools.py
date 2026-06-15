from app.ai.rag import search as rag_search, search_road_safety, search_fires


def road_safety_tool(year: int | None = None) -> str:
    """Search road accident statistics from Greek police data (2021-2025)."""
    query = f"road accidents Greece {year}" if year else "road accidents Greece"
    return search_road_safety(query)


def fires_tool(year: int | None = None) -> str:
    """Search forest fire and wildfire statistics for Greece (2021-2024)."""
    query = f"fires Greece {year}" if year else "fires Greece burned area"
    return search_fires(query)


def energy_tool(query: str) -> str:
    """Search ADMIE energy balance data using RAG"""
    context = rag_search(query)
    return f"Relevant energy data found:\n\n{context}"
