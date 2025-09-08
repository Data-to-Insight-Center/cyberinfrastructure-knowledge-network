import os
import sys
import httpx
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from utils import get_large_language_model

load_dotenv()


def create_http_tools():
    """Create HTTP-based tools that communicate with the Patra server"""
    patra_server_url = os.getenv('PATRA_SERVER_URL', 'http://patra-server:5002')
    
    @tool
    def get_model_cards() -> str:
        """Get all model cards from the Patra knowledge graph"""
        try:
            response = httpx.get(f"{patra_server_url}/tools/model_cards", timeout=10.0)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error getting model cards: {str(e)}"
    
    @tool
    def get_model_deployments() -> str:
        """Get all model deployments from the Patra knowledge graph"""
        try:
            response = httpx.get(f"{patra_server_url}/tools/model_deployments", timeout=10.0)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error getting model deployments: {str(e)}"
    
    @tool
    def get_average_compute_time() -> str:
        """Get the average compute time for all models in the Patra knowledge graph"""
        try:
            response = httpx.get(f"{patra_server_url}/tools/average_compute_time", timeout=10.0)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error getting average compute time: {str(e)}"
    
    return [get_model_cards, get_model_deployments, get_average_compute_time]


def run_agent():
    """Main agent execution function using HTTP-based tools"""
    
    try:
        # Get Patra tools via HTTP
        print(f"Connecting to Patra server at: {os.getenv('PATRA_SERVER_URL', 'http://patra-server:5002')}")
        tools = create_http_tools()
        print(f"Loaded {len(tools)} Patra tools via HTTP")
        
        # Print tool names for debugging
        for i, tool in enumerate(tools):
            print(f"  {i+1}. {tool.name}: {tool.description[:100]}...")
        
        model = get_large_language_model()

        # Check if the model supports tools (required for create_react_agent)
        try:
            # Test if the model supports bind_tools
            test_model = model.bind_tools([])
            print("✅ Model supports tool binding")
            
            # Create a single agent with the working approach from simple_main.py
            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt="Find the average compute time for all models in the patra knowledge graph.",
                name="model_placement_agent"
            )
            
        except (NotImplementedError, AttributeError) as e:
            print(f"❌ Model does not support tool binding: {e}")
            print("⚠️  Current model (likely Ollama) does not support the tool binding required for LangGraph agents")
            print("💡 To use the full agent functionality, please:")
            print("   1. Set ANTHROPIC_API_KEY environment variable, or")
            print("   2. Set OPENAI_API_KEY environment variable")
            print("   3. Restart the container")
            print("\n🔄 Exiting gracefully...")
            sys.exit(0)
        
        result = agent.invoke({
            "messages": [
                {
                    "role": "user", 
                    "content": "Find the average compute time for all models in the patra knowledge graph."
                }
            ]
        })
        
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
            
    except Exception as e:
        print(f"❌ Error connecting to Patra server: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        print("💡 Make sure the Patra server is running and accessible at the configured URL")
        print("💡 Check that the Patra server is running on the correct port and host")
        print("\n🔄 Exiting gracefully...")
        sys.exit(1)


if __name__ == "__main__":
    run_agent()