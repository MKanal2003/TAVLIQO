#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# TAVLIQO entrypoint
#
# Responsibilities:
#   1. Wait for control-db and tenant-db to accept connections.
#   2. Run migrations on both databases.
#   3. Seed the Super Admin accounts (safe to run repeatedly).
#   4. Collect static files.
#   5. exec the container's CMD.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

echo "[TAVLIQO] Waiting for both PostgreSQL databases..."

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
            print(f"[TAVLIQO] {name} reachable")
            return
        except psycopg2.OperationalError:
            print(f"[TAVLIQO] {name} not ready (attempt {attempt}/{timeout//2})")
            time.sleep(2)
    sys.exit(f"[TAVLIQO] FATAL: {name} unreachable at {url}")

wait("CONTROL_DATABASE_URL", os.environ["CONTROL_DATABASE_URL"])
wait("TENANT_DATABASE_URL",  os.environ["TENANT_DATABASE_URL"])
PY

if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then
    echo "[TAVLIQO] Applying control database migrations..."
    python manage.py migrate --noinput

    echo "[TAVLIQO] Applying tenant database migrations..."
    python manage.py migrate --database=tenant --noinput
    
    # NEW: Automatically create Super Admins on startup
    echo "[TAVLIQO] Seeding Super Admins..."
    python manage.py seed_super_admins || echo "[TAVLIQO] Seed skipped or already exists."
fi

if [[ "${SKIP_COLLECTSTATIC:-0}" != "1" ]]; then
    echo "[TAVLIQO] Collecting static files..."
    python manage.py collectstatic --noinput --clear
fi

echo "[TAVLIQO] Starting application: $*"
exec "$@"