"""SQLite database setup: the engine, and a session dependency used by FastAPI routes."""

from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./govchat.db"
engine = create_engine(DATABASE_URL, echo=False)


def create_db():
    """Create all SQLModel tables in the SQLite database if they don't already exist."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that yields a database session and closes it when the request is done."""
    with Session(engine) as session:
        yield session
