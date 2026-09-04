"""A no-login endpoint that calls run_agent() directly, with no session or history involved.

Not used by the Streamlit UI — this exists to exercise the AI agent in
isolation (proving it doesn't depend on the auth/session layer) with
minimal friction for manual testing/demos, and to give the agent path
cheap test coverage that doesn't need a token fixture.
"""

from fastapi import APIRouter

from app.ai.agent import run_agent

router = APIRouter()


@router.get("/query", status_code=200)
def public_query(q: str):
    """Answer a single question via the AI agent, with no login and no saved chat history."""
    answer, _ = run_agent(q)
    return {"question": q, "answer": answer}
