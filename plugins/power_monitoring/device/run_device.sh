#!/bin/bash

# Stop and remove any existing container named 'device'
if [ "$(docker ps -aq -f name=device)" ]; then
    docker rm -f device
fi

# Build the Docker image
docker build -t device .

# Run the Docker container
docker run --name device -t device