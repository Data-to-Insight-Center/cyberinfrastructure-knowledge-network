# Cyberinfrastructure Knowledge Network (CKN)

CKN connects the Edge to the cloud by means of event streaming.

<img src="ckn-design.png" alt="CKN Design" style="width:100%;">

## Components

### Broker
The system utilizes **Apache Kafka**, an open-source distributed event streaming platform. It functions as a message broker using a publisher-subscriber model with predefined topics for published events. 

### Knowledge Graph
The knowledge graph in the CKN system is powered by the **Neo4j database**. It contains comprehensive application and system-level information on the Edge System and historical data over time.

### Stream Processors
The stream processor employs a **tumbling window** to aggregate and summarize values. The processed data is sent to a separate topic within the pub-sub system. More information is available in the [CKN Stream Processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors).

### Dashboard
A **Streamlit dashboard** is provided for visualizing data from the knowledge graph. Additionally, it includes a chatbot powered by a large language model for enhanced user interaction.

## Plugins
**Oracle CKN Daemon**: Reads, processes, and sends camera trap events from Oracle Daemon and Power Measuring plugin.

## Getting Started

### Prerequisites

- Ensure docker and docker-compose is installed and running on your machine.

### Quickstart
We use Docker Compose to create an environment with Confluent Platform components and Neo4j running inside Docker.

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
  View the streamed data on the [dashboard](http://localhost:8502/Camera_Traps) or check the [local neo4j instance](http://localhost:7474/browser/) with username `neo4j` and password `PWD_HERE`. 

   Run the following query to view the data: ```MATCH (n) RETURN n``` 

<br>

3. **To shut down and remove all containers, run:**
    ```bash
    make down
   docker compose -f examples/docker-compose.yml down
    ```
   
### Reference
S. Withana and B. Plale, "CKN: An Edge AI Distributed Framework," 2023 IEEE 19th International Conference on e-Science (e-Science), Limassol, Cyprus, 2023, pp. 1-10, doi: 10.1109/e-Science58273.2023.10254827