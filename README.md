# Cyberinfrastructure Knowledge Network (CKN)

## Overview

The Cyberinfrastructure Knowledge Network (CKN) repository provides the setup and components required to run CKN. This system integrates various services to manage and analyze data using a sophisticated pipeline involving data ingestion, processing, and visualization.

![CKN Design](ckn-design.png)

## Components

### CKN Broker
- **Purpose**: Sets up Kafka broker and connectors for streaming data.
- **Components**: Configures Kafka brokers, topics, and connectors. Includes knowledge graph sinks for handling streamed events.

### CKN KG (Knowledge Graph)
- **Purpose**: Defines the Docker Compose setup for the knowledge graph.
- **Components**: Manages the knowledge graph's infrastructure and connections.

### Stream Processors
For additional stream processing capabilities, visit the [CKN Stream Processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors). This repository contains stream processors that integrate with CKN to enhance data processing workflows.

### Dashboard
- **Purpose**: Provides a CKN Analytics dashboard for visualizing data from knowledge graph.
- **Features**: Offers a Chatbot and interactive insights into the data.

## Quickstart
```bash
docker-compose up
```

## Plugins
### Oracle CKN Daemon
- **Purpose**: Reads, processes, and sends camera trap events from Oracle Daemon and Power Measuring plugin.
- **Functionality**: Extracts only those events that have been fully processed by the image scoring plugin.
- **Deployment**: Includes Dockerfile and Docker Compose files for straightforward deployment of the daemon.
