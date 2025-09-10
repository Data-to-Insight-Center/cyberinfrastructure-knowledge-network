#!/usr/bin/env python3
"""
Patra Server
Combines Flask REST API with LangGraph-compatible sync tools
"""

import os
import logging
import json
import httpx
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from flask import Flask, request, jsonify, Response
from flask_restx import Api, Resource
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from reconstructor.mc_reconstructor import MCReconstructor

# Configure logging
level_name = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, level_name, logging.INFO),
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("patra_server")

# Environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USER")
NEO4J_PWD = os.getenv("NEO4J_PWD")

# Initialize components (read-only server only needs reconstructor)
mc_reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)

# Flask app setup
app = Flask(__name__)
api = Api(app, version='1.0', title='Patra API',
          description='API and LangGraph tools for Patra Knowledge Graph',
          doc='/swagger')

# =============================================================================
# LangGraph-Compatible Sync Tools
# =============================================================================

class ModelCardInput(BaseModel):
    """Input for getting a model card."""
    model_id: str = Field(description="The model card ID to retrieve")

class ModelSearchInput(BaseModel):
    """(deprecated)"""
    query: str = Field(description="Deprecated")

class ModelStatisticInput(BaseModel):
    """Input for getting model statistics."""
    model_id: str = Field(description="The model card ID")
    statistic: str = Field(description="The statistic to retrieve (e.g., 'avg_compute_time', 'mean_latency_ms')")


class GetModelCardTool(BaseTool):
    """Get detailed information about a specific model card."""
    name: str = "get_model_card"
    description: str = "Get detailed information about a specific model card by ID"
    args_schema: type = ModelCardInput

    def _run(self, model_id: str, **kwargs) -> str:
        """Get model card details."""
        try:
            model_card = mc_reconstructor.reconstruct(model_id)
            if model_card is None:
                return f"Model card '{model_id}' not found"
            return json.dumps(model_card, indent=2)
        except Exception as e:
            return f"Error retrieving model card: {str(e)}"

class ListAllModelCardsTool(BaseTool):
    """Get a list of all model cards in the knowledge graph."""
    name: str = "list_all_model_cards"
    description: str = "Get a list of all model cards in the knowledge graph"

    def _run(self, **kwargs) -> str:
        """List all model cards."""
        try:
            model_cards = mc_reconstructor.get_all_mcs()
            return json.dumps(model_cards, indent=2)
        except Exception as e:
            return f"Error listing model cards: {str(e)}"

class ListModelIdsTool(BaseTool):
    """Get a list of all model card IDs."""
    name: str = "list_model_ids"
    description: str = "Get a list of all model card IDs in the knowledge graph"

    def _run(self, **kwargs) -> str:
        """List all model IDs."""
        try:
            model_ids = mc_reconstructor.get_all_model_ids()
            return json.dumps({"model_ids": model_ids}, indent=2)
        except Exception as e:
            return f"Error listing model IDs: {str(e)}"

class SearchModelCardsTool(BaseTool):
    """(deprecated)"""
    name: str = "search_model_cards"
    description: str = "Deprecated"
    args_schema: type = ModelSearchInput

    def _run(self, query: str, **kwargs) -> str:
        return json.dumps([])

class GetModelDeploymentsTool(BaseTool):
    """Get all deployments for a specific model."""
    name: str = "get_model_deployments"
    description: str = "Get all deployments for a specific model"
    args_schema: type = ModelCardInput

    def _run(self, model_id: str, **kwargs) -> str:
        """Get model deployments."""
        try:
            deployments = mc_reconstructor.get_deployments(model_id)
            if deployments is None:
                return f"No deployments found for model '{model_id}'"
            return json.dumps(deployments, indent=2)
        except Exception as e:
            return f"Error retrieving deployments: {str(e)}"

class GetModelDownloadUrlTool(BaseTool):
    """Get the download URL for a specific model."""
    name: str = "get_model_download_url"
    description: str = "Get the download URL for a specific model"
    args_schema: type = ModelCardInput

    def _run(self, model_id: str, **kwargs) -> str:
        """Get model download URL."""
        try:
            model_info = mc_reconstructor.get_model_location(model_id)
            if model_info is None:
                return f"Model '{model_id}' not found"
            return json.dumps(model_info, indent=2)
        except Exception as e:
            return f"Error retrieving download URL: {str(e)}"

class GetAverageComputeTimeTool(BaseTool):
    """Get the average compute time for a specific model."""
    name: str = "get_average_compute_time"
    description: str = "Get the average compute time for a specific model"
    args_schema: type = ModelCardInput

    def _run(self, model_id: str, **kwargs) -> str:
        """Get average compute time."""
        try:
            avg_time = mc_reconstructor.get_average_compute_time(model_id)
            if avg_time is None:
                return f"No compute time data available for model '{model_id}'"
            return json.dumps({"model_id": model_id, "average_compute_time": avg_time}, indent=2)
        except Exception as e:
            return f"Error retrieving compute time: {str(e)}"

