"""Chat endpoints: create/list chat sessions and send/read messages, handing each user message to the AI agent for a reply."""

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import Session, select

from app.ai.agent import run_agent
from app.db import get_session
from app.dependencies import get_current_user
from app.models import ChatMessage, ChatSession, User
from app.schemas import (
    MessageResponse,
    SendMessageResponse,
    SessionExportResponse,
    SessionResponse,
)
from app.serializers import SessionImport, deserialize_session, serialize_session


class CreateSessionRequest(BaseModel):
    """Request body for POST /chat/sessions."""

    title: str


class CreateMessageRequest(BaseModel):
    """Request body for POST /chat/sessions/{id}/messages."""

    content: str


router = APIRouter()
CURRENT_USER_DEPENDENCY = Depends(get_current_user)
SESSION_DEPENDENCY = Depends(get_session)


@router.post(
    "/sessions",
    summary="Create a new chat session",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionResponse,
)
def create_session(
    body: CreateSessionRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    session: Session = SESSION_DEPENDENCY,
):
    """Create a new, empty chat session for the current user."""
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
        )
    chat_session = ChatSession(title=body.title, user_id=current_user.id)
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return SessionResponse(
        id=chat_session.id,
        user_id=chat_session.user_id,
        title=chat_session.title,
        created_at=chat_session.created_at,
    )


@router.get(
    "/sessions",
    summary="List all chat sessions for the current user",
    status_code=status.HTTP_200_OK,
    response_model=list[SessionResponse],
)
def list_sessions(
    current_user: User = CURRENT_USER_DEPENDENCY,
    session: Session = SESSION_DEPENDENCY,
):
    """List all chat sessions belonging to the current user."""
    sessions = session.exec(
        select(ChatSession).where(ChatSession.user_id == current_user.id)
    ).all()
    return [
        SessionResponse(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.post(
    "/sessions/{session_id}/messages",
    summary="Send a message in a chat session",
    status_code=status.HTTP_201_CREATED,
    response_model=SendMessageResponse,
)
def send_message(
    session_id: int,
    body: CreateMessageRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    session: Session = SESSION_DEPENDENCY,
):
    """Save the user's message, run it through the AI agent, save the reply, and return both messages."""
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    is_first_message = not session.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id).limit(1)
    ).first()

    recent = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(desc(cast(Any, ChatMessage.id)))
        .limit(5)
    ).all()
    history = [{"role": m.role, "content": m.content} for m in reversed(recent)]

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=body.content,
    )
    session.add(user_message)

    if is_first_message:
        title = body.content if len(body.content) <= 50 else body.content[:47] + "..."
        chat_session.title = title
        session.add(chat_session)

    session.commit()
    session.refresh(user_message)

    ai_reply, detected_domain = run_agent(body.content, history=history)
    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_reply,
        domain=detected_domain,
    )
    session.add(assistant_message)
    session.commit()
    session.refresh(assistant_message)

    def msg_dict(msg: ChatMessage):
        """Convert a ChatMessage row into the plain dict shape returned to the client."""
        return {
            "id": msg.id,
            "session_id": msg.session_id,
            "role": msg.role,
            "content": msg.content,
            "domain": msg.domain,
            "created_at": msg.created_at,
        }

    return {
        "user_message": msg_dict(user_message),
        "assistant_message": msg_dict(assistant_message),
    }


@router.get(
    "/sessions/{session_id}/messages",
    summary="Get all messages in a chat session",
    status_code=status.HTTP_200_OK,
    response_model=list[MessageResponse],
)
def get_messages(
    session_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    session: Session = SESSION_DEPENDENCY,
):
    """Return every message in a chat session the current user owns."""
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(cast(Any, ChatMessage.id))
    ).all()
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            domain=m.domain,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.get(
    "/sessions/{session_id}/export",
    summary="Export a chat session",
    status_code=status.HTTP_200_OK,
    response_model=SessionExportResponse,
)
def export_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)  # type: ignore
    ).all()

    return serialize_session(chat_session, messages, current_user.username)


@router.post(
    "/sessions/import",
    summary="Import a chat session",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionResponse,
)
def import_session(
    body: SessionImport,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    chat_session = deserialize_session(body, cast(int, current_user.id), session)
    return SessionResponse(
        id=chat_session.id,
        user_id=chat_session.user_id,
        title=chat_session.title,
        created_at=chat_session.created_at,
    )
