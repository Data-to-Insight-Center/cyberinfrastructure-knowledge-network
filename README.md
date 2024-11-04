# Cyberinfrastructure Knowledge Network (CKN)

CKN is a system designed to connect edge devices to the cloud using event streaming.

<img src="ckn-design.png" alt="CKN Design" style="width:100%;">

## Components

### Broker:
**Apache Kafka** is used as the message broker. It operates on a publisher-subscriber model, allowing for real-time data streaming and processing. Kafka efficiently handles data streams by storing and processing them in the order they are received.

### Knowledge Graph
CKN employs a **Neo4j database** for its knowledge graph. Neo4j is a leading graph database known for its scalability, flexibility, and ability to handle complex relationships between data entities. It uses a property graph model with nodes and relationships, which makes it suitable for storing and querying connected data efficiently.

### Stream Processors
Stream processing in CKN is performed using a **tumbling window** approach. This method aggregates and summarizes data over fixed intervals, which is then published to a separate topic within the Kafka system.  More information is available in the [CKN Stream Processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors).

### Dashboard
A **Streamlit dashboard** is provided for visualizing data from the knowledge graph. Streamlit is an open-source Python library that simplifies the creation of interactive web applications and dashboards. It allows users to visualize data easily and interact with machine learning models without requiring extensive front-end development skills.

## Plugins
**Oracle CKN Daemon**: Reads, processes, and sends camera trap events from Oracle Daemon and Power Measuring plugin.

## Getting Started

### Prerequisites

- Ensure docker and docker-compose is installed and running on your machine.
- Ensure the following ports are available on your machine: 7474, 7687, 2181, 9092, 8083, 8502.

### Quickstart

1. **Clone the repository and run:**
   ```bash
   make up
   ```
   When the process completes you can check if all the modules up and running with:
   ```bash
    docker compose ps
    ```

<br>

2. **To produce [an example event](examples/event.json), run:**
   ```bash
   docker compose -f examples/docker-compose.yml up -d --build
   ``` 
   View the streamed data on the [CKN dashboard](http://localhost:8502/Camera_Traps) or go to the [local neo4j instance](http://localhost:7474/browser/) with username `neo4j`, password `PWD_HERE` and run ```MATCH (n) RETURN n```. 

<br>

3. **To shut down and remove all containers, run:**
    ```bash
    make down
   docker compose -f examples/docker-compose.yml down
    ```
   
### License
The copyright to the Cyber-infrastructure Knowledge Network is held by the Indiana University Board of Trustees and distributed under the BSD 3-Clause License. See LICENSE.txt for more information.

### Reference
S. Withana and B. Plale, "CKN: An Edge AI Distributed Framework," 2023 IEEE 19th International Conference on e-Science (e-Science), Limassol, Cyprus, 2023, pp. 1-10, doi: 10.1109/e-Science58273.2023.10254827
