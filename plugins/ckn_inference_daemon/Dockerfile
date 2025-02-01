FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r /app/requirements.txt && \
    mkdir -p /app/uploads

ENTRYPOINT [ "python", "-u", "/app/server.py" ]