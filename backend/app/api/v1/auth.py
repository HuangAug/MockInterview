"""Auth API routes — register, login, refresh, logout."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthUserResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_auth_response(user: User, job_role_name: str | None = None) -> AuthUserResponse:
    """Convert a User ORM instance to an AuthUserResponse DTO."""
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        target_job_role_id=user.target_job_role_id,
        target_job_role_name=job_role_name,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat(),
    )


def _success(data: dict | None, message: str | None = None) -> dict:
    """Build the unified success response envelope."""
    return {"success": True, "data": data, "message": message}


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /auth/register — create a new user account."""
    svc = AuthService(db)
    user, access_token, refresh_token = await svc.register(
        email=body.email,
        password=body.password,
        display_name=body.display_name,
    )
    return _success(
        data={
            "user": _user_to_auth_response(user).model_dump(by_alias=True),
            "tokens": TokenResponse(
                access_token=access_token, refresh_token=refresh_token
            ).model_dump(by_alias=True),
        },
        message="注册成功",
    )


@router.post("/login", response_model=dict)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /auth/login — authenticate and receive tokens."""
    svc = AuthService(db)
    user, access_token, refresh_token = await svc.login(
        email=body.email, password=body.password
    )
    return _success(
        data={
            "user": _user_to_auth_response(user).model_dump(by_alias=True),
            "tokens": TokenResponse(
                access_token=access_token, refresh_token=refresh_token
            ).model_dump(by_alias=True),
        },
    )


@router.post("/refresh", response_model=dict)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /auth/refresh — rotate refresh token and get new token pair."""
    svc = AuthService(db)
    access_token, refresh_token = await svc.refresh(body.refresh_token)
    return _success(
        data=TokenResponse(
            access_token=access_token, refresh_token=refresh_token
        ).model_dump(by_alias=True),
    )


@router.post("/logout", response_model=dict)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """POST /auth/logout — revoke the current refresh token."""
    svc = AuthService(db)
    await svc.logout(body.refresh_token)
    return _success(data=None, message="已退出登录")
