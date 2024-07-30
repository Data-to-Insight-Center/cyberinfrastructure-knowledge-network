from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
#from langchain_ollama.llms import OllamaLLM
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
import os

load_dotenv()

# get the env variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USER")
NEO4J_PWD = os.getenv("NEO4J_PWD")

# load the graph and the LLM
graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PWD)
llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini")
# llm = OllamaLLM(model="llama3.1")
top_k_results = 10
