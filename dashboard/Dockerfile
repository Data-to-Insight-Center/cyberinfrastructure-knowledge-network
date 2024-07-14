FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

COPY app.py /app/
COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

EXPOSE 5006

ENV CKN_KAFKA_BROKER=localhost:9092
ENV KAFKA_OFFSET=earliest
ENV ORACLE_EVENTS_TOPIC=oracle-events
ENV ORACLE_ALERTS_TOPIC=oracle-alerts
ENV DASHBOARD_GROUP_ID=ckn-analytics-dashboards

ENTRYPOINT [ "panel", "serve", "/app/app.py"]