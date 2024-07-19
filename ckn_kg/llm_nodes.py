from dotenv import load_dotenv
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
import os

from langchain_core.pydantic_v1 import BaseModel, Field

load_dotenv()

# get the env variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USER")
NEO4J_PWD = os.getenv("NEO4J_PWD")

# load the graph and the LLM
graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PWD)
llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini")
top_k_results = 10

cypher_prompt = """You are an expert in writing Cypher queries for a Neo4j database. Write Cypher queries that avoid using directional edges. Instead of using arrows (-> or <-) for relationships, use undirected relationships by using double hyphens (--) and specify the relationship type within square brackets.
Make sure that all relationships in the queries are undirected, 
using double hyphens and square brackets to specify the relationship type.

For example, instead of:
MATCH (u:User {{user_id: 'jstubbs'}})-[:SUBMITTED_BY]->(e:Experiment)
RETURN COUNT(e) AS NumberOfExperimentsRunByJstubbs

You should write:
MATCH (u:User {{user_id: 'jstubbs'}})-[r:SUBMITTED_BY]-(e:Experiment)
RETURN COUNT(e) AS NumberOfExperimentsRunByJstubbs

Only return the cypherql query for
question: {question}

Schema: {schema}
"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=cypher_prompt
)

neo4jQA = GraphCypherQAChain.from_llm(
    llm=llm,
    # cypher_llm=codellama13b,
    # qa_llm=codellama13b,
    graph=graph,
    verbose=False,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    # qa_prompt=QA_GEN_TEMPLATE,
    validate_cypher=True,
)
def execute_graphQA(query):
    return neo4jQA.run(query)

def get_cypher_generator():
    sysprompt = """You are an expert in writing Cypher queries for a Neo4j database. Write Cypher queries that avoid using directional edges. Instead of using arrows (-> or <-) for relationships, use undirected relationships by using double hyphens (--) and specify the relationship type within square brackets.
Make sure that all relationships in the queries are undirected, 
using double hyphens and square brackets to specify the relationship type.

For example, instead of:
MATCH (u:User {{user_id: 'jstubbs'}})-[:SUBMITTED_BY]->(e:Experiment)
RETURN COUNT(e) AS NumberOfExperimentsRunByJstubbs

You should write:
MATCH (u:User {{user_id: 'jstubbs'}})-[r:SUBMITTED_BY]-(e:Experiment)
RETURN COUNT(e) AS NumberOfExperimentsRunByJstubbs

"""
    generation_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", sysprompt),
            ("human", "only return the cypher query for the question: \n {question} \n Schema: {schema}.",
             ),
        ]
    )
    cypher_generator = generation_prompt | llm | StrOutputParser()

    return cypher_generator

cypher_generator = get_cypher_generator()
def generate_cypher(state):
    """
    Generate or regenerate the cypher query.
    """
    print("---GENERATING CYPHER QUERY---")
    user_question = state["question"]
    cypher_generation = state["cypher_generation"]

    if cypher_generation is not None:
        user_question = user_question + " Previously generated cypher was wrong which was: " + cypher_generation

    generated_cypher = cypher_generator.invoke({"schema": graph.get_structured_schema, "question": user_question})
    return {"cypher_generation": generated_cypher, "question": user_question}


def get_syntax_validator():
    cypher_generation_check_system = """You are a grader assessing whether a given cypherql query is syntactically correct. If it has directional edges in the query, it's not syntactically correct.
     Give a binary score 'yes' or 'no'. 'Yes' the query is syntactically correct """

    # Data model
    class CheckCypherGeneration(BaseModel):
        """Check for correct cypher generation"""

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
    return syntax_checker

syntax_checker = get_syntax_validator()
def decide_retrieve(state):
    """
    Test if the cypher query is correct
    :param state:
    :return:
    """
    cypher_generation = state["cypher_generation"]
    print("---DECIDING IF CYPHER QUERY IS SYNTACTICALLY CORRECT---")

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
    query = state["cypher_generation"]
    response = graph.query(query)[:top_k_results]
    query_result = str(response).replace("{", "{{").replace("}", "}}")
    return {"query_response": query_result, "cypher_generation": query}

def generate_answer():
    answer_generator_template = """You are tasked with generating a response to the question using the context information available in query that was run on a knowledge graph. Keep the output structured if possible.

question: 
{question}

graph query response: 
{db_response} 
 """
    answer_generator_prompt = PromptTemplate(
        input_variables=["question", "db_response"], template=answer_generator_template
    )
    answer_generator = answer_generator_prompt | llm | StrOutputParser()
    return answer_generator

answer_generator = generate_answer()

def generate_human_response(state):
    print("---GENERATING HUMAN LIKE RESPONSE ---")

    print(state)

    user_question = state["question"]
    query_response = state["query_response"]

    generated_answer = answer_generator.invoke({"question": user_question, "db_response": query_response})
    print("GENERATED:" + generated_answer)
    return {"query_response": query_response, "question": user_question, "generated_answer": generated_answer}