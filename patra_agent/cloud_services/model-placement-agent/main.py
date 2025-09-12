import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore
from langgraph.prebuilt import create_react_agent  # type: ignore
from langchain_ollama import ChatOllama  # type: ignore
from utils import (
    _read_text,
    _extract_last_content,
    _print_last_url_or_content,
)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
PATRA_MCP_URL = os.getenv("PATRA_MCP_URL", "http://localhost:8000/sse")

SERVERS_CFG = {
    "patra": {
        "url": PATRA_MCP_URL,
        "transport": "sse",
    },
}

REACT_GUIDE = (
    "\n\n"
    "Follow this exact ReAct format to use tools:\n"
    "Action: <tool_name>\n"
    "Action Input: <JSON arguments or {}>\n"
    "Observation: <paste the tool output>\n"
    "(Repeat Action/Observation as needed)\n"
    "Final Answer: <only the final output as required by the prompt>\n"
    "- Do NOT add extra wording or explanation in Final Answer.\n"
    "- If the output is a URL, Final Answer must be ONLY the raw URL string.\n"
    "Use ONLY these tools: list_model_ids, get_model_card, get_model_download_url,\n"
    "get_average_accuracy_all_models, get_average_compute_time_all_models,\n"
    "get_average_cpu_gpu_all_models, get_average_statistic.\n"
)

# -----------------------------------------------------------------------------
"""
Helper functions moved to utils.py
"""


# -----------------------------------------------------------------------------
# Agent building
# -----------------------------------------------------------------------------
async def build_agents():
    client = MultiServerMCPClient(SERVERS_CFG)
    tools = await client.get_tools()

    llm_model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b-instruct")
    llm_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "1024"))
    num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "96"))
    num_thread = int(os.getenv("OLLAMA_NUM_THREAD", str(max(1, (os.cpu_count() or 4) // 2))))

    llm = ChatOllama(
        model=llm_model,
        base_url=llm_base,
        num_ctx=num_ctx,
        num_predict=num_predict,
        temperature=0.2,
        num_thread=num_thread,
    )

    here = os.path.dirname(__file__)
    prompt_dir = os.path.normpath(os.path.join(here, "prompts"))
    p1 = _read_text(os.path.join(prompt_dir, "agent_1.txt")) + REACT_GUIDE
    p2 = _read_text(os.path.join(prompt_dir, "agent_2.txt")) + REACT_GUIDE
    p3 = _read_text(os.path.join(prompt_dir, "agent_3.txt")) + REACT_GUIDE
    porch = _read_text(os.path.join(prompt_dir, "orchestrator.txt")) + REACT_GUIDE

    accuracy_agent = create_react_agent(model=llm, tools=tools, prompt=p1, name="accuracy_agent")
    compute_agent = create_react_agent(model=llm, tools=tools, prompt=p2, name="compute_agent")
    power_agent = create_react_agent(model=llm, tools=tools, prompt=p3, name="power_agent")
    orchestrator = create_react_agent(model=llm, tools=tools, prompt=porch, name="orchestrator")

    return accuracy_agent, compute_agent, power_agent, orchestrator


async def main():
    accuracy_agent, compute_agent, power_agent, orchestrator = await build_agents()

    acc_resp = await accuracy_agent.ainvoke({
        "messages": [
            {"role": "user", "content": "Run your selection and output per your specified format only."}
        ]
    })
    print("\n[accuracy_agent]")
    print(_extract_last_content(acc_resp))

    cmp_resp = await compute_agent.ainvoke({
        "messages": [
            {"role": "user", "content": "Run your selection and output per your specified format only."}
        ]
    })
    print("\n[compute_agent]")
    print(_extract_last_content(cmp_resp))

    pwr_resp = await power_agent.ainvoke({
        "messages": [
            {"role": "user", "content": "Run your selection and output per your specified format only."}
        ]
    })
    print("\n[power_agent]")
    print(_extract_last_content(pwr_resp))

    orch_resp = await orchestrator.ainvoke({
        "messages": [
            {"role": "user", "content": "Return only the download URL for the best model."}
        ]
    })
    print("\n[orchestrator]")
    _print_last_url_or_content(orch_resp)


if __name__ == "__main__":
    asyncio.run(main())
