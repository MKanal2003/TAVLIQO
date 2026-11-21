#!/bin/sh
set -eu

PROJECT_NAME="TAVLIQO"
APP_URL="http://localhost:8000"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo "${GREEN}[INFO]${NC} $1"; }
fail() { echo "${RED}[ERROR]${NC} $1"; exit 1; }

# Ensure we are in the root directory
SCRIPT_DIR=$(dirname "$0")
PROJECT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_DIR"

echo "========================================"
echo "       ${PROJECT_NAME} STARTUP"
echo "========================================"

# 1. Check Docker
command -v docker >/dev/null 2>&1 || fail "Docker is not installed."
docker info >/dev/null 2>&1 || fail "Docker daemon is not running."

# 2. Check environment file
[ -f ".env" ] || fail ".env not found in $PROJECT_DIR. Create it first."
[ -f "docker-compose.yml" ] || fail "docker-compose.yml not found."

# 3. Start databases
log "Starting PostgreSQL databases..."
docker compose -f docker-compose.yml up -d --build control-db tenant-db

# 4. Wait for database health
wait_for_service() {
    service=$1
    retries=40
    count=0
    log "Waiting for $service..."
    
    while [ "$count" -lt "$retries" ]; do
        container_id=$(docker compose -f docker-compose.yml ps -q "$service" || true)
        
        if [ -n "$container_id" ]; then
            status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)
            
            if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
                log "$service is ready."
                return 0
            fi
        fi
        count=$((count + 1))
        sleep 2
    done
    
    docker compose -f docker-compose.yml logs --tail=50 "$service"
    fail "Timed out waiting for $service."
}

wait_for_service control-db
wait_for_service tenant-db

# 5. Start Web App
log "Building and starting TAVLIQO application..."
docker compose -f docker-compose.yml up -d --build web

wait_for_service web

# 6. Migrations
log "Applying control database migrations..."
docker compose -f docker-compose.yml exec -T web python manage.py migrate --database=default --noinput

log "Applying tenant database migrations..."
docker compose -f docker-compose.yml exec -T web python manage.py migrate --database=tenant --noinput

# 7. Collect Static
log "Collecting static files..."
docker compose -f docker-compose.yml exec -T web python manage.py collectstatic --noinput

# 8. Done
echo ""
echo "========================================"
echo "       TAVLIQO STARTED"
echo "========================================"
docker compose -f docker-compose.yml ps
echo ""
log "Application URL: $APP_URL"