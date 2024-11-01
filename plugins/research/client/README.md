```bash
docker build -t fastapi-client . && docker run -d --name client -p 8001:8001 fastapi-client && docker logs -f client
```