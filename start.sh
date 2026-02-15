#!/usr/bin/env bash
set -o errexit

python manage.py migrate --no-input
exec gunicorn mysite.wsgi:application
