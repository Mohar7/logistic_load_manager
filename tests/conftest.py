"""Test fixtures for the FastAPI + AsyncSession stack.

Design:
- Each test gets a fresh in-memory aiosqlite database. Schema is recreated
  via `Base.metadata.create_all` so we don't depend on Alembic migrations
  being SQLite-compatible (they use Postgres `now()` server_default).
- The app's `get_db` dependency is overridden to yield from the test
  sessionmaker, so route handlers see the same schema as fixtures.
- `AsyncClient` uses `httpx.ASGITransport`; `asgi_lifespan.LifespanManager`
  runs the lifespan() startup/shutdown around it. We DON'T call
  `setup_database()` in tests — that runs Alembic which requires Postgres.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


# Ensure config loads cleanly even without a real DB or telegram token.
os.environ.setdefault("DB_HOST", "ignored")
os.environ.setdefault("DB_USER", "u")
os.environ.setdefault("DB_PASSWORD", "p")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("DEBUG", "True")


# Import AFTER env stubs so config.get_settings() picks them up.
from app.auth.security import hash_password  # noqa: E402
from app.db.database import Base, get_db  # noqa: E402
from app.db.models import User  # noqa: E402
from app.main import app  # noqa: E402


# Skip the real Alembic startup so SQLite tests don't try to connect to PG.
async def _noop_setup() -> None:
    return None


# Patch setup_database() in lifespan's namespace.
import app.main as _app_main  # noqa: E402

_app_main.setup_database = _noop_setup  # type: ignore[assignment]


@pytest_asyncio.fixture
async def engine():
    """Per-test in-memory SQLite engine with the full schema."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with `get_db` overridden to use the per-test schema."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


# ----- Helper fixtures: seeded users -----


async def _seed_user(
    db: AsyncSession, *, username: str, password: str, role: str = "dispatcher"
) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    return await _seed_user(
        db_session, username="admin", password="admin-pw-123", role="admin"
    )


@pytest_asyncio.fixture
async def dispatcher_user(db_session: AsyncSession) -> User:
    return await _seed_user(
        db_session, username="dispatcher", password="disp-pw-123", role="dispatcher"
    )


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession) -> User:
    return await _seed_user(
        db_session, username="viewer", password="view-pw-123", role="viewer"
    )


async def _login(client: AsyncClient, username: str, password: str) -> str:
    """POST credentials to /auth/login and return the bearer token."""
    response = await client.post(
        "/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.fixture
def auth_headers_factory():
    """Factory: returns Authorization headers for a token."""

    def _make(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest_asyncio.fixture
async def admin_headers(
    client: AsyncClient, admin_user: User, auth_headers_factory
) -> dict[str, str]:
    token = await _login(client, admin_user.username, "admin-pw-123")
    return auth_headers_factory(token)


@pytest_asyncio.fixture
async def dispatcher_headers(
    client: AsyncClient, dispatcher_user: User, auth_headers_factory
) -> dict[str, str]:
    token = await _login(client, dispatcher_user.username, "disp-pw-123")
    return auth_headers_factory(token)


__all__: list[str] = []  # nothing exported; fixtures are auto-discovered
