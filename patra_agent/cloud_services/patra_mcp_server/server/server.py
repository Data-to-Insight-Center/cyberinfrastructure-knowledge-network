"""FastMCP server exposing Patra Knowledge Graph tools.

Run with:
    python fast_mcp_server.py    # defaults to stdio transport

Requires the environment variables NEO4J_URI, NEO4J_USER, NEO4J_PWD.
"""
from typing import Any
import os
import json

from mcp.server.fastmcp import FastMCP
try:
    from patra_mcp_server.reconstructor.mc_reconstructor import MCReconstructor  # type: ignore
except ModuleNotFoundError:
    # Fallback when code is copied without package directory (e.g., in Docker image)
    from reconstructor.mc_reconstructor import MCReconstructor  # type: ignore

# ----------------------------------------------------------------------------
# Runtime configuration
# ----------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USER")
NEO4J_PWD = os.getenv("NEO4J_PWD")

# Instantiate reconstructor (read-only operations)
reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)

# FastMCP instance (bind to all interfaces for Docker)
mcp = FastMCP("patra", host="0.0.0.0", port=int(os.getenv("MCP_PORT", "8000")))

# ----------------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------------

def _to_json(obj: Any) -> str:
    """Pretty JSON dump."""
    return json.dumps(obj, indent=2, ensure_ascii=False)

# ----------------------------------------------------------------------------
# Tools (async for compatibility with FastMCP)
# ----------------------------------------------------------------------------

@mcp.tool()
async def list_model_ids() -> str:
    """List all model card IDs in the Patra KG."""
    ids = reconstructor.get_all_model_ids()
    return _to_json({"model_ids": ids})


@mcp.tool()
async def list_all_model_cards() -> str:
    """List all model cards (id, name, version, description)."""
    mcs = reconstructor.get_all_mcs()
    return _to_json(mcs)


@mcp.tool()
async def get_model_card(model_id: str) -> str:
    """Get a detailed model card by ID."""
    card = reconstructor.reconstruct(model_id)
    if card is None:
        return f"Model card '{model_id}' not found."
    return _to_json(card)


@mcp.tool()
async def get_model_download_url(model_id: str) -> str:
    """Get the download URL for a model."""
    loc = reconstructor.get_model_location(model_id)
    if loc is None or "download_url" not in loc:
        return f"Download URL for model '{model_id}' not found."
    return loc["download_url"]


@mcp.tool()
async def get_model_deployments(model_id: str) -> str:
    """Get deployment details for a model."""
    deployments = reconstructor.get_deployments(model_id)
    if not deployments:
        return f"No deployments found for model '{model_id}'."
    return _to_json(deployments)


@mcp.tool()
async def get_average_compute_time(model_id: str) -> str:
    """Get average compute time for a model."""
    avg = reconstructor.get_average_compute_time(model_id)
    if avg is None:
        return f"No compute-time data for model '{model_id}'."
    return _to_json({"model_id": model_id, "average_compute_time": avg})


@mcp.tool()
async def get_average_statistic(model_id: str, statistic: str) -> str:
    """Get average of any statistic for a model.

    statistic examples: avg_accuracy, avg_cpu_power, avg_gpu_power, avg_total_power, avg_delay_qoe ...
    """
    res = reconstructor.get_average_statistic_for_model(model_id, statistic)
    if res is None:
        return f"Statistic '{statistic}' unavailable for model '{model_id}'."
    return _to_json(res)


@mcp.tool()
async def get_average_compute_time_all_models() -> str:
    """Average compute-time across all models."""
    res = reconstructor.get_average_compute_time_all_models()
    return _to_json(res)


@mcp.tool()
async def get_average_cpu_gpu_all_models() -> str:
    """Average CPU/GPU power across all models."""
    res = reconstructor.get_average_cpu_gpu_all_models()
    return _to_json(res)


@mcp.tool()
async def get_average_accuracy_all_models() -> str:
    """Average accuracy across all models."""
    res = reconstructor.get_average_accuracy_all_models()
    return _to_json(res)


