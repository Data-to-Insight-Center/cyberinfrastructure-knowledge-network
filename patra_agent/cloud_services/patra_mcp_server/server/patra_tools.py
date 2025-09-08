#!/usr/bin/env python3
"""
Patra Tools Client
Easy-to-use client for accessing Patra Knowledge Graph tools in LangGraph applications
"""

import os
import logging
from typing import List, Optional
from langchain_core.tools import BaseTool

# Import the tools from server
from server import get_langgraph_tools

logger = logging.getLogger(__name__)

class PatraToolsClient:
    """Client for accessing Patra Knowledge Graph tools."""
    
    def __init__(self, neo4j_uri: Optional[str] = None, neo4j_user: Optional[str] = None, 
                 neo4j_password: Optional[str] = None, enable_similarity: bool = False):
        """
        Initialize the Patra Tools Client.
        
        Args:
            neo4j_uri: Neo4j database URI (defaults to environment variable)
            neo4j_user: Neo4j username (defaults to environment variable)
            neo4j_password: Neo4j password (defaults to environment variable)
            enable_similarity: Enable model similarity features
        """
        # Set environment variables if provided
        if neo4j_uri:
            os.environ["NEO4J_URI"] = neo4j_uri
        if neo4j_user:
            os.environ["NEO4J_USER"] = neo4j_user
        if neo4j_password:
            os.environ["NEO4J_PWD"] = neo4j_password
        if enable_similarity:
            os.environ["ENABLE_MC_SIMILARITY"] = "True"
    
    def get_tools(self) -> List[BaseTool]:
        """
        Get all available LangGraph-compatible tools.
        
        Returns:
            List of BaseTool objects that can be used with LangGraph
        """
        try:
            tools = get_langgraph_tools()
            logger.info(f"Retrieved {len(tools)} Patra tools")
            return tools
        except Exception as e:
            logger.error(f"Error retrieving Patra tools: {e}")
            return []
    
    def get_tool_names(self) -> List[str]:
        """
        Get the names of all available tools.
        
        Returns:
            List of tool names
        """
        tools = self.get_tools()
        return [tool.name for tool in tools]
    
    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """
        Get a specific tool by name.
        
        Args:
            name: The name of the tool to retrieve
            
        Returns:
            The tool if found, None otherwise
        """
        tools = self.get_tools()
        for tool in tools:
            if tool.name == name:
                return tool
        return None

# Convenience function for easy import
def get_patra_tools(neo4j_uri: Optional[str] = None, neo4j_user: Optional[str] = None, 
                   neo4j_password: Optional[str] = None, enable_similarity: bool = False) -> List[BaseTool]:
    """
    Convenience function to get Patra tools.
    
    Args:
        neo4j_uri: Neo4j database URI (defaults to environment variable)
        neo4j_user: Neo4j username (defaults to environment variable)
        neo4j_password: Neo4j password (defaults to environment variable)
        enable_similarity: Enable model similarity features
        
    Returns:
        List of BaseTool objects that can be used with LangGraph
    """
    client = PatraToolsClient(neo4j_uri, neo4j_user, neo4j_password, enable_similarity)
    return client.get_tools()

# Example usage
if __name__ == "__main__":
    # Example of how to use the tools
    print("Patra Tools Client Example")
    print("=" * 40)
    
    # Get all tools
    tools = get_patra_tools()
    
    print(f"Available tools ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Example of using a specific tool
    if tools:
        list_tool = tools[0]  # Get the first tool
        print(f"\nExample usage of {list_tool.name}:")
        print(f"Description: {list_tool.description}")
        
        # You would typically use this in a LangGraph agent like:
        # agent = create_react_agent(model=llm, tools=tools)
