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
            print("🔄 Switching to Ollama-compatible mode...")
            
            # Fallback mode for Ollama - call tools directly and provide context to the model
            print("\n" + "="*60)
            print("OLLAMA COMPATIBLE MODE")
            print("="*60)
            
            # Call tools directly to get data
            print("📊 Fetching model data from Patra server...")
            model_cards = tools[0]()  # get_model_cards
            model_deployments = tools[1]()  # get_model_deployments  
            avg_compute_time = tools[2]()  # get_average_compute_time
            
            # Create a comprehensive prompt with the data
            prompt = f"""
You are a model placement agent. Based on the following data from the Patra knowledge graph, provide insights about model compute times and recommendations.

MODEL CARDS DATA:
{model_cards}

MODEL DEPLOYMENTS DATA:
{model_deployments}

AVERAGE COMPUTE TIME DATA:
{avg_compute_time}

Please analyze this data and provide:
1. Summary of the average compute times
2. Any notable patterns or insights
3. Recommendations for model placement based on compute efficiency

Provide a clear, structured response.
"""
            
            # Use the model directly without tool binding
            print("🤖 Generating response with Ollama...")
            response = model.invoke(prompt)
            
            print("\n" + "="*60)
            print("MODEL PLACEMENT ANALYSIS")
            print("="*60)
            print(response.content)
            print("="*60)
            
            print(f"\n✅ Successfully analyzed data using Ollama in compatible mode!")
            print("💡 For full agent functionality with tool binding, consider using Anthropic or OpenAI models")
            return
        
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