@mcp.tool()
async def best_model_by_accuracy() -> str:
    """Return the model_id with highest avg_accuracy (tie-break by model_id)."""
    data = reconstructor.get_average_accuracy_all_models() or []
    # Filter out nulls
    filtered = [d for d in data if d.get("avg_accuracy") is not None]
    if not filtered:
        return _to_json({"model_id": ""})
    # Sort by (-avg_accuracy, model_id)
    filtered.sort(key=lambda x: (-float(x.get("avg_accuracy", 0.0)), str(x.get("model_id", ""))))
    return _to_json({"model_id": filtered[0].get("model_id", "")})


@mcp.tool()
async def best_model_by_compute_time() -> str:
    """Return the model_id with lowest average_compute_time (tie-break by model_id)."""
    data = reconstructor.get_average_compute_time_all_models() or []
    filtered = [d for d in data if d.get("average_compute_time") is not None]
    if not filtered:
        return _to_json({"model_id": ""})
    filtered.sort(key=lambda x: (float(x.get("average_compute_time", 1e30)), str(x.get("model_id", ""))))
    return _to_json({"model_id": filtered[0].get("model_id", "")})


@mcp.tool()
async def best_model_by_power() -> str:
    """Return model_id minimizing (avg_cpu_power or INF) + (avg_gpu_power or INF) (tie-break by model_id)."""
    data = reconstructor.get_average_cpu_gpu_all_models() or []
    scored = []
    INF = 1e30
    for d in data:
        cpu = d.get("avg_cpu_power")
        gpu = d.get("avg_gpu_power")
        if cpu is None and gpu is None:
            continue
        score = (float(cpu) if cpu is not None else INF) + (float(gpu) if gpu is not None else INF)
        scored.append((score, str(d.get("model_id", ""))))
    if not scored:
        return _to_json({"model_id": ""})
    scored.sort(key=lambda x: (x[0], x[1]))
    return _to_json({"model_id": scored[0][1]})


@mcp.tool()
async def majority_vote_best_model() -> str:
    """Return the best model_id by majority vote across accuracy, compute-time, and power.

    Tie-break preference: accuracy > compute-time > power.
    """
    # Get winners from the three criteria
    try:
        import json as _json
        acc = _json.loads(await best_model_by_accuracy())
        lat = _json.loads(await best_model_by_compute_time())
        pwr = _json.loads(await best_model_by_power())
        candidates = [acc.get("model_id", ""), lat.get("model_id", ""), pwr.get("model_id", "")]
        # Count votes
        counts = {}
        for c in candidates:
            if not c:
                continue
            counts[c] = counts.get(c, 0) + 1
        if not counts:
            return _to_json({"model_id": ""})
        # Majority if any
        best = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
        # If no strict majority, apply priority order
        if list(counts.values()).count(counts[best]) > 1:
            # Priority: accuracy, then compute-time, then power
            for preferred in [acc.get("model_id", ""), lat.get("model_id", ""), pwr.get("model_id", "")]:
                if preferred and preferred in counts and counts[preferred] == counts[best]:
                    best = preferred
                    break
        return _to_json({"model_id": best})
    except Exception:
        return _to_json({"model_id": ""})


@mcp.tool()
async def get_recommended_model_download_url() -> str:
    """Return the download URL for the recommended model (majority vote). Returns empty string if unavailable."""
    import json as _json
    voted = await majority_vote_best_model()
    try:
        model_id = _json.loads(voted).get("model_id", "")
    except Exception:
        model_id = ""
    if not model_id:
        return ""
    url = await get_model_download_url(model_id)  # returns raw string or error string
    # If an error message came back instead of a URL, normalize to empty
    if isinstance(url, str) and url.startswith("http"):
        return url
    return ""


# ----------------------------------------------------------------------------
# Entry-point
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "sse")   # default ⇒ SSE

    if transport == "stdio":
        mcp.run(transport="stdio")                  # dev / interactive
    else:                                           # “sse”
        os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
        os.environ.setdefault("FASTMCP_PORT", "5002")   # will listen here
        mcp.run(transport="sse")