import os
import asyncio
import sys
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from utils import get_large_language_model

load_dotenv()


async def create_mcp_tools():
    """Create MCP-based tools that communicate with the Patra MCP server"""
    patra_mcp_url = os.getenv('PATRA_MCP_SERVER_URL', 'http://patra-mcp-server:8001')
    
    # Configure MCP client to connect to Patra MCP server
    client = MultiServerMCPClient({
        "patra": {
            "url": f"{patra_mcp_url}",
            "transport": "streamable_http",
        }
    })
    
    # Get tools from the MCP server
    tools = await client.get_tools()
    return tools, client


async def run_agent():
    """Main agent execution function using MCP client"""
    
    try:
        # Get Patra tools via MCP
        print(f"Connecting to MCP server at: {os.getenv('PATRA_MCP_SERVER_URL', 'http://patra-mcp-server:8001')}")
        tools, client = await create_mcp_tools()
        print(f"Loaded {len(tools)} Patra tools via MCP")
        
        # Print tool names for debugging
        for i, tool in enumerate(tools):
            print(f"  {i+1}. {tool.name}: {tool.description[:100]}...")
        
        model = get_large_language_model()

        # Check if the model supports tools (required for create_react_agent)
        try:
            # Test if the model supports bind_tools
            test_model = model.bind_tools([])
            print("✅ Model supports tool binding")
            
            # Create a single agent with MCP tools
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
        
        # Run the agent with async support
        result = await agent.ainvoke({
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
        print(f"❌ Error connecting to MCP server: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        print("💡 Make sure the Patra MCP server is running and accessible at the configured URL")
        print("💡 Check that the MCP server is running on the correct port and host")
        print("\n🔄 Exiting gracefully...")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_agent())