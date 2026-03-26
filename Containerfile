FROM docker.io/library/python:3.13.12-slim

ENV GUNICORN_CMD_ARGS="\
    --bind 0.0.0.0:8001 \
    --workers 1 \
    --threads 1 \
    --timeout 180 \
    --access-logfile -\
    --error-logfile -"
ENV AI_JAEDOLPH_CONFIG_FILE=/usr/src/app/ai_jaedolph.ini

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt . \
    && mkdir /usr/src/app/.gunicorn && chown 1001:0 /usr/src/app/.gunicorn 

USER 1001

CMD ["gunicorn", "ai_jaedolph:app"]
