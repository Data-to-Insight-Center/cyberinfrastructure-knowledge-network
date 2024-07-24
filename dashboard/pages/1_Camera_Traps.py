from ckn_kg import CKNKnowledgeGraph
import pandas as pd
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PWD = os.getenv('NEO4J_PWD', 'neo4jpwd')

kg = CKNKnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PWD)

st.set_page_config(
    page_title="Camera Traps Experiments",
    page_icon="📸",
    layout="wide")

st.header("Camera Traps Experiments")
st.sidebar.header("Camera Traps Analytics")

users = kg.fetch_distinct_users()

# Create three columns
col1, col2= st.columns(2)

# Display DataFrames in columns
with col1:
    selected_user = st.selectbox("Select User", users)

if selected_user:
    experiments = kg.fetch_experiments(selected_user)
    with col2:
        selected_experiment = st.selectbox("Select Experiment", experiments['experiment_id'])

if selected_user:
    with col1:
        st.subheader(f"Experiment detais for user: {selected_user}")
        exp_summary_user = kg.get_experiment_info_for_user(selected_user)
        st.write(exp_summary_user)

# Load user-specific data
if selected_experiment:
    with col2:
        st.subheader(f"Experiment data")
        experiment_info = kg.get_exp_info_raw(selected_experiment)
        st.write(experiment_info)
