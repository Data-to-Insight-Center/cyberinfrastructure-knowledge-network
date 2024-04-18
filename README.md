### Start Kafka broker
```bash
cd kafka
docker compose up
```

### Build Producer and Produce Events
```bash
cd capture-daemon
docker build -t capture-daemon .
docker container rm --force capture-daemon || true
docker run --network=host --name capture-daemon capture-daemon
```

### Start Kafka Stream Processor
```bash
cd cep_engine/aggregate
docker build -t cep-aggregate .
docker container rm --force cep-aggregate || true
docker run --network=host --name cep-aggregate cep-aggregate
```
```bash
cd cep_engine/alert-raw
docker build -t cep-alert-raw .
docker container rm --force cep-alert-raw || true
docker run --network=host --name cep-alert-raw cep-alert-raw
```
```bash
cd cep_engine/alert-agg
docker build -t cep-alert-agg .
docker container rm --force cep-alert-agg || true
docker run --network=host --name cep-alert-agg cep-alert-agg
```

