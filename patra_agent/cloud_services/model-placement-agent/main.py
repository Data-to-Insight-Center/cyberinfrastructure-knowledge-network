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
REACT_GUIDE = (
    "\n\n"
    "Follow this exact ReAct format to use tools:\n"
    "Action: <tool_name>\n"
    "Action Input: <JSON arguments or {}>\n"
    "Observation: <paste the tool output>\n"
    "(Repeat Action/Observation as needed)\n"
    "Final Answer: <only the final output as required by the prompt>\n"
    "- Do NOT add extra wording or explanation in Final Answer.\n"
    "Use ONLY these tools: list_model_ids, get_model_card, get_model_download_url,\n"
    "get_average_accuracy_all_models, get_average_compute_time_all_models,\n"
    "get_average_cpu_gpu_all_models, get_average_statistic, rank_by_accuracy,\n"
    "rank_by_compute_time, rank_by_power, rank_by_resources,\n"
    "rank_by_fairness_metrics, rank_by_dp_diff, rank_by_eo_diff.\n"
)

async def build_agents():
    client = MultiServerMCPClient({
        "patra": {
            "url": os.getenv("PATRA_MCP_URL", "http://localhost:8000/sse"),
            "transport": "sse",
        },
    })
    tools = await client.get_tools()

    llm_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
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

    resources_agent = create_react_agent(model=llm, tools=tools, prompt=p1, name="resources_agent")
    performance_agent = create_react_agent(model=llm, tools=tools, prompt=p2, name="performance_agent")
    accountability_agent = create_react_agent(model=llm, tools=tools, prompt=p3, name="accountability_agent")
    orchestrator = create_react_agent(model=llm, tools=tools, prompt=porch, name="orchestrator")

    return resources_agent, performance_agent, accountability_agent, orchestrator


async def main():
    resources_agent, performance_agent, accountability_agent, orchestrator = await build_agents()

    res_resp = await resources_agent.ainvoke({
        "messages": [
            {"role": "user", "content": "Run your selection and output per your specified format only."}
        ]
    })
    print("\n[resources_agent]")
    import pprint
    pprint.pprint(res_resp)
    # print(_extract_last_content(res_resp))

    perf_resp = await performance_agent.ainvoke({
        "messages": [
            {"role": "user", "content": "Run your selection and output per your specified format only."}
        ]
    })
    print("\n[performance_agent]")
    pprint.pprint(perf_resp)
    # print(_extract_last_content(perf_resp))

    acct_resp = await accountability_agent.ainvoke({
        "messages": [
            {"role": "user", "content": "Run your selection and output per your specified format only."}
        ]
    })
    print("\n[accountability_agent]")
    pprint.pprint(acct_resp)
    # print(_extract_last_content(acct_resp))

    orch_resp = await orchestrator.ainvoke({
        "messages": [
            {"role": "user", "content": "Return only the final model_id for the best model."}
        ]
    })
    print("\n[orchestrator]")
    # Orchestrator is asked to output only model_id; print directly
    pprint.pprint(orch_resp)
    # print(_extract_last_content(orch_resp))


if __name__ == "__main__":
    asyncio.run(main())
