# ─────────────────────────────────────────────────────────────────────────────
# QR-Dine — Django application image
#
# Single-stage build optimised for development. Production will swap CMD to
# gunicorn via docker-compose override (added in Cycle 6).
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System libraries required by Pillow, psycopg2-binary (fallback path),
# and general diagnostics. build-essential is included so any package that
# lacks an aarch64/amd64 wheel can compile at image-build time.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg62-turbo-dev \
        zlib1g-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Layer cache: requirements first, code second.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project.
COPY . .

# Entrypoint handles DB-wait, migrations, collectstatic, then execs CMD.
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]