class GetAverageStatisticTool(BaseTool):
    """Get the average of any statistic for a specific model."""
    name: str = "get_average_statistic"
    description: str = "Get the average of any statistic for a specific model (e.g., 'avg_compute_time', 'mean_latency_ms', 'mean_accuracy')"
    args_schema: type = ModelStatisticInput

    def _run(self, model_id: str, statistic: str, **kwargs) -> str:
        """Get average statistic."""
        try:
            result = mc_reconstructor.get_average_statistic_for_model(model_id, statistic)
            if result is None:
                return f"No data available for statistic '{statistic}' on model '{model_id}'"
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error retrieving statistic: {str(e)}"


# =============================================================================
# Tool Registry
# =============================================================================

def get_langgraph_tools() -> List[BaseTool]:
    """Get all LangGraph-compatible tools."""
    return [
        GetModelCardTool(),
        ListAllModelCardsTool(),
        ListModelIdsTool(),
        SearchModelCardsTool(),
        GetModelDeploymentsTool(),
        GetModelDownloadUrlTool(),
        GetAverageComputeTimeTool(),
        GetAverageStatisticTool(),
    ]

# =============================================================================
# Flask REST API Endpoints (existing functionality)
# =============================================================================

@app.route('/')
def home():
    return "Welcome to the Patra Knowledge Graph", 200

@api.route('/modelcard/<string:mc_id>')
class ModelCardDetail(Resource):
    def get(self, mc_id):
        logger.debug(f"GET /modelcard/{mc_id}")
        model_card = mc_reconstructor.reconstruct(str(mc_id))
        if model_card is None:
            return {"error": "Model card could not be found!"}, 400
        return model_card, 200

@api.route('/modelcards/search')
class SearchModelCards(Resource):
    def get(self):
        return [], 200

@api.route('/modelcard/<string:mc_id>/download_url')
class ModelDownloadURL(Resource):
    def get(self, mc_id):
        logger.debug(f"GET /modelcard/{mc_id}/download_url")
        model = mc_reconstructor.get_model_location(str(mc_id))
        if model is None or "download_url" not in model:
            return {"error": "Model could not be found!"}, 400
        return model["download_url"], 200

@api.route('/modelcards')
class ListModelCards(Resource):
    def get(self):
        logger.debug("GET /modelcards")
        model_card_dict = mc_reconstructor.get_all_mcs()
        return model_card_dict, 200

@api.route('/modelcard/<string:mc_id>/deployments')
class ModelDeployments(Resource):
    def get(self, mc_id):
        logger.debug(f"GET /modelcard/{mc_id}/deployments")
        deployments = mc_reconstructor.get_deployment_ids(mc_id)
        if deployments is None or len(deployments) == 0:
            return {"error": "Deployments not found!"}, 400
        return deployments, 200

@api.route('/modelcard/<string:mc_id>/average_compute_time')
class AverageComputeTime(Resource):
    def get(self, mc_id):
        logger.debug(f"GET /modelcard/{mc_id}/average_compute_time")
        average_compute_time = mc_reconstructor.get_average_compute_time(mc_id)
        return average_compute_time, 200

@api.route('/modelcards/ids')
class ListModelIds(Resource):
    def get(self):
        logger.debug("GET /modelcards/ids")
        model_ids = mc_reconstructor.get_all_model_ids()
        return {"model_ids": model_ids}, 200

@api.route('/modelcard/<string:mc_id>/average/<string:statistic>')
class AverageStatisticForModel(Resource):
    def get(self, mc_id, statistic):
        logger.debug(f"GET /modelcard/{mc_id}/average/{statistic}")
        result = mc_reconstructor.get_average_statistic_for_model(mc_id, statistic)
        if result is None:
            return {"error": f"No deployments found for model '{mc_id}' with statistic '{statistic}'"}, 404
        return result, 200

@api.route('/models/average_compute_time')
class AverageComputeTimeAllModels(Resource):
    def get(self):
        logger.debug("GET /models/average_compute_time")
        results = mc_reconstructor.get_average_compute_time_all_models()
        return results, 200

@api.route('/models/average_cpu_gpu')
class AverageCpuGpuAllModels(Resource):
    def get(self):
        logger.debug("GET /models/average_cpu_gpu")
        results = mc_reconstructor.get_average_cpu_gpu_all_models()
        return results, 200

@api.route('/models/average_accuracy')
class AverageAccuracyAllModels(Resource):
    def get(self):
        logger.debug("GET /models/average_accuracy")
        results = mc_reconstructor.get_average_accuracy_all_models()
        return results, 200

# =============================================================================
# LangGraph Tools Endpoint
# =============================================================================

@api.route('/tools')
class LangGraphTools(Resource):
    def get(self):
        """Get information about available LangGraph tools."""
        tools = get_langgraph_tools()
        tool_info = []
        for tool in tools:
            tool_info.append({
                "name": tool.name,
                "description": tool.description,
                "args_schema": tool.args_schema.model_json_schema() if tool.args_schema else None
            })
        return {"tools": tool_info}, 200

# =============================================================================
# Main Application
# =============================================================================

if __name__ == '__main__':
    logger.info("Starting Patra Server...")
    logger.info(f"Neo4j URI: {NEO4J_URI}")
    logger.info(f"Available LangGraph tools: {len(get_langgraph_tools())}")
    
    # Print available tools
    for tool in get_langgraph_tools():
        logger.info(f"  - {tool.name}: {tool.description}")
    
    app.run(debug=True, host='0.0.0.0', port=5002)
