```bash
cd power/camera_traps
docker volume create icicle
docker build -t generate_cpu_data
docker rm -f camera_traps . || true
docker run -d --name generate_container --network cpu_network -v icicle:/app generate_cpu_data
docker run --network=ckn --name camera_traps -v icicle:/data camera_traps

docker network create cpu_network

docker run -d --name generate_container --network cpu_network -v $(pwd)/cpu_generated.json:/app/cpu_generated.json generate_cpu_data
docker run -d --name monitor_container --network cpu_network -v $(pwd)/cpu_generated.json:/app/cpu_generated.json monitor_cpu_data

docker logs -f monitor_container
```

```bash
cd power/capture_daemon
docker build -t monitor_cpu_data

```

### Start Kafka broker
```bash
docker network create ckn
cd kafka
docker compose up
```

### Create Docker volume and mount files
```bash
cd power/camera_traps
docker volume create icicle
docker build -t camera_traps .
docker rm -f camera_traps . || true
docker run --network=ckn --name camera_traps -v icicle:/data camera_traps
```

### Create Docker containers to read files and produce events
```bash
cd power/capture_daemon
docker build -t capture_daemon .
docker rm -f capture_daemon . || true
docker run --network=ckn --name capture_daemon -v icicle:/data capture_daemon
```