#!/bin/bash

## Stop and remove any existing container named 'server'
if [ "$(docker ps -aq -f name=server)" ]; then
    docker rm -f server
fi

# Build the Docker image
docker build -t server .

# Run the Docker container
docker run --name server -t server