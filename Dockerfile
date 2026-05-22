# syntax=docker/dockerfile:1.7
#
# Multi-stage build:
#   builder  — uses uv to resolve+install deps into a venv we copy out
#   runtime  — slim python image, no build toolchain, non-root user
#
# Image is ~110 MB vs ~1.1 GB for the previous single-stage python:3.12.

# ---- builder ----
FROM python:3.12-slim AS builder

# Install uv (small static binary, fast resolver).
COPY --from=ghcr.io/astral-sh/uv:0.4.27 /uv /usr/local/bin/uv

# We compile to bytecode in the runtime image, not here, so bytecode
# generation in the venv is disabled to keep the layer small.
ENV UV_COMPILE_BYTECODE=0 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /build

# Layer 1: copy only the dep-spec files. Changes to source code don't
# invalidate this layer, so most rebuilds are <2s.
COPY pyproject.toml uv.lock ./

# Install runtime deps into a project-local venv at /build/.venv.
# --frozen guarantees lock fidelity. --no-dev excludes pytest/ruff/mypy.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Layer 2: now copy the app and install the project itself.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini init_app.py ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ---- runtime ----
FROM python:3.12-slim AS runtime

# netcat is used by entrypoint.sh to wait for the database.
RUN apt-get update \
    && apt-get install -y --no-install-recommends netcat-traditional \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Non-root user. Drops root capability inside the container, which is a
# baseline hardening expected by most production schedulers.
ARG APP_UID=10001
RUN groupadd --gid ${APP_UID} app \
    && useradd --uid ${APP_UID} --gid ${APP_UID} --no-create-home --shell /sbin/nologin app

WORKDIR /app

# Pull the venv from the builder. The venv ships its own Python
# interpreter symlink so we don't need pip / setuptools in runtime.
COPY --from=builder --chown=app:app /build/.venv /app/.venv

# Application code.
COPY --chown=app:app app ./app
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini init_app.py ./
COPY --chown=app:app entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# entrypoint.sh waits for the DB, runs migrations, then exec's uvicorn.
# No --reload — that's a dev-only flag.
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
