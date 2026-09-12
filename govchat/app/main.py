"""FastAPI app entrypoint: creates the database on startup and wires up the auth, chat, and query routers."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import create_db
from app.routers import auth, auth_v2, chat, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the SQLite tables on startup, then hand control back to FastAPI."""
    create_db()
    yield


app = FastAPI(
    title="GovChat Greece",
    description="A chatbot for Greek government open data, in the domains of energy, fires, and road safety.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
app.include_router(query.router, prefix="/v1", tags=["query"])
app.include_router(auth_v2.router, prefix="/v2", tags=["v2"])
