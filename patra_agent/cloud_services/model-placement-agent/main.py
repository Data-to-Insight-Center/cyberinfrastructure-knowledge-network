import os
import asyncio
import sys
import httpx
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from utils import get_large_language_model

load_dotenv()


def create_http_tools():
    """Create HTTP-based tools that communicate with the Patra server"""
    from langchain_core.tools import tool
    
    patra_server_url = os.getenv('PATRA_SERVER_URL', 'http://patra-server:5002')
    
    @tool
    def list_all_model_cards() -> str:
        """Get a list of all model cards in the knowledge graph"""
        try:
            response = httpx.get(f"{patra_server_url}/modelcards")
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error fetching model cards: {str(e)}"
    
    @tool
    def get_model_card(model_id: str) -> str:
        """Get detailed information about a specific model card by ID"""
        try:
            response = httpx.get(f"{patra_server_url}/modelcard/{model_id}")
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error fetching model card {model_id}: {str(e)}"
    
    @tool
    def list_model_ids() -> str:
        """Get a list of all model card IDs in the knowledge graph"""
        try:
            response = httpx.get(f"{patra_server_url}/modelcards/ids")
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error fetching model IDs: {str(e)}"
    
    @tool
    def search_model_cards(query: str) -> str:
        """Search for model cards using full-text search"""
        try:
            response = httpx.get(f"{patra_server_url}/modelcards/search", params={"q": query})
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error searching model cards: {str(e)}"
    
    @tool
    def get_model_deployments(model_id: str) -> str:
        """Get all deployments for a specific model"""
        try:
            response = httpx.get(f"{patra_server_url}/modelcard/{model_id}/deployments")
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error fetching deployments for {model_id}: {str(e)}"
    
    @tool
    def get_model_download_url(model_id: str) -> str:
        """Get the download URL for a specific model"""
        try:
            response = httpx.get(f"{patra_server_url}/modelcard/{model_id}/download")
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error fetching download URL for {model_id}: {str(e)}"
    
    @tool
    def get_average_compute_time(model_id: str) -> str:
        """Get the average compute time for a specific model"""
        try:
            response = httpx.get(f"{patra_server_url}/modelcard/{model_id}/average/compute_time")
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error fetching average compute time for {model_id}: {str(e)}"
    
    @tool
    def get_average_statistic(model_id: str, statistic: str) -> str:
        """Get the average of any statistic for a specific model (e.g., 'avg_compute_time', 'mean_latency_ms', 'mean_accuracy')"""
        try:
            response = httpx.get(f"{patra_server_url}/modelcard/{model_id}/average/{statistic}")
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error fetching {statistic} for {model_id}: {str(e)}"
    
    return [
        list_all_model_cards,
        get_model_card,
        list_model_ids,
        search_model_cards,
        get_model_deployments,
        get_model_download_url,
        get_average_compute_time,
        get_average_statistic
    ]


async def run_agent():

    # Get Patra tools via HTTP API
    tools = create_http_tools()
    print(f"Loaded {len(tools)} Patra tools via HTTP API")
    
    # Print tool names for debugging
    for i, tool in enumerate(tools):
        print(f"  {i+1}. {tool.name}: {tool.description[:100]}...")
    
    model = get_large_language_model()


    # Create a single agent with the working approach from simple_main.py
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt="",
        name="model_recommendation_agent"
    )

    # Test the agent
    print("\n🧪 Testing agent with model recommendation request...")
    
    result = agent.invoke({
        "messages": [
            {
                "role": "user", 
                "content": "Recommend the best model in the patra knowledge graph for image classification. You MUST use the available tools to get real data from the knowledge graph. Do not make up any model information."
            }
        ]
    })
    
    print("\n📋 Agent Response:")
    print("="*60)
    
    # Extract and display the final response
    messages = result.get("messages", [])
    for msg in messages:
        if hasattr(msg, 'content') and msg.content and not msg.content.startswith('{"name":'):
            if hasattr(msg, 'type') and msg.type == 'ai':
                print(msg.content)
                print("="*60)
    
    # Check if the agent actually used tools
    tool_calls = []
    for msg in messages:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_calls.extend(msg.tool_calls)
    
    if tool_calls:
        print(f"\n✅ Agent used {len(tool_calls)} tool calls!")
        for i, call in enumerate(tool_calls):
            print(f"  {i+1}. {call['name']} - {call.get('args', {})}")
    else:
        print("\n❌ Agent did not use any tools!")


def test_patra_server_connection():
    """Test basic connection to Patra server"""
    patra_server_url = os.getenv('PATRA_SERVER_URL', 'http://patra-server:5002')
    
    print(f"Testing connection to Patra server at: {patra_server_url}")
    
    try:
        # Test basic connectivity
        response = httpx.get(f"{patra_server_url}/modelcards")
        print(f"✅ GET /modelcards: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test model IDs endpoint
        response = httpx.get(f"{patra_server_url}/modelcards/ids")
        print(f"✅ GET /modelcards/ids: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test tools endpoint
        response = httpx.get(f"{patra_server_url}/tools")
        print(f"✅ GET /tools: {response.status_code}")
        tools_data = response.json()
        print(f"   Found {len(tools_data.get('tools', []))} tools")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    # Check if we should run in test mode
    if os.getenv("TEST_MODE", "false").lower() == "true":
        test_patra_server_connection()
    else:
        asyncio.run(run_agent())