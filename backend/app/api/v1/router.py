"""API v1 router — aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.job_roles import router as job_roles_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(job_roles_router)
