## Cyberinfrastructure Knowledge Network (CKN)

## Overview

The Cyberinfrastructure Knowledge Network (CKN) repository provides the setup and components required to run CKN. This system integrates various services to manage and analyze data using a sophisticated pipeline involving data ingestion, processing, and visualization.

![CKN Design](ckn-design.png)

### Components
- **Broker**: Sets up Kafka broker, topics, and connectors for streaming data.
- **Knowledge Graph**: Manages neo4j database's infrastructure and connections.
- **Stream Processors**: Integrates with CKN to enhance data processing workflows. More details at [CKN Stream Processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors). 
- **Dashboard**: Provides a Streamlit dashboard for visualizing data from knowledge graph and a LLM-based chatbot.

### Plugins
- **Oracle CKN Daemon**: Reads, processes, and sends camera trap events from Oracle Daemon and Power Measuring plugin.

## Getting Started
To get started with CKN, first, bring up all the required services:
```bash
make up
```
This command will set up the necessary Docker containers, including the Kafka broker, Neo4j database, and the Streamlit dashboard.

### Hello World Example
Once the services are up, run the following command to produce an example event:
```bash
python example/producer.py
```
Then, go to the [Dashboard](http://localhost:8502/Camera_Traps) to view the streamed data from the local instance of [neo4j database](http://localhost:7474/browser/).