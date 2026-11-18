#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# QR-Dine entrypoint
#
# Responsibilities:
#   1. Wait for control-db and tenant-db to accept connections.
#   2. Run migrations on both databases.
#   3. Collect static files (safe for dev; production will move this to build).
#   4. exec the container's CMD.
#
# Skipping any step via env var:
#   SKIP_MIGRATIONS=1   → do not run migrations
#   SKIP_COLLECTSTATIC=1 → do not run collectstatic
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

echo "[entrypoint] Waiting for Postgres (control + tenant)..."

python - <<'PY'
import os, sys, time
from urllib.parse import urlparse
import psycopg2

def wait(name, url, timeout=120):
    p = urlparse(url)
    for attempt in range(1, timeout // 2 + 1):
        try:
            psycopg2.connect(
                dbname=p.path.lstrip("/"),
                user=p.username,
                password=p.password,
                host=p.hostname,
                port=p.port or 5432,
                connect_timeout=2,
            ).close()
            print(f"[entrypoint] {name} reachable")
            return
        except psycopg2.OperationalError:
            print(f"[entrypoint] {name} not ready (attempt {attempt}/{timeout//2})")
            time.sleep(2)
    sys.exit(f"[entrypoint] FATAL: {name} unreachable at {url}")

wait("control-db", os.environ["CONTROL_DATABASE_URL"])
wait("tenant-db",  os.environ["TENANT_DATABASE_URL"])
PY

if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then
    echo "[entrypoint] Migrating control database..."
    python manage.py migrate --noinput

    echo "[entrypoint] Migrating tenant database..."
    python manage.py migrate --database=tenant --noinput
fi

if [[ "${SKIP_COLLECTSTATIC:-0}" != "1" ]]; then
    echo "[entrypoint] Collecting static files..."
    python manage.py collectstatic --noinput --clear
fi

echo "[entrypoint] Starting: $*"
exec "$@"