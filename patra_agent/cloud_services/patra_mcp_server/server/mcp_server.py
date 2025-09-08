#!/usr/bin/env python3
"""
Patra MCP Server
Model Context Protocol server for Patra Knowledge Graph tools
"""

import os
import json
import logging
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP
from reconstructor.mc_reconstructor import MCReconstructor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USER")
NEO4J_PWD = os.getenv("NEO4J_PWD")

# Initialize MCP server
mcp = FastMCP("Patra Knowledge Graph")

# Initialize reconstructor
mc_reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)


@mcp.tool()
async def list_all_model_cards() -> str:
    """Get a list of all model cards in the knowledge graph"""
    try:
        model_cards = mc_reconstructor.get_all_mcs()
        return json.dumps(model_cards, indent=2)
    except Exception as e:
        return f"Error retrieving model cards: {str(e)}"


@mcp.tool()
async def get_model_card(model_id: str) -> str:
    """Get detailed information about a specific model card by ID"""
    try:
        model_card = mc_reconstructor.reconstruct(model_id)
        if model_card is None:
            return f"Model card '{model_id}' not found"
        return json.dumps(model_card, indent=2)
    except Exception as e:
        return f"Error retrieving model card: {str(e)}"


@mcp.tool()
async def list_model_ids() -> str:
    """Get a list of all model card IDs in the knowledge graph"""
    try:
        model_ids = mc_reconstructor.get_all_model_ids()
        return json.dumps({"model_ids": model_ids}, indent=2)
    except Exception as e:
        return f"Error listing model IDs: {str(e)}"


@mcp.tool()
async def search_model_cards(query: str) -> str:
    """Search for model cards using full-text search"""
    try:
        results = mc_reconstructor.search_kg(query)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching model cards: {str(e)}"


@mcp.tool()
async def get_model_deployments(model_id: str) -> str:
    """Get all deployments for a specific model"""
    try:
        deployments = mc_reconstructor.get_deployments(model_id)
        if deployments is None:
            return f"No deployments found for model '{model_id}'"
        return json.dumps(deployments, indent=2)
    except Exception as e:
        return f"Error retrieving deployments: {str(e)}"


@mcp.tool()
async def get_model_download_url(model_id: str) -> str:
    """Get the download URL for a specific model"""
    try:
        model_info = mc_reconstructor.get_model_location(model_id)
        if model_info is None:
            return f"Model '{model_id}' not found"
        return json.dumps(model_info, indent=2)
    except Exception as e:
        return f"Error retrieving download URL: {str(e)}"


@mcp.tool()
async def get_average_compute_time(model_id: str) -> str:
    """Get the average compute time for a specific model"""
    try:
        avg_time = mc_reconstructor.get_average_compute_time(model_id)
        if avg_time is None:
            return f"No compute time data available for model '{model_id}'"
        return json.dumps({"model_id": model_id, "average_compute_time": avg_time}, indent=2)
    except Exception as e:
        return f"Error retrieving compute time: {str(e)}"


@mcp.tool()
async def get_average_statistic(model_id: str, statistic: str) -> str:
    """Get the average of any statistic for a specific model (e.g., 'avg_compute_time', 'mean_latency_ms', 'mean_accuracy')"""
    try:
        result = mc_reconstructor.get_average_statistic_for_model(model_id, statistic)
        if result is None:
            return f"No data available for statistic '{statistic}' on model '{model_id}'"
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving statistic: {str(e)}"


if __name__ == "__main__":
    logger.info("Starting Patra MCP Server...")
    logger.info(f"Neo4j URI: {NEO4J_URI}")
    
    # Use default FastMCP run method - it will run on 127.0.0.1:8000
    # We'll configure the client to connect to the correct port mapping
    mcp.run(transport="streamable-http")
