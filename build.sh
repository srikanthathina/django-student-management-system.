#!/usr/bin/env bash
# Build step for Render (and any similar host). Exit on the first error.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Optional: create the first admin login from environment variables (skipped if not set)
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
  python manage.py createsuperuser --no-input --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
fi

# Optional: load demo students once (the command does nothing if students already exist)
if [[ "${SEED_DEMO:-0}" == "1" ]]; then
  python manage.py seed_students --count 150
fi
