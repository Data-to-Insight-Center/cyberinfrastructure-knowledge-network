FROM python:3.9-slim

WORKDIR /app

COPY daemon.py /app/
COPY power_processor.py /app/
COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

# Default to running the daemon, but can be overridden
CMD [ "python", "-u", "/app/daemon.py"]