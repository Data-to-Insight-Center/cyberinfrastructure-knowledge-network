# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the necessary files into the container
COPY main.py /app/

# Install required packages
RUN pip install -r requirements.txt

# Command to run the main script
CMD ["python", "main.py"]
