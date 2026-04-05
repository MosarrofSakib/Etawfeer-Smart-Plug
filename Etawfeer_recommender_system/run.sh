#!/bin/bash

echo "[INFO] Starting Redis server..."
redis-server --daemonize yes

# Wait until Redis is ready instead of fixed sleep
until redis-cli ping | grep -q PONG; do
  echo "[INFO] Waiting for Redis to be ready..."
  sleep 0.5
done
echo "[INFO] Redis is up!"

echo "[INFO] Starting Celery worker..."
celery -A tasks.celery worker --loglevel=info &

# Start Celery beat for scheduled tasks
echo "[INFO] Starting Celery beat..."
celery -A tasks.celery beat --loglevel=info &

echo "[INFO] Starting Flask app..."
exec python3 app.py  # PID 1
