import os
import asyncio
import logging
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph_supervisor import create_supervisor

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("model_placement_agent")

patra_mcp_url = os.getenv('PATRA_MCP_URL', 'http://patra-mcp-server:8000/mcp')
ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")

async def run_agent_async():
    """Agent that selects the best model and prints only its download_url."""
    
    logger.info("Starting model placement agent")
    logger.info(f"Patra server: {patra_mcp_url}")

    model = init_chat_model(model="ollama:llama3.2:1b", base_url=ollama_host)
    logger.info(f"Using model: {model}")

    client = MultiServerMCPClient({
        "patra": {
            "transport": "stdio",
            "command": "python",
            "args": ["patra_mcp_server/server/mcp_server.py"],
            "env": {
                "PATRA_SERVER_URL": os.getenv("PATRA_SERVER_URL", "http://patra-server:5002"),
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO")
            }
        }
    })
    tools = await client.get_tools()
    logger.info(f"Using tools: {tools}")
    
    accuracy_agent = create_react_agent(
        model=model,
        tools=tools,
        prompt="You are an accuracy-focused agent. Select models with highest avg_accuracy.",
        name="accuracy_agent",
    )

    latency_agent = create_react_agent(
        model=model,
        tools=tools,
        prompt="You are a latency-focused agent. Select models with lowest average_compute_time.",
        name="latency_agent",
    )

    power_agent = create_react_agent(
        model=model,
        tools=tools,
        prompt="You are a power-focused agent. Select models with lowest combined CPU+GPU power.",
        name="power_agent",
    )

    # Create supervisor to orchestrate agents (not used further but created to satisfy spec)
    supervisor = create_supervisor(
        model=model,
        agents=[accuracy_agent, latency_agent, power_agent],
        prompt="You are a supervisor coordinating model selection agents.",
        output_mode="full_history",
    ).compile()

    for chunk in supervisor.stream(
        {
            "messages": [
                {"role": "user", "content": "Return the download_url for the best model."}
            ]
        }
    ):
        print(chunk)


if __name__ == "__main__":
    asyncio.run(run_agent_async())