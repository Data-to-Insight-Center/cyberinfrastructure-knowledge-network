#!/bin/sh

# Stop the existing container if it's running
docker stop server 2>/dev/null

# Remove the existing container if it exists
docker rm server 2>/dev/null

# Build the Docker image
docker build -t server .

# Run the container with the specified name and port mapping
docker run -d --name server -p 8000:8000 server

# Follow the logs of the running container
docker logs -f server