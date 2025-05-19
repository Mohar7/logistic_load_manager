#!/bin/bash
# start.sh
set -e

# Wait for database to be ready
echo "Waiting for PostgreSQL to start..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "PostgreSQL started"

# Run migrations
echo "Running database migrations"
alembic upgrade head

# Initialize database with default data
echo "Initializing database with default data"
python -m app.db.init_db

# Start the application
echo "Starting the API server"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload