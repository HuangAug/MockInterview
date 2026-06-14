"""UserService — GET/PATCH /users/me business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.job_role import JobRole
from app.models.user import User


class UserService:
    """Handles user profile business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_me(self, user_id: UUID) -> tuple[User, str | None]:
        """Return the current user and their target job role name.

        Raises:
            AppException(40401): User not found.
        """
        result = await self._db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise AppException(code=40401, message="资源不存在", status_code=404)

        job_role_name: str | None = None
        if user.target_job_role_id is not None:
            jr_result = await self._db.execute(
                select(JobRole).where(JobRole.id == user.target_job_role_id)
            )
            jr = jr_result.scalar_one_or_none()
            if jr is not None:
                job_role_name = jr.name_zh

        return user, job_role_name

    async def update_me(
        self,
        user_id: UUID,
        display_name: str | None = None,
        target_job_role_id: UUID | None = None,
        update_target_job_role: bool = False,
    ) -> tuple[User, str | None]:
        """Update user profile fields and return updated user + job role name.

        Raises:
            AppException(40401): User not found.
            AppException(40402): targetJobRoleId does not exist.
        """
        result = await self._db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise AppException(code=40401, message="资源不存在", status_code=404)

        if display_name is not None:
            user.display_name = display_name

        if update_target_job_role:
            if target_job_role_id is not None:
                jr_result = await self._db.execute(
                    select(JobRole).where(
                        JobRole.id == target_job_role_id,
                        JobRole.is_active.is_(True),
                    )
                )
                jr = jr_result.scalar_one_or_none()
                if jr is None:
                    raise AppException(
                        code=40402, message="岗位不存在", status_code=404
                    )
                user.target_job_role_id = target_job_role_id
            else:
                # Explicitly clear the target job role
                user.target_job_role_id = None

        await self._db.flush()

        # Resolve job role name for response
        job_role_name: str | None = None
        if user.target_job_role_id is not None:
            jr_result = await self._db.execute(
                select(JobRole).where(JobRole.id == user.target_job_role_id)
            )
            jr = jr_result.scalar_one_or_none()
            if jr is not None:
                job_role_name = jr.name_zh

        return user, job_role_name
