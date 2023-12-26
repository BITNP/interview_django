FROM python:3.12-slim
ENV DJANGO_PRODUCTION=1
COPY . /usr/src/app
WORKDIR /usr/src/app

COPY deploy/sources.list /etc/apt/sources.list
RUN rm /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y nginx tini && \
    rm -rf /var/lib/apt/lists/* && \
    sed -i 's/worker_processes auto/worker_processes 4/g' /etc/nginx/nginx.conf && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r requirements.txt --no-cache-dir && \
    python3 manage.py collectstatic --noinput

COPY deploy/nginx-app.conf /etc/nginx/sites-available/default
EXPOSE 80
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD [ "/bin/bash", "/usr/src/app/deploy/entrypoint.sh" ]
