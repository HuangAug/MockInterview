"""Job Roles API — GET /job-roles endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.job_role import JobRole
from app.models.user import User
from app.schemas.job_role import JobRoleResponse

router = APIRouter(prefix="/job-roles", tags=["job-roles"])


def _success(data: dict | None, message: str | None = None) -> dict:
    """Build the unified success response envelope."""
    return {"success": True, "data": data, "message": message}


@router.get("", response_model=dict)
async def list_job_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """GET /job-roles — return active job roles sorted by sort_order ascending."""
    result = await db.execute(
        select(JobRole)
        .where(JobRole.is_active.is_(True))
        .order_by(JobRole.sort_order.asc())
    )
    roles = result.scalars().all()

    items = [
        JobRoleResponse.model_validate(role).model_dump(by_alias=True)
        for role in roles
    ]
    return _success(data={"items": items})
