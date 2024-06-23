#!/bin/zsh

# Remove existing Docker containers and images if they exist
docker rm -f camera_traps || true
docker rm -f capture_daemon || true
docker rmi -f camera_traps || true
docker rmi -f capture_daemon || true

# Remove Docker network and volume if they exist
docker network rm cpu_network || true
docker volume rm icicle || true

# Clear all Docker cache and prune all unused Docker objects
docker system prune -af --volumes

# Create Docker volume
docker volume create icicle

# Copy initial cpu.json and metadata.json to the volume
docker run --rm -v icicle:/data -v $(pwd)/camera_traps:/temp busybox cp /temp/cpu.json /data/cpu.json
docker run --rm -v icicle:/data -v $(pwd)/camera_traps:/temp busybox cp /temp/metadata.json /data/metadata.json

# Navigate to camera_traps directory and build the image
cd camera_traps
docker build -t camera_traps .

# Navigate to capture_daemon directory and build the image
cd ../capture_daemon
docker build -t capture_daemon .

# Create Docker network
docker network create cpu_network || true

# Run new containers
docker run -d --name camera_traps --network cpu_network -v icicle:/data camera_traps
docker run -d --name capture_daemon --network cpu_network -v icicle:/data capture_daemon

# Follow the logs of the camera_traps and capture_daemon containers
docker logs -f camera_traps &
docker logs -f capture_daemon &

# Optionally delete the Docker network and volume if they exist after stopping the containers
# docker network rm cpu_network || true
# docker volume rm icicle || true

# Wait for 60 seconds
sleep 20

# Terminate the capture_daemon container
docker stop capture_daemon
