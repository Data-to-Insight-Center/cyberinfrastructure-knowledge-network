# Dockerfile for camera_traps

# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the main script explicitly
COPY main.py /app/
COPY metadata.json /app/
COPY cpu.json /app/

# Command to run the main script
CMD ["python", "main.py"]
