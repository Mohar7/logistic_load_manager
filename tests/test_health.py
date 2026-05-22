"""Smoke tests — if these don't pass, the test infrastructure is broken."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["docs_url"] == "/docs"


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_openapi_schema_includes_auth(client: AsyncClient) -> None:
    """Sanity check that /auth/login is published in the OpenAPI schema."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/auth/login" in schema["paths"]
    assert "/auth/me" in schema["paths"]
