### Start Kafka broker
```bash
cd kafka
docker compose up
```

### Start Kafka Stream Processor
```bash
cd cep_engine/aggregate
docker build -t cep_aggregate .
docker container rm --force cep_aggregate || true
docker run --network=host --name cep_aggregate cep_aggregate
```
```bash
cd cep_engine/alerts-raw
docker build -t cep_raw_alert .
docker container rm --force cep_raw_alert || true
docker run --network=host --name cep_raw_alert cep_raw_alert
```
```bash
cd cep_engine/alerts-agg
docker build -t cep_agg_alert .
docker container rm --force cep_raw_alert || true
docker run --network=host --name cep_agg_alert cep_agg_alert
```

### Build Producer and Produce Events
```bash
cd capture_daemon
docker build -t capture_daemon .
docker container rm --force capture_daemon || true
docker run --network=host --name capture_daemon capture_daemon
```