# Logistics Load Manager

> FastAPI + async PostgreSQL + Telegram bot for logistics load management. Parses dispatcher emails into structured loads, assigns drivers, and notifies them over Telegram.

[![CI](https://github.com/Mohar7/logistic_load_manager/actions/workflows/ci.yml/badge.svg)](https://github.com/Mohar7/logistic_load_manager/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Quick start

```bash
git clone https://github.com/Mohar7/logistic_load_manager.git
cd logistic_load_manager
cp .env.example .env       # fill in DB_PASSWORD, JWT_SECRET_KEY, etc.
docker compose up --build  # API on :8000, Swagger on :8000/docs
```

That's it. The `app` container runs Alembic migrations, the `db` container is a Postgres 16 with healthcheck, and the API comes up on `http://localhost:8000/docs`. To include the Telegram bot process: `docker compose --profile bot up`.

## What it does

A dispatcher pastes the load text from a broker email; the regex parser pulls out trip ID, pickup/dropoff facilities, times-with-timezones, rate, distance, and an assigned driver. The result lands in Postgres as `loads + legs` rows, gets assigned to a driver, and the driver is notified over Telegram. Admin endpoints expose CRUD for companies, drivers, and dispatchers.

## Architecture

```
                         ┌──────────────────────────────────────────────┐
   HTTP (FastAPI)        │  app/                                        │
   ──────────────►       │                                              │
                         │  api/routes/    ─►  services/   ─►  db/      │
                         │  (Pydantic I/O)     (business)      repositories/
                         │                                     (AsyncSession)
                         │                                              │
                         │             ▲                          ▼     │
                         │             │                                │
                         │       app/auth/                              │
                         │  ┌────────────────┐                          │
                         │  │ OAuth2 + JWT   │                          │
                         │  │ (passlib bcrypt│                          │
                         │  │  python-jose)  │                          │
                         │  └────────────────┘                          │
                         └──────────────────────────────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────────┐
                                    │   PostgreSQL 16     │
                                    │   asyncpg driver    │
                                    └─────────────────────┘
                                              ▲
                                              │
                         ┌────────────────────┴─────────────────────────┐
                         │  app/bot/  (aiogram 3, separate process)     │
                         │                                              │
                         │  handlers/  ─►  services/  ─►  db/...        │
                         │  (DatabaseMiddleware yields AsyncSession)    │
                         └──────────────────────────────────────────────┘
```

**Stack.** Python 3.12 · FastAPI · async SQLAlchemy 2.0 + asyncpg · Pydantic v2 · Alembic · aiogram 3 · Docker (multi-stage, non-root) · uv for deps · ruff + mypy + pytest in CI.

**Layered architecture, top to bottom**

| Layer | Responsibility | Code |
|---|---|---|
| Route | HTTP parsing, dependency injection, status codes | `app/api/routes/*.py` |
| Service | Business logic, transactions, cross-repo orchestration | `app/services/*.py` |
| Repository | One model = one repo. `await session.execute(select(...))` | `app/db/repositories/*.py` |
| Model | ORM models on a single `DeclarativeBase` | `app/db/models.py` |
| Schema | Pydantic v2 I/O contracts | `app/schemas/*.py` |

## Auth

OAuth2 password flow with JWT bearer tokens:

```bash
# Login (form-encoded — that's the OAuth2 spec)
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin-pw-123"
# → {"access_token": "eyJ...", "token_type": "bearer"}

# Use the token
curl http://localhost:8000/auth/me -H "Authorization: Bearer eyJ..."
```

| Endpoint kind | Auth requirement |
|---|---|
| `GET /…` (read-only) | Public |
| `POST/PUT/PATCH /…` (mutate) | Any active user (`Depends(require_any_authenticated)`) |
| `DELETE /…` | Admin only (`Depends(require_role("admin"))`) |
| `POST /auth/register` | Admin only |

The default JWT secret in `.env.example` is `INSECURE-DEV-ONLY-CHANGE-ME` — `pydantic-settings` will load whatever you put in `.env`, and production deployments **must** override it.

## Local development (no Docker)

```bash
uv sync                            # creates .venv with pinned deps
uv run alembic upgrade head        # apply migrations (requires running PG)
uv run uvicorn app.main:app --reload
```

Run the test suite:

```bash
uv run pytest --cov=app            # 27 tests, ~3s, in-memory SQLite
uv run ruff check app/ tests/      # lint
uv run mypy app/                   # type check (strict)
```

The test suite uses an in-memory SQLite database (via `aiosqlite`) so tests don't need a running Postgres; the real schema is recreated per test via `Base.metadata.create_all`.

## Configuration

All settings come from environment variables (or `.env`), parsed by `pydantic-settings`:

| Variable | Default | Notes |
|---|---|---|
| `DB_HOST` | `localhost` | Use `db` inside docker compose |
| `DB_PORT` | `5432` | |
| `DB_USER`, `DB_PASSWORD`, `DB_NAME` | — | Required. `DB_PASSWORD` default is `"change-me"` so misconfig fails loudly |
| `TELEGRAM_BOT_TOKEN` | empty | Required only if running the bot process |
| `JWT_SECRET_KEY` | `INSECURE-DEV-ONLY-CHANGE-ME` | **Must override in production** |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRE_MINUTES` | `60` | |
| `DEBUG` | `False` | Toggles SQLAlchemy echo + wildcard CORS |

See [`.env.example`](.env.example).

## API documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

The Swagger UI "Authorize" button uses the `/auth/login` endpoint — paste your credentials there and every subsequent request in the page is authenticated.

## Project layout

```
app/
├── api/routes/              # FastAPI routers (one per domain)
│   ├── auth.py              # login / register / me
│   ├── load_parser.py
│   ├── load_management.py
│   ├── driver_management.py
│   ├── company_management.py
│   ├── dispatcher_management.py
│   ├── bot_management.py
│   └── telegram_integration.py
├── auth/                    # security helpers + FastAPI deps
│   ├── security.py          # bcrypt + JWT encode/decode
│   └── dependencies.py      # get_current_user, require_role
├── services/                # business logic, transaction boundaries
├── db/
│   ├── database.py          # AsyncEngine + AsyncSessionLocal + Base
│   ├── models.py            # ORM
│   └── repositories/        # one repo per entity, all async
├── schemas/                 # Pydantic v2 I/O
├── core/
│   ├── parser/              # regex-based load text parser (no LLM)
│   └── utils/               # date/text helpers
├── bot/                     # aiogram 3 Telegram bot (separate process)
└── main.py                  # FastAPI app, lifespan, router includes
alembic/                     # migrations
tests/                       # 27 tests, async, in-memory SQLite
```

## Migrations

Alembic with manually-written migrations:

```bash
uv run alembic upgrade head         # apply
uv run alembic revision -m "msg"    # new empty migration
uv run alembic downgrade -1         # roll back one step
```

## CI

GitHub Actions on every push and PR to `main`:

1. **Lint** — `ruff check`, `ruff format --check`, `mypy app/` (mypy is `continue-on-error` while pre-existing untyped sites are migrated)
2. **Test** — `pytest --cov=app`, with coverage and junit XML uploaded as artifacts.

Concurrency-grouped to cancel in-flight runs on new pushes. Cached uv installs keep the cold-cache build under 90s.

## License

MIT — see [LICENSE](LICENSE).
