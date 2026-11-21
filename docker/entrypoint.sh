#!/bin/sh
set -eu

echo "[TAVLIQO] Waiting for both PostgreSQL databases..."
python - <<'PY'
import os, sys, time
from urllib.parse import urlparse
import psycopg2

def wait_for_database(env_name):
    raw = os.environ.get(env_name)
    if not raw:
        raise SystemExit(f"Missing required environment variable: {env_name}")
    parsed = urlparse(raw)
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            conn = psycopg2.connect(
                dbname=parsed.path.lstrip("/"),
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port or 5432,
                connect_timeout=3,
            )
            conn.close()
            print(f"[TAVLIQO] {env_name} is ready")
            return
        except psycopg2.OperationalError:
            time.sleep(2)
    raise SystemExit(f"Timed out waiting for {env_name}")

wait_for_database("CONTROL_DATABASE_URL")
wait_for_database("TENANT_DATABASE_URL")
PY

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[TAVLIQO] Applying control database migrations..."
    python manage.py migrate --database=default --noinput
    echo "[TAVLIQO] Applying tenant database migrations..."
    python manage.py migrate --database=tenant --noinput
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
    echo "[TAVLIQO] Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "[TAVLIQO] Starting application: $*"
exec "$@"
