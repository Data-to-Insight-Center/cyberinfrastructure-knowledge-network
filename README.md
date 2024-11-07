# Cyberinfrastructure Knowledge Network (CKN)

The Cyberinfrastructure Knowledge Network (CKN) is an extensible and portable distributed framework designed to optimize AI at the edge, particularly in dynamic environments where workloads on the edge server may change suddenly, such as in response to motion detection. CKN enhances edge-cloud collaboration by using historical data, graph representations, and adaptable deployment of AI models to meet changing demands in accuracy and latency at edge devices.

CKN facilitates seamless connectivity between edge devices and the cloud through event streaming, enabling real-time data capture and processing. By leveraging event stream processing, CKN captures, aggregates, and stores historical data about system performance. This data is stored in a knowledge graph and used to model application behavior and optimize model selection and deployment at the edge.

The CKN framework includes several core components:

- **CKN Daemon:** A lightweight service that resides on each edge server, responsible for managing communications with edge devices, handling requests, capturing performance data, and deploying AI models as needed. The daemon connects with the cloud-based CKN system via a pub/sub system. This module captures real-time events from edge devices, augmenting them with details such as model usage, resource consumption, prediction accuracy, and latency. 

- **Event Streaming and Processing:** It uses stream processing techniques, like tumbling windows, to aggregate events and generate real-time alerts based on the streaming data from the edge.

- **Knowledge Graph:** A Neo4j Graph database that stores historical data and provenance information about the system, including applications, available models, and events from edge devices. This knowledge graph enables CKN to maintain a comprehensive view of system evolution, track model usage, and analyze performance over time.

The primary objective of CKN is to provide a robust framework that optimizes AI application deployment and resource allocation at the edge. By leveraging real-time event streaming and knowledge graphs, CKN creates a system capable of efficiently handling AI workloads, adapting to changing requirements, and supporting scalable edge-cloud collaboration.

For more information on CKN, please refer to the [CKN paper](https://ieeexplore.ieee.org/document/10254827).

<img src="ckn-design.png" alt="CKN Design" style="width:100%;">

## Components

This GitHub repository includes all necessary components to set up and run CKN, including:

Together, these tools offer a comprehensive setup for deploying CKN, making it easy to adapt the framework to specific edge-computing environments.

### Broker
**Apache Kafka** is used as the message broker. It operates on a publisher-subscriber model, allowing for real-time data streaming and processing. Kafka efficiently handles data streams by storing and processing them in the order they are received.

### Knowledge Graph
CKN employs a **Neo4j database** for its knowledge graph. Neo4j is a leading graph database known for its scalability, flexibility, and ability to handle complex relationships between data entities. It uses a property graph model with nodes and relationships, which makes it suitable for storing and querying connected data efficiently.

### Stream Processors
Stream processing in CKN is performed using a **tumbling window** approach. This method aggregates and summarizes data over fixed intervals, which is then published to a separate topic within the Kafka system.  More information is available in the [CKN Stream Processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors).

### Dashboard
A **Streamlit dashboard** is provided for visualizing data from the knowledge graph. Streamlit is an open-source Python library that simplifies the creation of interactive web applications and dashboards. It allows users to visualize data easily and interact with machine learning models without requiring extensive front-end development skills.

## Plugins
**CKN Oracle Daemon**: Reads, processes, and sends camera trap events from Oracle Daemon and Power Measuring plugin.

---

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose**: Ensure both are installed and running.
- **Available Ports**: Ensure the following ports are available: `7474`, `7687`, `2181`, `9092`, `8083`, `8502`.

### Quickstart

1. **Clone the Repository and Start Services**:
   ```bash
   git clone https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network.git
   ```
   ```bash
   make up
   ```

   Once setup is complete, verify that all modules are running:
   ```bash
   docker compose ps
   ```

2. **Produce an Example Event**:
   To stream a sample event, navigate to the `examples` directory and run:
    ```bash
   docker compose -f examples/docker-compose.yml up -d --build
   ```
   
   View streamed data on the [CKN dashboard](http://localhost:8502/Camera_Traps) or via the [Neo4j Browser](http://localhost:7474/browser/). Use `neo4j` as the username and replace `PWD_HERE` with your password, then run:
   ```cypher
   MATCH (n) RETURN n
   ```

3. **Shut Down and Clean Up**:
   To stop and remove all running containers:
    ```bash
   make down
   docker compose -f examples/docker-compose.yml down
    ```

---

## License

The Cyberinfrastructure Knowledge Network is copyrighted by the Indiana University Board of Trustees and is distributed under the BSD 3-Clause License. See `LICENSE.txt` for more information.

## Reference

S. Withana and B. Plale, "CKN: An Edge AI Distributed Framework," *2023 IEEE 19th International Conference on e-Science (e-Science)*, Limassol, Cyprus, 2023, pp. 1-10, doi: 10.1109/e-Science58273.2023.10254827.
