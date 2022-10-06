FROM python:3-slim
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app

ENV DJANGO_PRODUCTION=1
RUN sed -i 's/deb.debian.org/mirrors-tuna.bitnp.net/g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org/debian-security|mirrors-tuna.bitnp.net/debian-security|g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org|mirrors-tuna.bitnp.net/debian-security|g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y gcc nginx supervisor && \
    pip config set global.index-url http://pypi-tuna.bitnp.net/simple && \
    pip config set install.trusted-host pypi-tuna.bitnp.net && \
    pip3 install -r requirements.txt --no-cache-dir && \
    apt-get remove -y gcc && \
    rm -rf /var/lib/apt/lists/* && \
    echo "daemon off;" >> /etc/nginx/nginx.conf && \
    python3 manage.py collectstatic --noinput
COPY deploy/nginx-app.conf /etc/nginx/sites-available/default
COPY deploy/supervisor-app.conf /etc/supervisor/conf.d/
EXPOSE 80
ENTRYPOINT [ "/bin/bash", "deploy/entrypoint.sh" ]
CMD ["supervisord", "-n"]

