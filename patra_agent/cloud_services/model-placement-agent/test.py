import asyncio
import json
from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_URL = "http://localhost:8000/sse"

TOOL_CALLS = [
  ("list_model_ids", {}),
  ("list_all_model_cards", {}),
  ("get_fairness_metrics_all_models", {}),
  ("rank_by_fairness_metrics", {}),
  ("get_average_compute_time_all_models", {}),
  ("get_average_cpu_gpu_all_models", {}),
  ("get_average_accuracy_all_models", {}),
  ("rank_by_accuracy", {}),
  ("rank_by_compute_time", {}),
  ("rank_by_power", {}),
  ("rank_by_resources", {}),
  ("majority_vote_best_model", {}),
  ("get_recommended_model_download_url", {}),
]

async def main():
  client = MultiServerMCPClient({"patra": {"url": MCP_URL, "transport": "sse"}})
  tools = await client.get_tools()
  name_to_tool = {t.name: t for t in tools}

  for name, params in TOOL_CALLS:
    t = name_to_tool.get(name)
    if not t:
      print(f"{name}: <not found>")
      continue
    out = await t.ainvoke(params)
    try:
      parsed = json.loads(out)
      print(f"{name}: {json.dumps(parsed, indent=2)}")
    except Exception:
      print(f"{name}: {out}")

asyncio.run(main())