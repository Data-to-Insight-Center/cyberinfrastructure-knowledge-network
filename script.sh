#!/bin/zsh

# Remove existing Docker containers and images if they exist
docker rm -f read_volume || true
docker rm -f camera_traps || true
docker rm -f capture_daemon || true
docker rmi -f read_volume || true
docker rmi -f camera_traps || true
docker rmi -f capture_daemon || true

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

# Navigate to read_volume directory and build the image
cd ../read_volume
docker build -t read_volume .

# Create Docker network
docker network create ckn || true

# Start Kafka and Zookeeper using docker-compose
docker-compose up -d

# Run the containers with the volume mounted
docker run -d --name camera_traps --network ckn -v icicle:/data camera_traps
docker run -d --name capture_daemon --network ckn -v icicle:/data capture_daemon
docker run -d --name read_volume --network ckn -v icicle:/data read_volume

# Follow the logs of the read_volume container
docker logs -f read_volume

# Optionally delete the Docker network and volume if they exist after stopping the containers
# docker network rm ckn || true
# docker volume rm icicle || true
