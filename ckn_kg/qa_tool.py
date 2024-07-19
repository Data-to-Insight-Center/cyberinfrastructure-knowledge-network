from langchain.chains import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from util import graph, llm


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
