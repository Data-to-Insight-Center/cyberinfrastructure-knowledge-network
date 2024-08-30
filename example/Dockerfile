# /example/Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy necessary files
COPY producer.py .

# Install dependencies
RUN pip install confluent_kafka

# Command to run the Kafka producer script
CMD ["python", "producer.py"]
