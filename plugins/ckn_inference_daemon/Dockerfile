FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install -r /app/requirements.txt && \
    mkdir -p /app/uploads

ENV PYTHONPATH=/app

# Expose the port for FastAPI
EXPOSE 8080

# Run the FastAPI server
ENTRYPOINT ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]