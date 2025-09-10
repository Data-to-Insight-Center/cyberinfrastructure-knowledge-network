FROM python:3.9-slim

WORKDIR /app

COPY ckn_dashboard/Home.py /app/
COPY ckn_dashboard/ckn_kg.py /app/
COPY ckn_dashboard/llm_graph.py /app/
COPY ckn_dashboard/util.py /app/
COPY ckn_dashboard/modelcards /app/modelcards
COPY ckn_dashboard/requirements.txt /app/
COPY ckn_dashboard/pages /app/pages

RUN pip install -r /app/requirements.txt

EXPOSE 8502

ENV PYTHONPATH="${PYTHONPATH}:/app"

ENV OPENAI_API_KEY=''
ENV NEO4J_URI='bolt://locahost:7687'
ENV NEO4J_USER=neo4j
ENV NEO4J_PWD='pwd'

ENTRYPOINT [ "streamlit", "run", "/app/Home.py", "--server.port", "8502"]