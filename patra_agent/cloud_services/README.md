# Cloud Services

This directory contains all cloud services for the Patra Knowledge Graph system, managed through a single `docker-compose.yml` file.

## Services

### Core Services
- **neo4j**: Graph database (ports 7474, 7687)
- **patra-server**: Knowledge Graph API + LangGraph tools (port 5002)
- **patra-mcp-server**: MCP server for Patra tools (port 8001)
- **model-placement-agent**: AI agent using Patra MCP tools
- **ollama**: Local LLM server (port 11434)

### Infrastructure Services
- **postgres**: PostgreSQL database (port 5432)
- **pgadmin**: PostgreSQL web interface (port 8080)
- **zookeeper**: Kafka coordination service (port 2181)
- **broker**: Kafka message broker (port 9092)
- **kafka-connect**: Kafka Connect for data integration (port 8083)

## Quick Start

### Full Stack (All Services)
```bash
# Start everything
docker-compose up

# Or start in background
docker-compose up -d
```

### Core Services Only
```bash
# Start only core services (Neo4j + Patra Server)
docker-compose up neo4j patra-server

# Or start in background
docker-compose up -d neo4j patra-server
```

### Individual Services
```bash
# Start specific services
docker-compose up neo4j patra-server model-placement-agent

# Start with infrastructure services
docker-compose up neo4j postgres kafka-connect
```

## Environment Variables

Create a `.env` file in this directory:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PWD=your_password_here
ENABLE_MC_SIMILARITY=False

# LLM Provider API Keys (for model-placement-agent)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Patra Server Configuration
PATRA_SERVER_URL=http://patra-server:5002

# Ollama Configuration
OLLAMA_HOST=http://ollama:11434

```

## Service Details

### Patra Server
- **Purpose**: Provides Knowledge Graph API and LangGraph-compatible tools
- **Port**: 5002
- **Endpoints**: 
  - `GET /` - Health check
  - `GET /modelcards` - List all model cards
  - `GET /modelcard/{id}` - Get specific model card
  - `GET /tools` - Get LangGraph tools information
- **Dependencies**: Neo4j

### Patra MCP Server
- **Purpose**: MCP (Model Context Protocol) server for Patra Knowledge Graph tools
- **Port**: 8001
- **Protocol**: MCP over HTTP
- **Tools**: All Patra Knowledge Graph tools available via MCP
- **Dependencies**: Neo4j
- **Usage**: Used by model-placement-agent for standardized tool access

### Model Recommendation Agent
- **Purpose**: AI agent that provides model recommendations using Patra tools
- **Dependencies**: Patra Server
- **Features**: Uses LangGraph with direct Patra tools (no MCP needed)

### Neo4j Database
- **Purpose**: Graph database for storing model cards and relationships
- **Ports**: 7474 (web interface), 7687 (bolt protocol)
- **Plugins**: APOC
- **Web Interface**: http://localhost:7474

### Ollama
- **Purpose**: Local LLM server for running models locally
- **Port**: 11434
- **Usage**: Alternative to OpenAI/Anthropic APIs

### Infrastructure Services
- **PostgreSQL**: Relational database for structured data
- **PgAdmin**: Web interface for PostgreSQL management
- **Kafka**: Message streaming platform for real-time data processing
- **Kafka Connect**: Data integration platform for connecting various systems

## Development

### Building Services
```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build patra-server
```

### Viewing Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs patra-server
docker-compose logs model-placement-agent
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Services                          │
├─────────────────────────────────────────────────────────────┤
│  Neo4j Database (Required)                                │
│  ├── Port 7474: Web Interface                            │
│  └── Port 7687: Bolt Protocol                            │
├─────────────────────────────────────────────────────────────┤
│  Patra Server (Required)                                  │
│  ├── Port 5002: REST API + LangGraph Tools               │
│  └── Dependencies: Neo4j                                  │
├─────────────────────────────────────────────────────────────┤
│  Model Recommendation Agent (Optional)                    │
│  ├── Profile: model-agent                                 │
│  └── Dependencies: Patra Server                           │
├─────────────────────────────────────────────────────────────┤
│  Ollama (Optional)                                        │
│  ├── Port 11434: Local LLM Server                        │
│  └── Profile: ollama                                      │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Make sure ports 5002, 7474, 7687, and 11434 are available
2. **Neo4j Connection**: Check that Neo4j is running and accessible
3. **Environment Variables**: Ensure all required environment variables are set

### Health Checks

```bash
# Check service status
docker-compose ps

# Check Neo4j health
curl http://localhost:7474

# Check Patra server health
curl http://localhost:5002
```

### Logs

```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f patra-server
```
