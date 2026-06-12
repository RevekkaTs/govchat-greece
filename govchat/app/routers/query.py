from fastapi import APIRouter

from app.ai.agent import run_agent

router = APIRouter()


@router.get("/query", status_code=200)
def public_query(q: str):
    answer, _ = run_agent(q)
    return {"question": q, "answer": answer}
