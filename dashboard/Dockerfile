FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

COPY CKN_Dashboard.py /app/
COPY ckn_kg.py /app/
COPY llm_graph.py /app/
COPY util.py /app/
COPY requirements.txt /app/
COPY /pages /app/pages

RUN pip install -r /app/requirements.txt

EXPOSE 8502

ENV PYTHONPATH="${PYTHONPATH}:/app"

ENV OPENAI_API_KEY=''
ENV NEO4J_URI='bolt://locahost:7687'
ENV NEO4J_USER=neo4j
ENV NEO4J_PWD='pwd'

ENTRYPOINT [ "streamlit", "run", "/app/CKN_Dashboard.py", "--server.port", "8502"]