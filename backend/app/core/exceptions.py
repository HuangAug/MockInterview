"""Application exception class and global exception handlers."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for all application errors.

    Attributes:
        code: Business error code (e.g. 40001, 40102).
        message: Human-readable error message.
        details: Optional list of field-level error details.
        status_code: HTTP status code for the response.
    """

    def __init__(
        self,
        code: int,
        message: str,
        details: list[dict] | None = None,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(message)


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    """Global handler that converts AppException to the unified JSON error format."""
    body: dict = {
        "success": False,
        "data": None,
        "error": {
            "code": exc.code,
            "message": exc.message,
        },
    }
    if exc.details is not None:
        body["error"]["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic validation errors to the unified error format (code 40001)."""
    details = []
    for error in exc.errors():
        loc = error.get("loc", ())
        # Skip the first element ("body"/"query"/"path") to get the field name
        field = ".".join(str(part) for part in loc[1:]) if len(loc) > 1 else "unknown"
        details.append({"field": field, "message": error.get("msg", "")})
    body: dict = {
        "success": False,
        "data": None,
        "error": {
            "code": 40001,
            "message": "参数校验失败",
            "details": details,
        },
    }
    return JSONResponse(status_code=400, content=body)
