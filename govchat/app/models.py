"""Database tables (SQLModel): registered users, their chat sessions, and the messages within each session."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """A registered user: username and hashed password."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str


class ChatSession(SQLModel, table=True):
    """One conversation thread belonging to a user."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatMessage(SQLModel, table=True):
    """One message (user or assistant) within a chat session, optionally tagged with the data domain that answered it."""

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id")
    role: str
    content: str
    domain: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
