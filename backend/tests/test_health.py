"""Tests for the /health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_timestamp_is_iso(client: AsyncClient) -> None:
    response = await client.get("/health")
    data = response.json()
    # ISO 8601 contains 'T' separator
    assert "T" in data["timestamp"]
