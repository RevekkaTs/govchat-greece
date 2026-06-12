from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.ai.agent import run_agent
from app.db import get_session
from app.dependencies import get_current_user
from app.models import ChatSession, ChatMessage, User


class CreateSessionRequest(BaseModel):
    title: str


class CreateMessageRequest(BaseModel):
    content: str


router = APIRouter()


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    chat_session = ChatSession(title=body.title, user_id=current_user.id)
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return {
        "id": chat_session.id,
        "user_id": chat_session.user_id,
        "title": chat_session.title,
        "created_at": chat_session.created_at,
    }


@router.get("/sessions", status_code=status.HTTP_200_OK)
def list_sessions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    sessions = session.exec(
        select(ChatSession).where(ChatSession.user_id == current_user.id)
    ).all()
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "title": s.title,
            "created_at": s.created_at,
        }
        for s in sessions
    ]


@router.post("/sessions/{session_id}/messages", status_code=status.HTTP_201_CREATED)
def send_message(
    session_id: int,
    body: CreateMessageRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=body.content,
    )
    session.add(user_message)
    session.commit()
    session.refresh(user_message)

    ai_reply, detected_domain = run_agent(body.content)
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


@router.get("/sessions/{session_id}/messages", status_code=status.HTTP_200_OK)
def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    messages = session.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    ).all()
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "domain": m.domain,
            "created_at": m.created_at,
        }
        for m in messages
    ]
