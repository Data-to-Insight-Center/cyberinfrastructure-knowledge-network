FROM python:3.9-slim

WORKDIR /app

COPY device_request_generator.py /app/
COPY requirements.txt /app/
COPY data /app/data
COPY .env /app/.env

RUN pip install -r /app/requirements.txt

ENTRYPOINT [ "python", "-u", "/app/device_request_generator.py"]