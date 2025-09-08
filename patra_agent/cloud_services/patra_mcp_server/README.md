# Patra Unified Server

A unified container that combines the Patra Knowledge Graph REST API with LangGraph-compatible sync tools.

## Features

- **🔗 Unified Architecture**: Combines Flask REST API and LangGraph tools in a single container
- **🛠️ LangGraph Compatible**: Provides sync tools that work directly with LangGraph agents
- **📊 Knowledge Graph Access**: Direct access to Neo4j database without HTTP overhead
- **🚀 High Performance**: Eliminates the need for separate MCP server and HTTP calls
- **🔧 Easy Integration**: Simple Python client for LangGraph applications

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Patra Unified Server                       │
├─────────────────────────────────────────────────────────────┤
│  Flask REST API (Port 5002)                                │
│  ├── /modelcards                                           │
│  ├── /modelcard/{id}                                       │
│  ├── /modelcards/search                                    │
│  └── /tools (LangGraph tools info)                         │
├─────────────────────────────────────────────────────────────┤
│  LangGraph Sync Tools                                      │
│  ├── get_model_card                                        │
│  ├── list_all_model_cards                                  │
│  ├── search_model_cards                                    │
│  ├── get_model_deployments                                 │
│  └── get_average_statistic                                 │
├─────────────────────────────────────────────────────────────┤
│  Direct Database Access                                    │
│  └── Neo4j (via MCReconstructor)                          │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Using Docker Compose

```bash
# Start the unified server with Neo4j
docker-compose -f docker-compose.unified.yml up

# Or start just the server (requires external Neo4j)
docker-compose -f docker-compose.unified.yml up patra-unified-server
```

### Using Docker

```bash
# Build the image
docker build -f Dockerfile.unified -t patra-unified-server .

# Run with external Neo4j
docker run -p 5002:5002 \
  -e NEO4J_URI=bolt://your-neo4j-host:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PWD=password \
  patra-unified-server
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

### Method 1: Direct Import (Recommended)

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

### Method 2: Using the Client

```python
from patra_tools import PatraToolsClient

# Initialize client
client = PatraToolsClient(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

# Get tools
tools = client.get_tools()

# Use with LangGraph
agent = create_react_agent(model=llm, tools=tools)
```

## Available Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `get_model_card` | Get detailed model information | `model_id: str` |
| `list_all_model_cards` | List all models | None |
| `list_model_ids` | List all model IDs | None |
| `search_model_cards` | Search models by query | `query: str` |
| `get_model_deployments` | Get model deployments | `model_id: str` |
| `get_model_download_url` | Get model download URL | `model_id: str` |
| `get_average_compute_time` | Get average compute time | `model_id: str` |
| `get_average_statistic` | Get any model statistic | `model_id: str`, `statistic: str` |

## REST API Endpoints

The unified server also provides the same REST API as the original Patra server:

- `GET /` - Health check
- `GET /modelcards` - List all model cards
- `GET /modelcard/{id}` - Get specific model card
- `GET /modelcards/search?q={query}` - Search model cards
- `GET /modelcard/{id}/deployments` - Get model deployments
- `GET /modelcard/{id}/average_compute_time` - Get average compute time
- `GET /modelcard/{id}/average/{statistic}` - Get any statistic
- `GET /tools` - Get LangGraph tools information

## Example Usage

See `examples/langgraph_example.py` for a complete example of using the unified server with LangGraph.

## Benefits over Separate Services

1. **Performance**: Direct database access eliminates HTTP overhead
2. **Simplicity**: Single container to manage
3. **Reliability**: No network dependencies between services
4. **Development**: Easier to develop and debug
5. **Deployment**: Simpler deployment and scaling

## Migration from MCP Server

If you're currently using the separate MCP server, migration is straightforward:

### Before (MCP Server)
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "patra_kg": {
        "command": "python",
        "args": ["-m", "mcp_server"],
        "cwd": "../patra_mcp_server/server"
    }
})
async_tools = await client.get_tools()
tools = convert_async_tools_to_sync(async_tools)
```

### After (Unified Server)
```python
from patra_tools import get_patra_tools

tools = get_patra_tools()  # Direct sync tools, no async conversion needed
```

## Testing

```bash
# Test the unified server
docker run --rm patra-unified-server python test_unified_tools.py

# Test with docker-compose
docker-compose -f docker-compose.unified.yml up --build
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**: Check NEO4J_URI, NEO4J_USER, and NEO4J_PWD
2. **Tools Not Loading**: Ensure LangChain dependencies are installed
3. **Pydantic Errors**: Check that tool classes have proper type annotations

### Logs

```bash
# View container logs
docker logs patra-unified-server

# View with docker-compose
docker-compose -f docker-compose.unified.yml logs patra-unified-server
```

## Contributing

1. Make changes to the unified server
2. Test with `python test_unified_tools.py`
3. Build and test the Docker image
4. Submit a pull request
