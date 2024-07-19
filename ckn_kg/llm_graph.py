from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langgraph.graph import END, StateGraph, START
from typing import Annotated, Literal, Sequence, TypedDict
from langchain_core.pydantic_v1 import BaseModel, Field
from util import graph, llm, top_k_results

class CypherGenerator(BaseModel):
    cypher_query: str = Field(
        description="Syntactically correct cypher query ready for execution"
    )

    context: str = Field(
        description="Context about the query"
    )


sysprompt = """You are an expert in writing Cypher queries for a Neo4j database. Write Cypher queries that avoid using directional edges. Instead of using arrows (-> or <-) for relationships, use undirected relationships by using double hyphens (--) and specify the relationship type within square brackets.
Make sure that all relationships in the queries are undirected, 
using double hyphens and square brackets to specify the relationship type.
Only return the cypher query

For example, instead of:
MATCH (u:User {{user_id: 'jstubbs'}})-[:SUBMITTED_BY]->(e:Experiment)
RETURN COUNT(e) AS NumberOfExperimentsRunByJstubbs

You should write:
MATCH (u:User {{user_id: 'jstubbs'}})-[r:SUBMITTED_BY]-(e:Experiment)
RETURN COUNT(e) AS NumberOfExperimentsRunByJstubbs

Try and convert datetime when returning. 
Here's an example:
MATCH (u:User {{user_id: 'swithana'}})-[r:SUBMITTED_BY]-(e:Experiment)
RETURN e, datetime({{epochMillis: e.start_time}}) AS start_time
"""


generation_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", sysprompt),
        ("human", "Only return the cypher query for the question: \n {question} \n Schema: {schema}.",
        ),
    ]
)
cypher_gen_llm = llm.with_structured_output(CypherGenerator)
cypher_generator = generation_prompt | cypher_gen_llm

cypher_generation_check_system = """You are a grader assessing whether a given cypherql query is syntactically correct. If it has directional edges in the query, it's not syntactically correct.
     Give a binary score 'yes' or 'no'. 'Yes' the query is syntactically correct """
# Data model
class CheckCypherGeneration(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Query is syntactically correct and grounded in the given schema, 'yes' or 'no'"
    )

syntax_grader = llm.with_structured_output(CheckCypherGeneration)

syntax_grader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", cypher_generation_check_system),
        ("human", "Schema: \n\n {schema} \n\n LLM generation: {cypher_generation}"),
    ]
)

syntax_checker = syntax_grader_prompt | syntax_grader

generation_test_system = """You are a grader assessing whether a given result from a graph database aligns with the question asked. 
     Give a binary score 'yes' or 'no'. 'Yes' the result answers the question  """
# Data model
class CheckAnswerGeneration(BaseModel):
    """Binary score for generated answer."""

    binary_score: str = Field(
        description="Result answers the question, 'yes' or 'no'"
    )

answer_grader_llm = llm.with_structured_output(CheckAnswerGeneration)

answer_grader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", generation_test_system),
        ("human", "Question: \n\n {question} \n\n Graph query response: {query_response}"),
    ]
)

answer_grader = answer_grader_prompt | answer_grader_llm


answer_generator_template = """You are tasked with generating a response to the question using the context information available in query that was run on a knowledge graph. Keep the output structured if possible. Don't use bold, underline or other text altering stuff. Just plain text. 

question: 
{question}

graph query response: 
{db_response} 
 """

answer_generator_prompt = PromptTemplate(
    input_variables=["question", "db_response"], template=answer_generator_template
)

answer_generator = answer_generator_prompt | llm | StrOutputParser()

class GraphState(TypedDict):
    """
    Represents the state of the graph
    """

    question: str
    generated_answer: str
    query_response: str
    cypher_generation: str


def generate_cypher(state):
    """
    Generate or regenerate the cypher query.
    """
    print("---GENERATING CYPHER QUERY---")
    user_question = state["question"]
    cypher_generation = state["cypher_generation"]

    if cypher_generation is not None:
        user_question = user_question + " Previously generated cypher was wrong which was: " + cypher_generation

    cypher_gen_result = cypher_generator.invoke({"schema": graph.get_structured_schema, "question": user_question})
    generated_cypher = cypher_gen_result.cypher_query
    print(state)
    return {"cypher_generation": generated_cypher, "question": user_question}


def decide_retrieve(state):
    """
    Test if the cypher query is correct
    :param state:
    :return:
    """
    cypher_generation = state["cypher_generation"]
    print("---DECIDING IF CYPHER QUERY IS SYNTACTICALLY CORRECT---")
    print(state)

    score = syntax_checker.invoke({"schema": graph.get_structured_schema, "cypher_generation": cypher_generation})
    grade = score.binary_score
    print(f'Grade: {grade}')
    if grade == "yes":
        # correct query generated
        print(
            "---DECISION: GENERATED CYPHER QUERY IS SYNTACTICALLY CORRECT---"
        )
        return "retrieve_data"
    else:
        # Not correct query, regenerate
        print("---DECISION: GENERATED CYPHER QUERY IS INCORRECT---")
        print(cypher_generation)

        return "generate_cypher"


def execute_query(state):
    print("---DECISION: EXECUTING QUERY ON GRAPH ---")
    print(state)
    query = state["cypher_generation"]
    response = graph.query(query)[:top_k_results]
    query_result = str(response).replace("{", "{{").replace("}", "}}")
    return {"query_response": query_result, "cypher_generation": query}


def generate_human_response(state):
    print("---GENERATING HUMAN LIKE RESPONSE ---")

    print(state)

    user_question = state["question"]
    query_response = state["query_response"]

    generated_answer = answer_generator.invoke({"question": user_question, "db_response": query_response})
    print("GENERATED:" + generated_answer)
    return {"query_response": query_response, "question": user_question, "generated_answer": generated_answer}

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

from pprint import pprint

def run_langraph(query):
    try:
        inputs = {"question": query}
        for output in app.stream(inputs):
            for key, value in output.items():
                # Node
                pprint(f"Node '{key}':")
                # Optional: print full state at each node
                # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
            pprint("\n---\n")

        # Final generation
        return(value["generated_answer"])
    except Exception as e:
        print(e)
        return "There was an error generating the query."