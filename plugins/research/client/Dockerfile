FROM python:3.9-slim

WORKDIR /app

COPY main.py /app/
COPY abacus.jpg /app/
COPY requirements.txt . /app/

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python", "-u", "/app/main.py"]