#!/bin/bash
set -e
python3 manage.py migrate
gunicorn -w 4 --forwarded-allow-ips='*' -b unix:/tmp/gunicorn.sock -k uvicorn.workers.UvicornWorker interview_django.asgi:application
