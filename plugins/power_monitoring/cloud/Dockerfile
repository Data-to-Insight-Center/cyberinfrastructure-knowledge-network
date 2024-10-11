# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir confluent_kafka

# Make port 9092 available to the world outside this container
EXPOSE 9092

# Run producer.py when the container launches
CMD ["python", "producer.py"]