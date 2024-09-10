#!/bin/bash
set -e
/usr/sbin/nginx
python3 manage.py migrate
gunicorn -w 4 --forwarded-allow-ips='*' -b unix:/tmp/gunicorn.sock -k eventlet --access-logfile /usr/src/app/logs/gunicorn/access.log --log-file /usr/src/app/logs/gunicorn/error.log --log-level debug interview_django.wsgi:application
