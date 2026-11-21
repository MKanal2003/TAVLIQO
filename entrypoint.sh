
#!/usr/bin/env bash

# =============================================================================
# TAVLIQO - Production Entrypoint
# =============================================================================

set -Eeuo pipefail

echo "================================================="
echo "       TAVLIQO APPLICATION STARTUP"
echo "================================================="

# -----------------------------------------------------------------------------
# 1. Validate required environment variables
# -----------------------------------------------------------------------------

: "${CONTROL_DATABASE_URL:?CONTROL_DATABASE_URL is required}"
: "${TENANT_DATABASE_URL:?TENANT_DATABASE_URL is required}"

echo "[TAVLIQO] Environment variables validated."

# -----------------------------------------------------------------------------
# 2. Wait for PostgreSQL databases
# -----------------------------------------------------------------------------

echo "[TAVLIQO] Waiting for PostgreSQL databases..."

python - <<'PY'
import os
import sys
import time
from urllib.parse import urlparse

import psycopg2


def wait_for_database(name, database_url, timeout=120):
    parsed = urlparse(database_url)
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            connection = psycopg2.connect(
                dbname=parsed.path.lstrip("/"),
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port or 5432,
                connect_timeout=5,
                sslmode="require",
            )

            connection.close()

            print(f"[TAVLIQO] {name} is ready.", flush=True)
            return

        except psycopg2.OperationalError as error:
            print(
                f"[TAVLIQO] Waiting for {name}: {error}",
                flush=True
            )
            time.sleep(3)

    sys.exit(f"[TAVLIQO] ERROR: {name} connection timed out.")


wait_for_database(
    "CONTROL_DATABASE_URL",
    os.environ["CONTROL_DATABASE_URL"]
)

wait_for_database(
    "TENANT_DATABASE_URL",
    os.environ["TENANT_DATABASE_URL"]
)

print("[TAVLIQO] Both databases are reachable.", flush=True)
PY

# -----------------------------------------------------------------------------
# 3. Apply database migrations
# -----------------------------------------------------------------------------

if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then

    echo "[TAVLIQO] Applying control database migrations..."

    python manage.py migrate --noinput

    echo "[TAVLIQO] Control database migrations completed."

    echo "[TAVLIQO] Applying tenant database migrations..."

    python manage.py migrate --database=tenant --noinput

    echo "[TAVLIQO] Tenant database migrations completed."

else
    echo "[TAVLIQO] Database migrations skipped."
fi

# -----------------------------------------------------------------------------
# 4. Create or update Super Admin accounts
# -----------------------------------------------------------------------------

echo "[TAVLIQO] Initializing Super Admin accounts..."

python manage.py seed_super_admins

echo "[TAVLIQO] Super Admin initialization completed."

# -----------------------------------------------------------------------------
# 5. Collect static files
# -----------------------------------------------------------------------------

if [[ "${SKIP_COLLECTSTATIC:-0}" != "1" ]]; then

    echo "[TAVLIQO] Collecting static files..."

    python manage.py collectstatic --noinput

    echo "[TAVLIQO] Static files collection completed."

else
    echo "[TAVLIQO] Static files collection skipped."
fi

# -----------------------------------------------------------------------------
# 6. Start application
# -----------------------------------------------------------------------------

echo "================================================="
echo "       TAVLIQO STARTING APPLICATION"
echo "================================================="

if [[ $# -eq 0 ]]; then
    set -- gunicorn qrdine.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers "${WEB_CONCURRENCY:-3}" \
        --timeout 60
fi

echo "[TAVLIQO] Starting: $*"

exec "$@"
