# TAVLIQO

TAVLIQO is a Django-based QR restaurant menu and ordering platform. The application includes platform administration, restaurant management, staff workflows, customer-facing menus and order handling.

## Technology

- Python 3.11 runtime
- Django 4.2.11 (as pinned in `requirements.txt`)
- PostgreSQL 16
- Django templates and static assets
- Gunicorn
- Docker Compose

## Architecture note

The current Django settings configure **two PostgreSQL databases**:

| Django alias | Purpose | Routed app |
|---|---|---|
| `default` | Control-plane data | Accounts, restaurants, menu, superadmin, core and Django built-ins |
| `tenant` | Order data | `orders` |

This follows `qrdine/settings.py` and `qrdine/db_routers.py` in the source. The local Docker setup therefore starts two PostgreSQL services. Redis is not included because the inspected Django settings and application dependencies do not configure or require it.

## Prerequisites

- Docker Engine / Docker Desktop
- Docker Compose v2 (`docker compose`)
- Git

No host Python or PostgreSQL installation is required for the Docker workflow.

## First-time setup (Linux / macOS / WSL2)

```bash
git clone https://github.com/MKanal2003/TAVLIQO.git
cd TAVLIQO
cp .env.example .env
```

Edit `.env` and replace:
- `SECRET_KEY` with a long, random secret.
- `DB_PASSWORD` with a unique database password.
- The password in **both** database URLs so it matches `DB_PASSWORD`.

For a password containing URL-reserved characters (`@`, `:`, `/`, `#`, `%`), URL-encode it in the two database URLs.

Start the application:

```bash
chmod +x scripts/*.sh docker/entrypoint.sh
./scripts/start.sh
```

On the first start, Docker builds the image, starts both PostgreSQL databases, waits for them to become healthy, applies Django migrations to both database aliases, collects static files, and starts Gunicorn.

Open: **http://localhost:8000**

## First-time Django administrator

After the application is running:

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts. Do not put administrator passwords in the Dockerfile, image, README, or source control.

## Everyday commands

```bash
# Start / rebuild
./scripts/start.sh

# Stop containers (keeps database and uploaded media)
./scripts/stop.sh

# Follow web logs
docker compose logs -f web

# Show service health
docker compose ps

# Apply migrations manually after model changes
./scripts/migrate.sh

# Run Django checks
docker compose exec web python manage.py check

# Open a Django shell
docker compose exec web python manage.py shell
```

## Database migrations

The repository already contains migrations under `accounts/migrations`, `restaurants/migrations` and `orders/migrations`. Do not delete or regenerate these migration files for a normal first-time deployment.

The container entrypoint applies the existing migrations to both databases:

```bash
python manage.py migrate --database=default --noinput
python manage.py migrate --database=tenant --noinput
```

When you change Django models during development, generate migrations inside the running web container:

```bash
docker compose exec web python manage.py makemigrations
```

Review the generated files, commit them to Git, then apply them:

```bash
./scripts/migrate.sh
```

Before applying migrations to an existing production database, take and verify a database backup. Never use `docker compose down -v` on a database whose data you need.

## Persistence

Docker named volumes retain:
- Control-plane PostgreSQL data
- Tenant/order PostgreSQL data
- Uploaded media
- Collected static files

Stopping with `./scripts/stop.sh` does not delete these volumes.

**Destructive reset:** `docker compose down -v` deletes the named database and media volumes. Use only when intentionally resetting a disposable local environment.

## Configuration

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django signing secret |
| `DEBUG` | Django debug mode; keep `False` for this Compose setup |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins including scheme |
| `APP_PORT` | Host port mapped to the web container |
| `DB_USER`, `DB_PASSWORD` | Credentials shared by the two local PostgreSQL services |
| `CONTROL_DATABASE_URL` | Connection URL for the `default` database |
| `TENANT_DATABASE_URL` | Connection URL for the `tenant` database |
| `CLOUDINARY_URL` | Optional Cloudinary configuration; blank uses local media storage |

For access from another machine, add its hostname/IP to `ALLOWED_HOSTS` and its full origin (including `http://` or `https://`) to `CSRF_TRUSTED_ORIGINS`.

## Troubleshooting

```bash
# Inspect all service logs
docker compose logs --tail=200

# Inspect web logs only
docker compose logs --tail=200 web

# Restart the web service
docker compose restart web

# Rebuild after Dockerfile or requirements changes
docker compose up -d --build

# Confirm applied migrations
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py showmigrations --database=tenant
```

If a database password is changed after PostgreSQL has already initialized its volume, changing `.env` alone does not change the existing database user's password. Update the database user in PostgreSQL or intentionally recreate a disposable local volume.

## Important production checklist

This setup is intended as a reproducible local/container first-start baseline. Before public production deployment:

- Upgrade Django and dependencies to currently supported, security-patched versions after compatibility testing.
- Configure HTTPS/reverse proxy and production `CSRF_TRUSTED_ORIGINS`.
- Configure durable object storage for customer uploads and backups for both databases.
- Set strong unique secrets and database credentials through deployment secrets.
- Review tenant isolation, staff authentication, payment handling and authorization.
- Add automated tests for migrations, both database routers, tenant isolation, checkout and payment flows.
- Add health/readiness endpoints, monitoring, log retention and a tested restore procedure.
- Do not expose PostgreSQL ports publicly.

## License

See [LICENSE](LICENSE).
