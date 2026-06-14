"""MockInterview AI — FastAPI application entry point."""

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
)
from app.core.logging import LoggingMiddleware, setup_logging

setup_logging(settings.log_level)

app = FastAPI(
    title="MockInterview AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

app.add_middleware(LoggingMiddleware)

app.include_router(v1_router)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }
