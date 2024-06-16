# Dockerfile for capture_daemon

# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the main script to the container
COPY main.py /app/

# Install watchdog
RUN pip install watchdog

# Command to run the main script
CMD ["python", "main.py"]
