#!/bin/sh
set -e

echo "Waiting for DB..."
until pg_isready -h db -U "$POSTGRES_USER"; do
  sleep 2
done

echo "Running migrations..."
alembic upgrade head

echo "Starting dev server..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload