import os

import streamlit as st
from dotenv import load_dotenv
from modelcards.mc_reconstructor import MCReconstructor
from modelcards.patra_kg_server import search_kg, retrieve_mc

from ckn_kg import CKNKnowledgeGraph

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PWD = os.getenv('NEO4J_PWD', 'neo4jpwd')
PATRA_SERVER = os.getenv('PATRA_SERVER', 'localhost:5000')

kg = CKNKnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PWD)

# todo: remove mc reconstructor once Patra Server is up
mc_util = MCReconstructor(kg)

st.set_page_config(
    page_title="Model Cards",
    page_icon="🪙",
    layout="wide")

st.header("Model Cards")
st.sidebar.header("Model Cards Access")

text_search = st.text_input("Search Model Cards", value="")

model_card_ids = kg.get_model_card_ids()

if text_search:
    if text_search != "":
        model_card_ids = search_kg(text_search, PATRA_SERVER)

selected_model_card = st.selectbox("Select Model Card", model_card_ids)

if selected_model_card:
    result = retrieve_mc(selected_model_card, PATRA_SERVER)
    st.json(result)
