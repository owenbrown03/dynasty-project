#!/bin/sh
set -e

echo "Running migrations..."
alembic upgrade head

echo "Starting application..."
if [ "${DEBUG_MODE}" = "true" ]; then
  exec python -m app.dev_server
fi

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
