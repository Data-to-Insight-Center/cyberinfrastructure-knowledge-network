## Cyberinfrastructure Knowledge Network (CKN)

### Overview

The Cyberinfrastructure Knowledge Network (CKN) repository provides the setup and components required to run CKN. This system integrates various services to manage and analyze data using a sophisticated pipeline involving data ingestion, processing, and visualization.

![CKN Design](ckn-design.png)

### Components
- **Broker**: Sets up Kafka broker, topics, and connectors for streaming data.
- **Knowledge Graph**: Manages neo4j db's infrastructure and connections.
- **Stream Processors**: Integrates with CKN to enhance data processing workflows. More details at [CKN Stream Processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors). 
- **Dashboard**: Provides a Streamlit dashboard for visualizing data from knowledge graph and a LLM-based chatbot.

### Getting Started
```bash
make up
```

### Plugins
- **Oracle CKN Daemon**: Reads, processes, and sends camera trap events from Oracle Daemon and Power Measuring plugin.
