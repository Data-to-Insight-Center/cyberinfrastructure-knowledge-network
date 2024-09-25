# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy all files and folders from current directory to /app in container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Conditionally create the uploads directory
RUN mkdir -p /app/uploads

# Expose the port the app runs on
EXPOSE 8080

# Run the application
ENTRYPOINT ["python", "/app/server.py"]