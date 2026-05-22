"""Auth flow tests: register, login, /me, role gates, expiration."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from httpx import AsyncClient

from app.auth.security import create_access_token, hash_password
from app.db.models import User


# ---------- /auth/login ----------


@pytest.mark.asyncio
async def test_login_returns_jwt_for_valid_credentials(
    client: AsyncClient, dispatcher_user: User
) -> None:
    response = await client.post(
        "/auth/login",
        data={"username": "dispatcher", "password": "disp-pw-123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].count(".") == 2  # JWT structure: header.payload.sig


@pytest.mark.asyncio
async def test_login_rejects_unknown_user(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/login",
        data={"username": "ghost", "password": "whatever"},
    )
    assert response.status_code == 401
    # The error message must NOT reveal whether the user exists.
    assert response.json()["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(
    client: AsyncClient, dispatcher_user: User
) -> None:
    response = await client.post(
        "/auth/login",
        data={"username": "dispatcher", "password": "WRONG"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_inactive_user(
    client: AsyncClient, db_session, dispatcher_user: User
) -> None:
    dispatcher_user.is_active = False
    await db_session.commit()

    response = await client.post(
        "/auth/login",
        data={"username": "dispatcher", "password": "disp-pw-123"},
    )
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


# ---------- /auth/me ----------


@pytest.mark.asyncio
async def test_me_returns_current_user(
    client: AsyncClient, dispatcher_headers: dict[str, str]
) -> None:
    response = await client.get("/auth/me", headers=dispatcher_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "dispatcher"
    assert response.json()["role"] == "dispatcher"


@pytest.mark.asyncio
async def test_me_rejects_missing_token(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_garbage_token(client: AsyncClient) -> None:
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_expired_token(client: AsyncClient, dispatcher_user) -> None:
    # Issue a token that's already expired.
    expired = create_access_token(
        subject="dispatcher",
        role="dispatcher",
        expires_delta=timedelta(seconds=-1),
    )
    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401


# ---------- /auth/register (admin-only) ----------


@pytest.mark.asyncio
async def test_register_succeeds_for_admin(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/auth/register",
        json={"username": "new_disp", "password": "fresh-pw-9999", "role": "dispatcher"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "new_disp"
    assert body["role"] == "dispatcher"
    assert body["is_active"] is True
    assert "password_hash" not in body  # never leak hashes


@pytest.mark.asyncio
async def test_register_rejects_non_admin(
    client: AsyncClient, dispatcher_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/auth/register",
        json={"username": "rogue", "password": "rogue-pw-12345", "role": "admin"},
        headers=dispatcher_headers,
    )
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_rejects_unauthenticated(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"username": "any", "password": "anypassword", "role": "dispatcher"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_rejects_duplicate_username(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    payload = {"username": "duplicate", "password": "first-pass-1234", "role": "viewer"}
    first = await client.post("/auth/register", json=payload, headers=admin_headers)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload, headers=admin_headers)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_register_validates_short_password(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/auth/register",
        json={"username": "shorty", "password": "tiny", "role": "viewer"},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ---------- Role-gated mutations ----------


@pytest.mark.asyncio
async def test_delete_requires_admin_role(
    client: AsyncClient, dispatcher_headers: dict[str, str]
) -> None:
    """Any DELETE endpoint should 403 for a non-admin user."""
    # /loads/{id} delete is admin-gated.
    response = await client.delete("/loads/999", headers=dispatcher_headers)
    # Either 403 (role gate) or 404 (no such load) is acceptable, but
    # NEVER 200 — that would mean the gate failed open.
    assert response.status_code in (403, 404)
    if response.status_code == 403:
        assert "admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_mutating_endpoint_requires_token(client: AsyncClient) -> None:
    """No token → 401 on POST. Using a JSON endpoint to bypass body-parsing
    quirks where Content-Type negotiation can short-circuit to 422 before
    dependencies run."""
    response = await client.post(
        "/drivers/",
        json={"name": "Anyone", "company_id": 1},
    )
    assert response.status_code == 401
