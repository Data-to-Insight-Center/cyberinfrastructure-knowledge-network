from ckn_kg import CKNKnowledgeGraph
from modelcards.mc_reconstructor import MCReconstructor
import pandas as pd
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PWD = os.getenv('NEO4J_PWD', 'neo4jpwd')

kg = CKNKnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PWD)
mc_util = MCReconstructor(kg)

st.set_page_config(
    page_title="Model Cards",
    page_icon="🪙",
    layout="wide")

st.header("Model Cards")
st.sidebar.header("Model Cards Access")

model_card_ids = kg.get_model_card_ids()
selected_model_card = st.selectbox("Select Model Card", model_card_ids)

if selected_model_card:
    result = mc_util.reconstruct(selected_model_card)
    st.json(result)
