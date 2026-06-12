"""Tests for AppException and global exception handlers."""

import pytest
from httpx import AsyncClient

from app.core.exceptions import AppException
from app.main import app


@app.get("/test/app-error")
async def _raise_app_error() -> None:
    raise AppException(code=40001, message="参数校验失败", status_code=400)


@app.get("/test/app-error-with-details")
async def _raise_app_error_with_details() -> None:
    raise AppException(
        code=40001,
        message="参数校验失败",
        details=[{"field": "email", "message": "邮箱格式不正确"}],
        status_code=400,
    )


@app.get("/test/unhandled-error")
async def _raise_unhandled() -> None:
    raise RuntimeError("unexpected")


@pytest.mark.asyncio
async def test_app_exception_returns_unified_format(client: AsyncClient) -> None:
    response = await client.get("/test/app-error")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == 40001
    assert body["error"]["message"] == "参数校验失败"
    assert "details" not in body["error"]


@pytest.mark.asyncio
async def test_app_exception_with_details(client: AsyncClient) -> None:
    response = await client.get("/test/app-error-with-details")
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["details"] == [
        {"field": "email", "message": "邮箱格式不正确"}
    ]


@pytest.mark.asyncio
async def test_unhandled_exception_returns_50001(client: AsyncClient) -> None:
    response = await client.get("/test/unhandled-error")
    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == 50001
