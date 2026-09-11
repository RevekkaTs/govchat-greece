"""A single no-login endpoint for asking the AI agent a one-off question, outside of any chat session."""

from fastapi import APIRouter

from app.ai.agent import run_agent
from app.schemas import QueryResponse

router = APIRouter()


@router.get(
    "/query",
    summary="Public query endpoint",
    status_code=200,
    response_model=QueryResponse,
)
def public_query(q: str):
    """Answer a single question via the AI agent, with no login and no saved chat history."""
    answer, _ = run_agent(q)
    return {"question": q, "answer": answer}
