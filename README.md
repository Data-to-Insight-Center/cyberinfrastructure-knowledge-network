# Cyberinfrastructure Knowledge Network (CKN)

This repository provides the setup and components required to run the Cyberinfrastructure Knowledge Network (CKN). It integrates various services to manage and analyze data using a sophisticated pipeline involving data ingestion, processing, and visualization.

![CKN Design](ckn-design.png)

## Table of Contents

- [About The Project](#about-the-project)
- [Components](#components)
- [Plugins](#plugins)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Hello World Example](#hello-world-example)
- [Shutting Down](#shutting-down)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## About The Project

CKN is designed to manage and analyze data through a sophisticated pipeline that involves data ingestion, processing, and visualization. This project aims to streamline data workflows by integrating various services.

## Components

- **Broker**: Configures Kafka broker, topics, and connectors for streaming data.
- **Knowledge Graph**: Manages Neo4j database infrastructure and connections.
- **Stream Processors**: Integrates with CKN to enhance data processing workflows. More details can be found in the [CKN Stream Processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors).
- **Dashboard**: Provides a Streamlit dashboard for visualizing data from the knowledge graph and a chatbot powered by a large language model.

## Plugins

- **Oracle CKN Daemon**: Reads, processes, and sends camera trap events from Oracle Daemon and Power Measuring plugin.

## Getting Started

### Prerequisites

- Ensure Docker is installed and running on your machine.

### Usage

1. **Start Services**
   ```bash
   make up
   ```

2. **Run Example**
   Once the services are up, produce an example event by running:
   ```bash
   pip install -r examples/requirements.txt
   python examples/daemon.py
   ```

3. **View Streamed Data**
   - Access the [Dashboard](http://localhost:8502/Camera_Traps) to view streamed data.
   - Check the [local Neo4j instance](http://localhost:7474/browser/) with username `neo4j` and password `PWD_HERE`.

4. **Stop Services**
    To shut down CKN, run:
    ```bash
    make down
    ```