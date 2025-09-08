# Model Recommendation Agent

A containerized AI agent that provides model recommendations using the Patra Knowledge Graph.

## Features

- **AI-Powered Recommendations**: Uses LangGraph and LangChain to provide intelligent model recommendations
- **Knowledge Graph Integration**: Connects to Patra MCP Server to access real model data
- **Multiple LLM Support**: Supports OpenAI, Anthropic, and Ollama models
- **Containerized**: Fully containerized with Docker for easy deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least one LLM provider API key (OpenAI, Anthropic, or Ollama)

### Environment Variables

Create a `.env` file with the following variables:

```bash
# LLM Provider API Keys (choose one or more)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Patra Server Configuration
PATRA_SERVER_URL=http://localhost:5002

# Ollama Configuration (for local LLM)
OLLAMA_HOST=http://localhost:11434

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

#### Option 3: With Ollama (local LLM)
```bash
# Run with Ollama for local LLM
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

1. **No LLM Provider Available**: Ensure at least one API key is set
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
