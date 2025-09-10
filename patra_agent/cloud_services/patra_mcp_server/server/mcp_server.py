from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ────────────────── Logging Configuration ──────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("patra_mcp_server")

# ────────────────── FastMCP Instance ──────────────────
mcp = FastMCP("patra")

# ────────────────── Constants ──────────────────
PATRA_SERVER_URL = os.getenv(
    "PATRA_SERVER_URL", os.getenv("PATRA_SERVER_BASE_URL", "http://patra-server:5002")
).rstrip("/")
DEFAULT_TIMEOUT = 30.0
USER_AGENT = "patra-mcp-server/1.0"

# ────────────────── Helper Functions ──────────────────
async def _http_get(path: str, params: Optional[Dict[str, Any]] = None) -> Optional[dict]:
    """Perform GET request to Patra REST API and return JSON or None."""
    url = f"{PATRA_SERVER_URL}{path}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("HTTP GET failed %s – %s", url, exc)
            return None

def _err_or_empty(data: Optional[dict], empty_msg: str) -> Optional[str]:
    """Return error string if data is None/empty, else None."""
    if data is None:
        return "Error retrieving data from Patra server."
    if not data:
        return empty_msg
    return None

# ────────────────── Tool Definitions ──────────────────
@mcp.tool()
async def list_all_model_cards() -> str:
    """List all model cards in Patra Knowledge Graph."""
    data = await _http_get("/modelcards")
    err = _err_or_empty(data, "No model cards available.")
    return err or httpx.dumps(data, indent=2)


@mcp.tool()
async def get_model_card(model_id: str) -> str:
    """Get detailed model card by ID."""
    data = await _http_get(f"/modelcard/{model_id}")
    err = _err_or_empty(data, f"Model card {model_id} not found.")
    return err or httpx.dumps(data, indent=2)


@mcp.tool()
async def list_model_ids() -> str:
    """Return JSON list of model_id strings."""
    data = await _http_get("/modelcards/ids")
    err = _err_or_empty(data, "No model IDs available.")
    return err or httpx.dumps(data, indent=2)


@mcp.tool()
async def get_model_download_url(model_id: str) -> str:
    """Return raw download URL for the specified model ID."""
    url = f"{PATRA_SERVER_URL}/modelcard/{model_id}/download_url"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            return resp.text.strip()
        except Exception as exc:
            logger.warning("Download URL fetch failed %s – %s", url, exc)
            return f"Error fetching download URL for {model_id}."


@mcp.tool()
async def get_average_accuracy_all_models() -> str:
    """Return average accuracy for all models."""
    data = await _http_get("/models/average_accuracy")
    err = _err_or_empty(data, "Accuracy statistics unavailable.")
    return err or httpx.dumps(data, indent=2)


@mcp.tool()
async def get_average_compute_time_all_models() -> str:
    """Return average compute time for all models."""
    data = await _http_get("/models/average_compute_time")
    err = _err_or_empty(data, "Compute-time statistics unavailable.")
    return err or httpx.dumps(data, indent=2)


@mcp.tool()
async def get_average_cpu_gpu_all_models() -> str:
    """Return average combined CPU+GPU power for all models."""
    data = await _http_get("/models/average_cpu_gpu")
    err = _err_or_empty(data, "CPU/GPU statistics unavailable.")
    return err or httpx.dumps(data, indent=2)

# ────────────────── Entry Point ──────────────────
if __name__ == "__main__":
    logger.info("Starting Patra MCP Server – Patra API at %s", PATRA_SERVER_URL)
    # Run with HTTP transport so other services can connect via http://patra-mcp-server:8000/mcp
    mcp.run(transport="stdio")
