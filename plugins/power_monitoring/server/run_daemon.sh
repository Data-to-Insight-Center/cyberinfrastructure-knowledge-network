#!/bin/bash

## Stop and remove any existing container named 'ckn-daemon'
if [ "$(docker ps -aq -f name=ckn-daemon)" ]; then
    docker rm -f ckn-daemon
fi

# Build the Docker image
docker build -t ckn-daemon .

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the Docker container with a relative path for the uploads volume
docker run -p 8080:8080 \
--name ckn-daemon \
-e TZ=America/New_York \
-v "$SCRIPT_DIR/uploads:/app/uploads" \
-v "$SCRIPT_DIR/QoE_predictive.csv:/app/QoE_predictive.csv" \
-v "$SCRIPT_DIR/timers.csv:/app/timers.csv" \
-t ckn-daemon

