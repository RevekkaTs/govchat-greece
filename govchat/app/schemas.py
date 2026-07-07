# Pydantic response models
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str


class UserDetailResponse(BaseModel):
    id: int
    username: str
    is_admin: bool  # (v2)


class SessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    domain: Optional[str] = None
    created_at: datetime


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class ExportedMessageResponse(BaseModel):
    role: str
    content: str
    domain: Optional[str] = None
    created_at: str


class SessionExportResponse(BaseModel):
    username: str
    title: str
    created_at: str
    messages: list[ExportedMessageResponse]


class QueryResponse(BaseModel):
    question: str
    answer: str
