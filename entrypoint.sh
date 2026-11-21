import os
from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = "Create default Super Admin accounts"

    def handle(self, *args, **options):
        accounts = [
            ("SUPERADMIN1_EMAIL", "SUPERADMIN1_PASSWORD", "Primary Super Admin"),
            ("SUPERADMIN2_EMAIL", "SUPERADMIN2_PASSWORD", "Backup Super Admin"),
        ]

        for email_key, pw_key, label in accounts:
            email = os.environ.get(email_key, "").strip().lower()
            password = os.environ.get(pw_key, "").strip()

            if not email or not password:
                continue

            if User.objects.filter(email__iexact=email).exists():
                self.stdout.write(f"{label}: {email} already exists — skipping")
                continue

            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                role=User.ROLE_SUPERADMIN,
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write(self.style.SUCCESS(f"{label} created: {email}"))