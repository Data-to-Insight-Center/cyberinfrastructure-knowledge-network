from langchain_core.messages import convert_to_messages
from langchain.chat_models import init_chat_model
import os

def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)

def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        is_subgraph = True

    for node_name, node_update in update.items():
        if node_update is None or "messages" not in node_update:
            continue
        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            # Only show human-readable messages, skip tool calls and internal transfers
            if hasattr(m, 'content') and m.content and not m.content.startswith('{"name":'):
                # Check if this is the final supervisor message with recommendations
                if node_name == "supervisor" and "recommendation" in m.content.lower():
                    print("\n" + "="*60)
                    print("STOCK RECOMMENDATIONS")
                    print("="*60)
                    print(m.content)
                    print("="*60)
                elif node_name == "price_recommender_agent":
                    print("\n" + "="*60)
                    print("FINAL RECOMMENDATIONS")
                    print("="*60)
                    print(m.content)
                    print("="*60)
                elif hasattr(m, 'type') and m.type == 'human':
                    # Show user messages
                    print(f"\nUser: {m.content}")
                elif hasattr(m, 'type') and m.type == 'ai' and not m.content.startswith('{"name":'):
                    # Show AI responses that aren't tool calls
                    print(f"\n{m.content}")

def load_prompt_from_file(filename):
    """Load prompt from a text file"""
    try:
        with open(f"prompts/{filename}", 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"⚠️  Prompt file {filename} not found, using default prompt")
        return "You are an AI agent. Please help the user with their request."

def get_large_language_model():
    """
    Get a LLM model with fallback options
    Priority: Claude (Anthropic) > OpenAI > Ollama
    """    
    # Try Anthropic Claude first (best for tool use)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            print("Initializing Anthropic Claude 3.5 Sonnet model")
            return init_chat_model(model="anthropic:claude-3-5-sonnet-20241022", api_key=anthropic_key)
        except Exception as e:
            print(f"⚠️  Anthropic failed: {e}")
    
    # Try OpenAI if available
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            print("Initializing OpenAI GPT-4o-mini model")
            return init_chat_model(model="openai:gpt-4o-mini", api_key=openai_key)
        except Exception as e:
            print(f"⚠️  OpenAI failed: {e}")
    
    # Try Ollama (may not support tools, but worth trying)
    try:
        print("Initializing Ollama 3.2 model")
        return init_chat_model(model="ollama:llama3.2")
    except Exception as e:
        print(f"⚠️  Ollama failed: {e}")
    
    raise Exception("No LLM provider available. Please set up Anthropic or OpenAI API key.")

def load_prompt_from_file(filename):
    """Load prompt from a text file"""
    try:
        with open(f"prompts/{filename}", 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"⚠️  Prompt file {filename} not found, using default prompt")
        return "You are an AI agent. Please help the user with their request."