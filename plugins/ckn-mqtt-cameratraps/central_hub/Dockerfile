FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir paho-mqtt

COPY event_subscriber.py image_subscriber.py /app/

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]