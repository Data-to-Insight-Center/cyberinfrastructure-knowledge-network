```bash
docker build -t capture_daemon .
```

```bash
docker build -t capture_daemon . && docker rm -f capture_daemon || true && docker run --name capture_daemon -v icicle:/data capture_daemon
```