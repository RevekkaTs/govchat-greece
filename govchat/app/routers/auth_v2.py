from typing import cast

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from app.db import get_session
from app.dependencies import get_current_admin, get_current_user
from app.models import User
from app.schemas import UserDetailResponse, UserResponse

router = APIRouter()


@router.get(
    "/auth/me",
    summary="Get the current user's details (v2)",
    status_code=status.HTTP_200_OK,
    response_model=UserDetailResponse,
)
def me(current_user: User = Depends(get_current_user)):
    return UserDetailResponse(
        id=cast(int, current_user.id),
        username=current_user.username,
        is_admin=current_user.is_admin,
    )


@router.get(
    "/admin/users",
    summary="List all users (admin only)",
    status_code=status.HTTP_200_OK,
    response_model=list[UserResponse],
)
def list_users(
    _current_admin: User = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    users = session.exec(select(User)).all()
    return [UserResponse(id=cast(int, u.id), username=u.username) for u in users]
