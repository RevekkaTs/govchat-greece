"""The three tools the AI agent can call, each wrapping a RAG search for one data domain (road safety, fires, energy)."""

from app.ai.rag import search_road_safety, search_fires, search_energy


def road_safety_tool(year: int | None = None) -> str:
    """Search road accident statistics from Greek police data (2018-2025)."""
    query = f"road accidents Greece {year}" if year else "road accidents Greece"
    return search_road_safety(query)


def fires_tool(year: int | None = None) -> str:
    """Search forest fire and wildfire statistics for Greece (2021-2024)."""
    query = f"fires Greece {year}" if year else "fires Greece burned area"
    return search_fires(query)


def energy_tool(year: int | None = None) -> str:
    """Search Greece's electricity balance data from ADMIE (2021-2024)."""
    query = f"energy balance Greece {year}" if year else "energy balance Greece"
    return search_energy(query)
