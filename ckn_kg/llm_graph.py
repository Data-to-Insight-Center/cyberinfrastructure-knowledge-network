from langgraph.graph import END, StateGraph, START
from typing import Annotated, Literal, Sequence, TypedDict
import os
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from llm_nodes import generate_cypher, execute_query, generate_human_response
load_dotenv()

class GraphState(TypedDict):
    """
    Represents the state of the graph
    """

    question: str
    generated_answer: str
    query_response: str
    cypher_generation: str


workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("generate_cypher", generate_cypher)  # retrieve
workflow.add_node("execute_query", execute_query)  # grade documents
workflow.add_node("gen_human_response", generate_human_response)  # grade documents
# workflow.add_node("test_cypher_query", decide_retrieve)  # grade documents
# workflow.add_node("generate", generate)  # generatae
# workflow.add_node("transform_query", transform_query)  # transform_query

# Build graph
workflow.add_edge(START, "generate_cypher")
workflow.add_edge("generate_cypher", "execute_query")
workflow.add_edge("execute_query", "gen_human_response")
workflow.add_edge("gen_human_response", END)
# workflow.add_conditional_edges(
#     "generate_cypher",
#     decide_retrieve,
#     {
#         "retrieve_data": "execute_query",
#         "generate": "generate_cypher",
#     },
# )

# Compile
app = workflow.compile()

def execute_llm_graph(query):
    for output in app.stream(query):
        for key, value in output.items():
            print(f"Node '{key}':")
        print("\n---\n")

    # Final generation
    return(value["generated_answer"])

