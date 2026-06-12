from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import create_db
from app.routers import auth, chat, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(title="GovChat Greece", lifespan=lifespan)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(query.router, tags=["query"])
