"""Auth endpoints: register a new user, log in for a JWT token, and fetch the current user's profile."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.dependencies import get_current_user
from app.models import User
from app.schemas import TokenResponse, UserResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter()
session_dependency = Depends(get_session)
current_user_dependency = Depends(get_current_user)


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""

    username: str
    password: str


@router.post(
    "/register",
    summary="Register a new user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
def register(body: RegisterRequest, session: Session = session_dependency):
    """Create a new user with a hashed password; rejects a username that's already taken."""
    existing = session.exec(select(User).where(User.username == body.username)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    user = User(username=body.username, hashed_password=hash_password(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse(id=user.id, username=user.username)


@router.post(
    "/login",
    summary="Login a user and get an access token",
    response_model=TokenResponse,
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = session_dependency,
):
    """Verify username/password and return a JWT access token."""
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token, token_type="bearer")


@router.get(
    "/me", summary="Get the current user's details", response_model=UserResponse
)
def me(current_user: User = current_user_dependency):
    """Return the profile of whoever the bearer token belongs to."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
    )
