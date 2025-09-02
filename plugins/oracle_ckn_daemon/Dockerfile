FROM python:3.9-slim

WORKDIR /app

COPY oracle_daemon.py /app/
COPY power_processor.py /app/
COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

ENTRYPOINT [ "python", "-u", "/app/oracle_daemon.py"]