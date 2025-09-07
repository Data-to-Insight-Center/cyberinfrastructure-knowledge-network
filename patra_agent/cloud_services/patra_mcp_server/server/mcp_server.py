#!/usr/bin/env python3
"""
MCP Server for Patra Knowledge Graph
Wraps the existing Flask REST API functionality as MCP tools
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
server = Server("patra-kg")

# Configuration
PATRA_SERVER_URL = os.getenv("PATRA_SERVER_URL", "http://localhost:5002")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PWD", "password")

# HTTP client for making requests to patra-server
http_client = httpx.AsyncClient(timeout=30.0)


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools for interacting with the Patra Knowledge Graph."""
    tools = [
        Tool(
            name="search_model_cards",
            description="Search for model cards in the knowledge graph using full-text search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant model cards"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_model_card",
            description="Get detailed information about a specific model card by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "The unique identifier of the model card"
                    }
                },
                "required": ["model_id"]
            }
        ),
        Tool(
            name="list_all_model_cards",
            description="Get a list of all model cards in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="add_model_card",
            description="Add a new model card to the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_card_data": {
                        "type": "object",
                        "description": "The model card data as a JSON object"
                    }
                },
                "required": ["model_card_data"]
            }
        ),
        Tool(
            name="update_model_card",
            description="Update an existing model card in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "The unique identifier of the model card to update"
                    },
                    "model_card_data": {
                        "type": "object",
                        "description": "The updated model card data as a JSON object"
                    }
                },
                "required": ["model_id", "model_card_data"]
            }
        ),
        Tool(
            name="get_model_deployments",
            description="Get all deployments for a specific model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "The unique identifier of the model"
                    }
                },
                "required": ["model_id"]
            }
        ),
        Tool(
            name="get_model_download_url",
            description="Get the download URL for a specific model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "The unique identifier of the model"
                    }
                },
                "required": ["model_id"]
            }
        ),
        Tool(
            name="set_model_location",
            description="Set or update the location/URL for a model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "The unique identifier of the model"
                    },
                    "location": {
                        "type": "string",
                        "description": "The new location/URL for the model"
                    }
                },
                "required": ["model_id", "location"]
            }
        ),
        Tool(
            name="generate_model_id",
            description="Generate a unique model ID for a given author, name, and version",
            inputSchema={
                "type": "object",
                "properties": {
                    "author": {
                        "type": "string",
                        "description": "The author of the model"
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the model"
                    },
                    "version": {
                        "type": "string",
                        "description": "The version of the model"
                    }
                },
                "required": ["author", "name", "version"]
            }
        ),
        Tool(
            name="add_datasheet",
            description="Add a datasheet to the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "datasheet_data": {
                        "type": "object",
                        "description": "The datasheet data as a JSON object"
                    }
                },
                "required": ["datasheet_data"]
            }
        ),
        Tool(
            name="register_device",
            description="Register a new edge device for deployment tracking",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_data": {
                        "type": "object",
                        "description": "Device information including device_id and other metadata"
                    }
                },
                "required": ["device_data"]
            }
        ),
        Tool(
            name="register_user",
            description="Register a new user for experiment tracking and model submissions",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_data": {
                        "type": "object",
                        "description": "User information including user_id and other metadata"
                    }
                },
                "required": ["user_data"]
            }
        )
    ]
    
    return ListToolsResult(tools=tools)


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls to interact with the Patra Knowledge Graph."""
    try:
        if name == "search_model_cards":
            return await search_model_cards(arguments)
        elif name == "get_model_card":
            return await get_model_card(arguments)
        elif name == "list_all_model_cards":
            return await list_all_model_cards(arguments)
        elif name == "add_model_card":
            return await add_model_card(arguments)
        elif name == "update_model_card":
            return await update_model_card(arguments)
        elif name == "get_model_deployments":
            return await get_model_deployments(arguments)
        elif name == "get_model_download_url":
            return await get_model_download_url(arguments)
        elif name == "set_model_location":
            return await set_model_location(arguments)
        elif name == "generate_model_id":
            return await generate_model_id(arguments)
        elif name == "add_datasheet":
            return await add_datasheet(arguments)
        elif name == "register_device":
            return await register_device(arguments)
        elif name == "register_user":
            return await register_user(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def search_model_cards(arguments: Dict[str, Any]) -> CallToolResult:
    """Search for model cards using full-text search."""
    query = arguments.get("query", "")
    if not query:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: Query parameter is required")]
        )
    
    try:
        response = await http_client.get(
            f"{PATRA_SERVER_URL}/modelcards/search",
            params={"q": query}
        )
        response.raise_for_status()
        results = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Search results for '{query}':\n{json.dumps(results, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def get_model_card(arguments: Dict[str, Any]) -> CallToolResult:
    """Get detailed information about a specific model card."""
    model_id = arguments.get("model_id", "")
    if not model_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: model_id parameter is required")]
        )
    
    try:
        response = await http_client.get(f"{PATRA_SERVER_URL}/modelcard/{model_id}")
        response.raise_for_status()
        model_card = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Model card for {model_id}:\n{json.dumps(model_card, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def list_all_model_cards(arguments: Dict[str, Any]) -> CallToolResult:
    """Get a list of all model cards in the knowledge graph."""
    try:
        response = await http_client.get(f"{PATRA_SERVER_URL}/modelcards")
        response.raise_for_status()
        model_cards = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"All model cards:\n{json.dumps(model_cards, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def add_model_card(arguments: Dict[str, Any]) -> CallToolResult:
    """Add a new model card to the knowledge graph."""
    model_card_data = arguments.get("model_card_data", {})
    if not model_card_data:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: model_card_data parameter is required")]
        )
    
    try:
        response = await http_client.post(
            f"{PATRA_SERVER_URL}/modelcard",
            json=model_card_data
        )
        response.raise_for_status()
        result = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Model card added successfully:\n{json.dumps(result, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def update_model_card(arguments: Dict[str, Any]) -> CallToolResult:
    """Update an existing model card in the knowledge graph."""
    model_id = arguments.get("model_id", "")
    model_card_data = arguments.get("model_card_data", {})
    
    if not model_id or not model_card_data:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: model_id and model_card_data parameters are required")]
        )
    
    try:
        response = await http_client.put(
            f"{PATRA_SERVER_URL}/modelcard/{model_id}",
            json=model_card_data
        )
        response.raise_for_status()
        result = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Model card updated successfully:\n{json.dumps(result, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def get_model_deployments(arguments: Dict[str, Any]) -> CallToolResult:
    """Get all deployments for a specific model."""
    model_id = arguments.get("model_id", "")
    if not model_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: model_id parameter is required")]
        )
    
    try:
        response = await http_client.get(f"{PATRA_SERVER_URL}/modelcard/{model_id}/deployments")
        response.raise_for_status()
        deployments = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Deployments for model {model_id}:\n{json.dumps(deployments, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def get_model_download_url(arguments: Dict[str, Any]) -> CallToolResult:
    """Get the download URL for a specific model."""
    model_id = arguments.get("model_id", "")
    if not model_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: model_id parameter is required")]
        )
    
    try:
        response = await http_client.get(f"{PATRA_SERVER_URL}/modelcard/{model_id}/download_url")
        response.raise_for_status()
        result = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Download URL for model {model_id}:\n{json.dumps(result, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def set_model_location(arguments: Dict[str, Any]) -> CallToolResult:
    """Set or update the location/URL for a model."""
    model_id = arguments.get("model_id", "")
    location = arguments.get("location", "")
    
    if not model_id or not location:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: model_id and location parameters are required")]
        )
    
    # Validate URL format
    parsed_url = urlparse(location)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        return CallToolResult(
            content=[TextContent(type="text", text="Error: Location must be a valid URL")]
        )
    
    try:
        response = await http_client.put(
            f"{PATRA_SERVER_URL}/modelcard/{model_id}/location",
            json={"location": location}
        )
        response.raise_for_status()
        result = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Model location updated successfully:\n{json.dumps(result, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def generate_model_id(arguments: Dict[str, Any]) -> CallToolResult:
    """Generate a unique model ID for a given author, name, and version."""
    author = arguments.get("author", "")
    name = arguments.get("name", "")
    version = arguments.get("version", "")
    
    if not all([author, name, version]):
        return CallToolResult(
            content=[TextContent(type="text", text="Error: author, name, and version parameters are required")]
        )
    
    try:
        response = await http_client.post(
            f"{PATRA_SERVER_URL}/modelcard/id",
            json={"author": author, "name": name, "version": version}
        )
        response.raise_for_status()
        result = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Generated model ID:\n{json.dumps(result, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def add_datasheet(arguments: Dict[str, Any]) -> CallToolResult:
    """Add a datasheet to the knowledge graph."""
    datasheet_data = arguments.get("datasheet_data", {})
    if not datasheet_data:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: datasheet_data parameter is required")]
        )
    
    try:
        response = await http_client.post(
            f"{PATRA_SERVER_URL}/datasheet",
            json=datasheet_data
        )
        response.raise_for_status()
        result = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Datasheet added successfully:\n{json.dumps(result, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def register_device(arguments: Dict[str, Any]) -> CallToolResult:
    """Register a new edge device for deployment tracking."""
    device_data = arguments.get("device_data", {})
    if not device_data:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: device_data parameter is required")]
        )
    
    try:
        response = await http_client.post(
            f"{PATRA_SERVER_URL}/device",
            json=device_data
        )
        response.raise_for_status()
        result = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Device registered successfully:\n{json.dumps(result, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def register_user(arguments: Dict[str, Any]) -> CallToolResult:
    """Register a new user for experiment tracking and model submissions."""
    user_data = arguments.get("user_data", {})
    if not user_data:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: user_data parameter is required")]
        )
    
    try:
        response = await http_client.post(
            f"{PATRA_SERVER_URL}/user",
            json=user_data
        )
        response.raise_for_status()
        result = response.json()
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"User registered successfully:\n{json.dumps(result, indent=2)}"
            )]
        )
    except httpx.HTTPError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP error: {str(e)}")]
        )


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Patra Knowledge Graph MCP Server...")
    logger.info(f"Connecting to patra-server at: {PATRA_SERVER_URL}")
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="patra-kg",
                server_version="1.0.0",
                capabilities=server.get_capabilities(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
