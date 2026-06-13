"""Users API — GET /users/me, PATCH /users/me."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UpdateUserRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def _success(data: dict | None, message: str | None = None) -> dict:
    """Build the unified success response envelope."""
    return {"success": True, "data": data, "message": message}


def _user_response(user: User, job_role_name: str | None) -> dict:
    """Convert User model to UserResponse dict with camelCase aliases."""
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        target_job_role_id=user.target_job_role_id,
        target_job_role_name=job_role_name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    ).model_dump(by_alias=True)


@router.get("/me", response_model=dict)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """GET /users/me — return current user profile."""
    svc = UserService(db)
    user, job_role_name = await svc.get_me(current_user.id)
    return _success(data=_user_response(user, job_role_name))


@router.patch("/me", response_model=dict)
async def update_me(
    body: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """PATCH /users/me — update display name and/or target job role."""
    svc = UserService(db)
    user, job_role_name = await svc.update_me(
        user_id=current_user.id,
        display_name=body.display_name,
        target_job_role_id=body.target_job_role_id,
    )
    return _success(data=_user_response(user, job_role_name), message="更新成功")
