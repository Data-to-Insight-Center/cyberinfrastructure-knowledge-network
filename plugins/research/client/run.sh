#!/bin/sh

# Stop the existing container if it's running
docker stop client 2>/dev/null

# Remove the existing container if it exists
docker rm client 2>/dev/null

# Build the Docker image
docker build -t client .

# Run the container with the specified name and port mapping
docker run -d --name client -p 8001:8001 client

# Follow the logs of the running container
docker logs -f client