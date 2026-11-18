# QR-Dine Docker setup

These files are intended to be copied into the existing `QR-Dine/` Django
project directory (the directory containing `manage.py` and `requirements.txt`).

## Important scope

This container setup matches the **current Django code in the uploaded
repository**: Python 3.11, Django 4.2.11, and one Django database alias
(`default`). It is a containerization baseline, not the final two-database
control/tenant architecture. Redis is not included because the current Django
application does not use it.

The Docker image is ARM64-compatible through the official Python and PostgreSQL
multi-architecture images. The image runs Gunicorn as a non-root user.

## 1. Create your runtime environment file

Copy `.env.example` to `.env` and set real local values. At minimum:

- `SECRET_KEY`: generate a strong Django secret.
- `DEBUG=False` for a production-like run.
- `ALLOWED_HOSTS=localhost,127.0.0.1` for local access.
- `CSRF_TRUSTED_ORIGINS=http://localhost:8000` for local access.
- `POSTGRES_DB=TAVLIQO`
- `POSTGRES_USER=TAVLIQO`
- `POSTGRES_PASSWORD`: a strong local database password.
- `DATABASE_URL=postgres://TAVLIQO:YOUR_PASSWORD@db:5432/TAVLIQO`

If the database password contains reserved URL characters, URL-encode them
inside `DATABASE_URL`.

Do not commit `.env` or use example credentials in production.

## 2. Build and start

From the `QR-Dine/` directory:

```bash
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f web
```

Open `http://localhost:8000`.

## 3. Database migrations

Migrations are intentionally not run automatically by the web container.
Before applying migrations to any database containing important data, take and
verify a backup first.

For a new local database:

```bash
docker compose run --rm web python manage.py migrate
```

Create an administrator interactively:

```bash
docker compose run --rm web python manage.py createsuperuser
```

Do not bake administrator credentials into the Docker image or create users
during the image build.

## 4. Useful commands

```bash
# Stop containers; retain named volumes and data
docker compose down

# Stop and remove containers plus database/media data (DESTRUCTIVE)
docker compose down -v

# View logs
docker compose logs -f

# Open a Django shell
docker compose exec web python manage.py shell

# Check Django configuration
docker compose exec web python manage.py check --deploy
```

## 5. Data persistence

- PostgreSQL data is stored in `qrdine_postgres_data`.
- Uploaded media and generated QR images are stored in `qrdine_media`.
- Static assets are collected into the image at build time.

Back up the PostgreSQL volume using `pg_dump` and separately back up media.
A Docker volume is persistence, not a backup.

## 6. Production limitations to resolve before launch

This does not yet provide the final requested deployment design:

- Separate `control` and `tenant` PostgreSQL databases and Django routers.
- Redis integration.
- Caddy / HTTPS and `<ip>.nip.io` reverse proxy configuration.
- CI/CD image publishing, SHA-based tags, smoke tests and rollback.
- Automated backup-before-migration deployment orchestration.
- Production media object storage or a separately managed durable media volume.
- JWT-only authentication and the other security changes in the product plan.

Do not use this as a claim that the application is production-ready. Complete and
test those architecture changes before production deployment.
