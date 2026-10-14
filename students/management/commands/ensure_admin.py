
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Ensure the configured admin account exists."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not username or not password:
            raise CommandError("Admin username/password environment variables are missing.")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            **{User.USERNAME_FIELD: username},
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)

        if email and hasattr(user, "email"):
            user.email = email

        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"Admin account {'created' if created else 'updated'} successfully."
        ))
