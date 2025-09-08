# Model Placement Agent

A containerized AI agent that provides model recommendations using the Patra Knowledge Graph via HTTP-based tools.

## Features

- **AI-Powered Recommendations**: Uses LangGraph and LangChain to provide intelligent model recommendations
- **HTTP Integration**: Uses HTTP requests to connect to Patra Server for tool access
- **Knowledge Graph Integration**: Accesses real model data through HTTP-based tools
- **Ollama-First Design**: Prioritizes local Ollama models for development, with fallback to cloud APIs
- **Containerized**: Fully containerized with Docker for easy deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Ollama running locally (recommended) or API keys for cloud providers

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Ollama Configuration (recommended for local development)
OLLAMA_HOST=http://localhost:11434

# Patra Server Configuration
PATRA_SERVER_URL=http://localhost:5002

# Optional: Cloud LLM Provider API Keys (fallback)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Neo4j Configuration (if using local Neo4j)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PWD=password
ENABLE_MC_SIMILARITY=False
```

### Running the Application

#### Option 1: Standalone (requires external services)
```bash
# Build and run the model recommendation agent
docker-compose up model-placement-agent
```

#### Option 2: With Patra MCP Server
```bash
# Run with Patra MCP Server
docker-compose --profile patra-server up
```

#### Option 3: With Ollama (recommended for local development)
```bash
# Run with Ollama for local LLM (no API keys needed)
docker-compose --profile ollama up
```

#### Option 4: Full Stack (all services)
```bash
# Run everything including Neo4j
docker-compose --profile neo4j --profile patra-server --profile ollama up
```

### Building the Image

```bash
# Build the Docker image
docker build -t model-placement-agent .

# Or use docker-compose
docker-compose build model-placement-agent
```

## Architecture

The application consists of:

1. **Model Recommendation Agent**: Main application that provides AI-powered recommendations
2. **Patra MCP Server**: Knowledge graph server (optional, can use external)
3. **Ollama**: Local LLM server (optional, can use external APIs)
4. **Neo4j**: Graph database (optional, can use external)

## API Integration

The agent connects to the Patra MCP Server using the Model Context Protocol (MCP) to:
- List all available models
- Get detailed model information
- Search for models with specific criteria
- Retrieve performance metrics

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
```

### Adding New Prompts

Add new prompt files to the `prompts/` directory and reference them in your code using the `load_prompt_from_file()` function.

## Troubleshooting

### Common Issues

1. **No LLM Provider Available**: Ensure Ollama is running or at least one API key is set
2. **Connection to Patra Server Failed**: Check PATRA_SERVER_URL and ensure the server is running
3. **Ollama Connection Failed**: Ensure Ollama is running and accessible

### Logs

Check container logs:
```bash
docker-compose logs model-placement-agent
```

## Contributing

1. Make changes to the code
2. Test locally
3. Build and test the Docker image
4. Submit a pull request
