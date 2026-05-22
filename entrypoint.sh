#!/usr/bin/env bash
# entrypoint.sh — Wait for Postgres, run migrations, then exec the command.
# Designed for both API and bot containers (they share the same image).

set -euo pipefail

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

echo "[entrypoint] waiting for ${DB_HOST}:${DB_PORT}..."
until nc -z "${DB_HOST}" "${DB_PORT}"; do
    sleep 0.5
done
echo "[entrypoint] database is reachable"

# Only the API container should run migrations. The bot container sets
# SKIP_MIGRATIONS=1 to avoid two processes racing on alembic_version.
if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then
    echo "[entrypoint] running alembic upgrade head"
    alembic upgrade head
fi

# Replace the shell with the actual command (PID 1 receives SIGTERM
# directly — important for graceful shutdown in Kubernetes / Compose).
exec "$@"
