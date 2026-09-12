from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel
from sqlmodel import Session

from app.models import ChatMessage, ChatSession


class MessageImport(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    domain: Optional[str] = None
    created_at: datetime


class SessionImport(BaseModel):
    title: str
    messages: list[MessageImport]


def serialize_session(session, messages, username: str) -> dict:
    return {
        "username": username,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
                **(
                    {"domain": message.domain}
                    if message.role == "assistant" and message.domain is not None
                    else {}
                ),
            }
            for message in messages
        ],
    }


def deserialize_session(data: SessionImport, user_id: int, db: Session) -> ChatSession:
    chat_session = ChatSession(user_id=user_id, title=data.title)
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)

    if chat_session.id is None:
        raise ValueError("Failed to create chat session")

    for message_data in data.messages:
        chat_message = ChatMessage(
            session_id=chat_session.id,
            role=message_data.role,
            content=message_data.content,
            domain=message_data.domain,
            created_at=message_data.created_at,
        )
        db.add(chat_message)

    db.commit()
    db.refresh(chat_session)
    return chat_session
