
#!/usr/bin/env bash
set -Eeuo pipefail

# TAVLIQO - Development Startup Script
# Run from the project root: ./scripts/start.sh

PROJECT_NAME="TAVLIQO"
APP_URL="http://localhost:8000"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Always execute from project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "========================================"
echo "       ${PROJECT_NAME} STARTUP"
echo "========================================"

# 1. Check Docker
command -v docker >/dev/null 2>&1 || fail "Docker is not installed."
docker info >/dev/null 2>&1 || fail "Docker daemon is not running."

# 2. Check Docker Compose
docker compose version >/dev/null 2>&1 || fail "Docker Compose plugin is unavailable."

# 3. Check environment file
[[ -f ".env" ]] || fail ".env not found. Create it from .env.example first."

# 4. Check Compose file
COMPOSE_FILE="docker-compose.dev.yml"
[[ -f "$COMPOSE_FILE" ]] || fail "$COMPOSE_FILE not found."

COMPOSE=(docker compose -f "$COMPOSE_FILE" --env-file .env)

# 5. Validate Compose configuration
log "Validating Docker Compose configuration..."
"${COMPOSE[@]}" config --quiet || fail "Docker Compose configuration is invalid."

# 6. Start infrastructure first
log "Starting PostgreSQL databases and Redis..."
"${COMPOSE[@]}" up -d --build control-db tenant-db redis

# 7. Wait for database health
wait_for_service() {
    local service="$1"
    local retries=40
    local count=0

    log "Waiting for $service..."

    while (( count < retries )); do
        local container_id
        container_id="$("${COMPOSE[@]}" ps -q "$service")"

        [[ -n "$container_id" ]] || {
            ((count+=1))
            sleep 2
            continue
        }

        local status
        status="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)"

        if [[ "$status" == "healthy" || "$status" == "running" ]]; then
            log "$service is ready."
            return 0
        fi

        if [[ "$status" == "exited" || "$status" == "unhealthy" ]]; then
            "${COMPOSE[@]}" logs --tail=80 "$service"
            fail "$service failed to start."
        fi

        ((count+=1))
        sleep 3
    done

    "${COMPOSE[@]}" logs --tail=80 "$service"
    fail "Timed out waiting for $service."
}

wait_for_service control-db
wait_for_service tenant-db
wait_for_service redis

# 8. Build and start Django application
log "Building and starting TAVLIQO application..."
"${COMPOSE[@]}" up -d --build web

# 9. Wait for Django container
wait_for_service web

# 10. Apply migrations to both databases
log "Applying control database migrations..."
"${COMPOSE[@]}" exec -T web python manage.py migrate --database=default --noinput

log "Applying tenant database migrations..."
"${COMPOSE[@]}" exec -T web python manage.py migrate --database=tenant --noinput

# 11. Collect static files
log "Collecting static files..."
"${COMPOSE[@]}" exec -T web python manage.py collectstatic --noinput

# 12. Display final status
echo ""
echo "========================================"
echo "       TAVLIQO STARTED"
echo "========================================"

"${COMPOSE[@]}" ps

echo ""
log "Application URL: $APP_URL"
log "Admin setup: docker compose -f $COMPOSE_FILE exec web python manage.py createsuperuser"
echo ""
warn "Development mode is enabled. Do not use these credentials in production."
