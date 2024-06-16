```bash
cd camera_traps
docker build -t camera_traps .

cd capture_daemon
docker build -t capture_daemon .

docker network create cpu_network || true
docker volume create icicle || true

docker rm -f camera_traps || true
docker run -d --name camera_traps --network cpu_network -v icicle:/app camera_traps

docker rm -f capture_daemon || true
docker run -d --name capture_daemon --network cpu_network -v icicle:/app capture_daemon

docker logs -f capture_daemon
```