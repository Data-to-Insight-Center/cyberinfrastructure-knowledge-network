<div align="center">

# Cyberinfrastructure Knowledge Network

[![Documentation Status](https://img.shields.io/badge/docs-latest-blue.svg)](https://cyberinfrastructure-knowledge-network.readthedocs.io/en/latest/)
[![Build Status](https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network/actions/workflows/ci.yml/badge.svg)](https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network/actions)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

</div>

The **Cyberinfrastructure Knowledge Network (CKN)** is an extensible and portable distributed framework designed to optimize AI at the edge—particularly in dynamic environments where workloads may change suddenly (for example, in response to motion detection). CKN enhances edge–cloud collaboration by using historical data, graph representations, and adaptable deployment of AI models to satisfy changing accuracy‑and‑latency demands on edge devices.

*Tag: CI4AI, Software, PADI*

---

## Explanation

CKN facilitates seamless connectivity between edge devices and the cloud through event streaming, enabling real‑time data capture and processing. By leveraging event‑stream processing, it captures, aggregates, and stores historical system‑performance data in a knowledge graph that models application behaviour and guides model selection and deployment at the edge.

CKN comprises several core components:

- **CKN Daemon** – A lightweight service that resides on each edge server. It manages communication with edge devices, handles requests, captures performance data, and deploys AI models as needed. The daemon connects with the cloud‑based CKN system via a pub/sub system, capturing real‑time events from edge devices (model usage, resource consumption, prediction accuracy, latency, and more).
- **Event Streaming & Processing** – Stream‑processing techniques (for example, tumbling windows) aggregate events and generate real‑time alerts from edge‑device streams.
- **Knowledge Graph** – A Neo4j graph database that stores historical and provenance information about applications, models, and edge events. This comprehensive view of the system enables CKN to track model usage and analyse performance over time.

The primary objective of CKN is to provide a robust framework for optimising AI‑application deployment and resource allocation at the edge. Leveraging real‑time event streaming and knowledge graphs, CKN efficiently handles AI workloads, adapts to changing requirements, and supports scalable edge–cloud collaboration. 
The CKN topics and their details are mentioned [here](https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network/blob/main/docs/topics.md).

Refer to this paper for more information: [https://ieeexplore.ieee.org/document/10254827](https://ieeexplore.ieee.org/document/10254827).

![CKN Design](docs/ckn-design.png)

---

## How‑To Guide

See the full [documentation](https://cyberinfrastructure-knowledge-network.readthedocs.io/en/latest/) for detailed instructions on creating custom plug‑ins and streaming events to the knowledge graph.

### Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose) installed and running.
- Open network access to the following ports:
  - `7474` (Neo4j Web UI)
  - `7687` (Neo4j Bolt)
  - `2181` (ZooKeeper)
  - `9092` (Kafka Broker)
  - `8083` (Kafka Connect)
  - `8502` (CKN dashboard)

### Quick‑Start

#### 1. Clone the repository and start services

```bash
git clone https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network.git
make up
```

After setup completes, verify that all modules are running:

```bash
docker compose ps
```

#### 2. Stream an example camera‑trap event

```bash
docker compose -f examples/docker-compose.yml up -d --build
```

- View the streamed data on the CKN dashboard: [http://localhost:8502/Camera\_Traps](http://localhost:8502/Camera_Traps)

- Access the Neo4j Browser: [http://localhost:7474/browser/](http://localhost:7474/browser/) (username `neo4j`, password `PWD_HERE`). Run:

  ```cypher
  MATCH (n) RETURN n;
  ```

- Shut down services:

  ```bash
  make down
  docker compose -f examples/docker-compose.yml down
  ```

## Tutorial

### Step 1 | Set Up Your Environment

```bash
git clone https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network.git
cd cyberinfrastructure-knowledge-network
make up  # launches Kafka, Neo4j, and supporting services
```

*Wait a few moments for all services to initialise.*

### Step 2 | Create a CKN Topic

We will create a CKN topic named `temperature-sensor-data` to store temperature events.

**Update `docker-compose.yml`** (root directory) and add the topic to the broker environment:

```yaml
services:
  broker:
    environment:
      KAFKA_CREATE_TOPICS: "temperature-sensor-data:1:1"
```

Apply the change:

```bash
make down
make up
```


### Step 3 | Produce Events

#### Install required libraries

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install confluent-kafka  # <https://pypi.org/project/confluent-kafka/>
```

#### Create the producer script – `produce_temperature_events.py`

```python
from confluent_kafka import Producer
import json, time

kafka_conf = {"bootstrap.servers": "localhost:9092"}
producer = Producer(kafka_conf)

sensors = ["sensor_1", "sensor_2", "sensor_3"]

try:
    for i in range(10):
        for sensor_id in sensors:
            event = {
                "sensor_id": sensor_id,
                "temperature": round(20 + 10 * (0.5 - time.time() % 1), 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            producer.produce("temperature-sensor-data", key=sensor_id, value=json.dumps(event))
        producer.flush()
        time.sleep(1)
    print("Produced 10 events successfully.")
except Exception as e:
    print(f"An error occurred: {e}")
```

Run the producer:

```bash
python produce_temperature_events.py
```

### Step 4 | Consume and View Events

1. **Open a shell inside the broker container**

   ```bash
   docker exec -it broker bash  # replace "broker" with the container name if different
   ```

2. **Start the consumer**

   ```bash
   kafka-console-consumer --bootstrap-server localhost:9092 --topic temperature-sensor-data --from-beginning
   ```

   You should see JSON‑formatted temperature events.

Press **Ctrl +C** (or **Ctrl + Break** on Windows) to exit.

### Step 5 | Connect to a Data Sink

#### Create connector configuration – `neo4jsink-temperature-connector.json`

```json
{
  "name": "Neo4jSinkConnectorTemperature",
  "config": {
    "topics": "temperature-sensor-data",
    "connector.class": "streams.kafka.connect.sink.Neo4jSinkConnector",
    "errors.retry.timeout": "-1",
    "errors.retry.delay.max.ms": "1000",
    "errors.tolerance": "all",
    "errors.log.enable": true,
    "errors.log.include.messages": true,
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "key.converter.schemas.enable": false,
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": false,
    "neo4j.server.uri": "bolt://neo4j:7687",
    "neo4j.authentication.basic.username": "neo4j",
    "neo4j.authentication.basic.password": "PWD_HERE",
    "neo4j.topic.cypher.temperature-sensor-data": "MERGE (sensor:Sensor {id: event.sensor_id}) MERGE (reading:TemperatureReading {timestamp: datetime(event.timestamp)}) SET reading.temperature = event.temperature MERGE (sensor)-[:REPORTED]->(reading)"
  }
}
```

Place the file in `ckn_broker/connectors/` (or your chosen directory).

#### Register the connector – `setup_connector.sh`

```bash
curl -X POST -H "Content-Type: application/json" \
     --data @/app/neo4jsink-temperature-connector.json \
     http://localhost:8083/connectors
```

Restart CKN:

```bash
make down
make up
```

Run the temperature‑event producer again:

```bash
python produce_temperature_events.py
```

### Step 6 | Visualise Data

1. **Open the Neo4j browser:** [http://localhost:7474/browser/](http://localhost:7474/browser/)

2. **Log in** – username `neo4j`, password `PWD_HERE`.

3. **Query the graph:**

   ```cypher
   MATCH (s:Sensor)-[:REPORTED]->(r:TemperatureReading)
   RETURN s, r;
   ```

4. **Explore** the graph using Neo4j visual tools.

---

## Next Steps

You have successfully set up a temperature‑monitoring use case with **CKN**, **Kafka**, and **Neo4j**. Consider:

- **Adding more sensors** to simulate a larger network.
- Extending the cypher mapping to handle additional event attributes.
- Integrating alerting or dashboarding tools for real‑time monitoring.

---

## License

The Cyberinfrastructure Knowledge Network (CKN) is copyrighted by the Indiana University Board of Trustees and is distributed under the BSD 3-Clause License. See `LICENSE.txt` for more information.

## Acknowledgements

This research is funded in part by the National Science Foundation (award #2112606 – *AI Institute for Intelligent CyberInfrastructure with Computational Learning in the Environment* \[ICICLE]) and by the *Data to Insight Center* (D2I) at Indiana University.
