
import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create or update default Super Admin accounts."

    def handle(self, *args, **options):
        accounts = [
            ("SUPERADMIN1_EMAIL", "SUPERADMIN1_PASSWORD", "Primary Super Admin"),
            ("SUPERADMIN2_EMAIL", "SUPERADMIN2_PASSWORD", "Backup Super Admin"),
        ]

        for email_key, password_key, label in accounts:
            email = os.getenv(email_key, "").strip().lower()
            password = os.getenv(password_key, "")

            if not email:
                self.stdout.write(f"{label}: Email not configured. Skipping.")
                continue

            if not password:
                self.stdout.write(
                    self.style.ERROR(f"{label}: Password not configured.")
                )
                continue

            user = User.objects.filter(email__iexact=email).first()

            created = user is None

            if created:
                user = User(username=email, email=email)

            user.username = email
            user.email = email
            user.role = User.ROLE_SUPERADMIN
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()

            action = "created" if created else "updated"

            self.stdout.write(
                self.style.SUCCESS(f"{label}: Account {action} successfully.")
            )
            
