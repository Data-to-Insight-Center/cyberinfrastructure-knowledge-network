```bash
docker build -t capture_daemon .
docker run --network=host --name capture_daemon capture_daemon
```