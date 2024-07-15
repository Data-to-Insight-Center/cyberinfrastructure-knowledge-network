FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

COPY ckn_dashboard.py /app/
COPY ckn_kg.py /app/
COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

EXPOSE 8502

ENV CKN_KG_URI='bolt://localhost:7687'
ENV CKN_KG_USER=neo4j
ENV CKN_KG_PWD='pwd'

ENTRYPOINT [ "streamlit", "run", "/app/ckn_dashboard.py", "--server.port", "8502"]