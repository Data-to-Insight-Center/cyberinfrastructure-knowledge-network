### Start Kafka broker
```bash
cd kafka
docker compose up
```

### Build Producer and Produce Events
```bash
cd capture-daemon
docker build -t capture-daemon .
docker run --network=host --name capture-daemon capture-daemon
```

### Start Kafka Stream Processor
```bash
cd cep_engine/aggregate
docker build -t cep-aggregate .
docker run --network=host --name cep-aggregate cep-aggregate
```
```bash
cd cep_engine/alert-raw
docker build -t cep-alert-raw .
docker run --network=host --name cep-alert-raw cep-alert-raw
```
```bash
cd cep_engine/alert-agg
docker build -t cep-alert-agg .
docker run --network=host --name cep-alert-agg cep-alert-agg
```

