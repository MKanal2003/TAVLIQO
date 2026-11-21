#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose exec web python manage.py migrate --database=default --noinput
docker compose exec web python manage.py migrate --database=tenant --noinput
echo "Both TAVLIQO databases are migrated."
