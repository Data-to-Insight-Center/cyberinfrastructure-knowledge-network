FROM python:3.9-slim

WORKDIR /app

COPY rest_generator.py /app/
COPY requirements.txt /app/
COPY data /app/data

RUN pip install -r /app/requirements.txt

ENTRYPOINT [ "python", "-u", "/app/rest_generator.py"]