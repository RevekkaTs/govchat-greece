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
    answer, _ = run_agent(q)
    return {"question": q, "answer": answer}
