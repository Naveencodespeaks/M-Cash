#!/bin/bash
# Run Alembic migrations
poetry run alembic -c /app/project/alembic.ini upgrade head
# Start the application
exec poetry run uvicorn application:app --host 0.0.0.0 --port 8000
