#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose down
echo "TAVLIQO stopped. Database and media volumes were preserved."
