FROM python:3.9-slim

WORKDIR /app

ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./experiment_monitor.py"]