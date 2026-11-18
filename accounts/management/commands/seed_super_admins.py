"""
Idempotent seeding of the two default Super Admin accounts.

Reads from environment:
    SUPERADMIN1_EMAIL / SUPERADMIN1_PASSWORD   (primary)
    SUPERADMIN2_EMAIL / SUPERADMIN2_PASSWORD   (backup, optional)

If a password is not set, a strong one is generated and printed once.
If the account already exists, it is skipped — safe to re-run.

Usage:
    docker compose -f docker-compose.dev.yml exec web \\
        python manage.py seed_super_admins
"""

import os
import secrets

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Create the two default Super Admin accounts (idempotent)."

    def handle(self, *args, **options):
        accounts = [
            ("SUPERADMIN1_EMAIL", "SUPERADMIN1_PASSWORD", "Primary Super Admin"),
            ("SUPERADMIN2_EMAIL", "SUPERADMIN2_PASSWORD", "Backup Super Admin"),
        ]

        for email_key, pw_key, label in accounts:
            email = os.environ.get(email_key, "").strip().lower()
            password = os.environ.get(pw_key, "").strip()

            if not email:
                self.stdout.write(
                    self.style.WARNING(f"{label}: {email_key} not set — skipping")
                )
                continue

            if User.objects.filter(email__iexact=email).exists():
                self.stdout.write(f"{label}: {email} already exists — skipping")
                continue

            generated = False
            if not password:
                password = secrets.token_urlsafe(16)
                generated = True

            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                role=User.ROLE_SUPERADMIN,
                is_staff=True,
                is_superuser=True,
            )

            self.stdout.write(self.style.SUCCESS(f"{label} created: {email}"))
            if generated:
                self.stdout.write(
                    self.style.WARNING(
                        f"  GENERATED PASSWORD (save this now!): {password}"
                    )
                )