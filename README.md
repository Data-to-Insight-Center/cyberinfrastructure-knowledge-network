## Cyberinfrastructure Knowledge Network (CKN)

This repo provides the setup and components required to run CKN. It integrates various services to manage and analyze data using a sophisticated pipeline involving data ingestion, processing, and visualization.

![CKN Design](ckn-design.png)

### Components
- **Broker**: Configures Kafka broker, topics, and connectors for streaming data.
- **Knowledge Graph**: Manages Neo4j database infrastructure and connections.
- **Stream Processors**: Integrates with CKN to enhance data processing workflows. More details at [CKN Stream Processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors). 
- **Dashboard**: Provides a Streamlit dashboard for visualizing data from knowledge graph and a chatbot powered by a large language model.

### Plugins
- **Oracle CKN Daemon**: Reads, processes, and sends camera trap events from Oracle Daemon and Power Measuring plugin.

## Getting Started
To get started with CKN, ensure that Docker is running. Then, bring up all the required services by starting Docker and running the command below:
```bash
make up
```

## Hello World Example
Once the services are up, produce an example event by running:
```bash
pip install -r example/requirements.txt
python example/producer.py
```
Then, go to the [Dashboard](http://localhost:8502/Camera_Traps) to view the streamed data.
To see the data in the database, access the [local Neo4j instance](http://localhost:7474/browser/) using the username `neo4j` and password `PWD_HERE`.

To shut down CKN, run:
```bash
make down
```