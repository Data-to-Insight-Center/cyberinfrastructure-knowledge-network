FROM python:3.9-slim

WORKDIR /app

COPY daemon/ /app/
COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

ENTRYPOINT [ "python", "-u", "/app/daemon.py"]