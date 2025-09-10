# Patra Server

A container that combines the Patra Knowledge Graph REST API with LangGraph-compatible sync tools.

## Features

- **🔗 Architecture**: Combines Flask REST API and LangGraph tools in a single container
- **🛠️ LangGraph Compatible**: Provides sync tools that work directly with LangGraph agents
- **📊 Knowledge Graph Access**: Direct access to Neo4j database without HTTP overhead
- **🚀 High Performance**: Eliminates the need for separate MCP server and HTTP calls
- **🔧 Easy Integration**: Simple Python client for LangGraph applications

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Patra Server                         │
├─────────────────────────────────────────────────────────────┤
│  Flask REST API (Port 5002)                                │
│  ├── /modelcards                                           │
│  ├── /modelcards/ids                                       │
│  ├── /modelcard/{id}                                       │
│  ├── /modelcard/{id}/download_url                          │
│  ├── /modelcard/{id}/deployments                           │
│  ├── /models/average_compute_time                          │
│  ├── /models/average_cpu_gpu                               │
│  ├── /models/average_accuracy                              │
│  └── /tools (LangGraph tools info)                         │
├─────────────────────────────────────────────────────────────┤
│  LangGraph Sync Tools                                      │
│  ├── get_model_card                                        │
│  ├── list_all_model_cards                                  │
│  ├── list_model_ids                                        │
│  ├── get_model_deployment_ids                              │
│  ├── get_model_download_url                                │
│  ├── get_average_compute_time                              │
│  └── get_average_statistic                                 │
├─────────────────────────────────────────────────────────────┤
│  Direct Database Access                                    │
│  └── Neo4j (via MCReconstructor)                          │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Using Docker Compose

```bash
# Start the server with Neo4j
docker-compose -f docker-compose.yml up patra-server
```

### Using Docker

```bash
# Build the image
docker build -f Dockerfile -t patra-server .

# Run with external Neo4j
docker run -p 5002:5002 \
  -e NEO4J_URI=bolt://your-neo4j-host:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PWD=password \
  patra-server
```

## Environment Variables

```bash
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PWD=password
ENABLE_MC_SIMILARITY=False

# Python Configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

## LangGraph Integration

### Direct Import

```python
from patra_tools import get_patra_tools
from langgraph.prebuilt import create_react_agent

# Get Patra tools
tools = get_patra_tools()

# Create LangGraph agent
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt="You are a model recommendation agent..."
)

# Use the agent
result = agent.invoke({"messages": [{"role": "user", "content": "Recommend a model"}]})
```

## Available Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `get_model_card` | Get detailed model information | `model_id: str` |
| `list_all_model_cards` | List all models | None |
| `list_model_ids` | List all model IDs | None |
| `get_model_deployments` | Get model deployments | `model_id: str` |
| `get_model_download_url` | Get model download URL | `model_id: str` |
| `get_average_compute_time` | Get average compute time | `model_id: str` |
| `get_average_statistic` | Get any model statistic | `model_id: str`, `statistic: str` |
| `get_average_compute_time_all_models` | Average compute time for all models | None |
| `get_average_cpu_gpu_all_models` | Average CPU/GPU for all models | None |
| `get_average_accuracy_all_models` | Average accuracy for all models | None |

## REST API Endpoints

The server provides the REST API:

- `GET /` - Health check
- `GET /modelcards` - List all model cards
- `GET /modelcards/ids` - List all model IDs
- `GET /modelcard/{id}` - Get specific model card
- `GET /modelcard/{id}/download_url` - Get model download URL (returns raw URL string)
- `GET /modelcard/{id}/deployments` - Get model deployments (returns list of `deployment_id`)
- `GET /modelcard/{id}/average_compute_time` - Get average compute time
- `GET /modelcard/{id}/average/{statistic}` - Get any statistic
- `GET /models/average_compute_time` - Average compute time for all models
- `GET /models/average_cpu_gpu` - Average CPU/GPU for all models
- `GET /models/average_accuracy` - Average accuracy for all models
- `GET /tools` - Get LangGraph tools information

## Testing

```bash
# View container logs
docker logs patra-server

# View with docker-compose
docker-compose logs patra-server
```

## Contributing

1. Make changes to the server
2. Test changes locally
3. Build and test the Docker image
4. Submit a pull request
