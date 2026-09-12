from typing import cast

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user
from app.models import User
from app.schemas import UserResponse

router = APIRouter()


@router.get(
    "/auth/me",
    summary="Get the current user's details (v2)",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=cast(int, current_user.id), username=current_user.username)
