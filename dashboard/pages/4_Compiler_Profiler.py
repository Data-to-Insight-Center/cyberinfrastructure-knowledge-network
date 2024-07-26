from ckn_kg import CKNKnowledgeGraph
import pandas as pd
import os
import streamlit as st
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PWD = os.getenv('NEO4J_PWD', 'neo4jpwd')

kg = CKNKnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PWD)

st.set_page_config(
    page_title="Compiler profiling application",
    page_icon="📸",
    layout="wide")

st.header("Compiler profiling application")
st.sidebar.header("Compiler profiling application")

application = kg.fetch_distinct_compiler_applications()

# Create three columns
col1, col2 = st.columns(2)

# Display DataFrames in columns
with col1:
    selected_application = st.selectbox("Select application", application)
    st.write("#")

if selected_application:
    profile_runs = kg.fetch_profile_runs(selected_application)
    with col2:
        selected_profile_run = st.selectbox("Select Profile Run", profile_runs['profile_run'])
        st.write("#")

# Load user-specific data
if selected_profile_run:
    st.subheader(f"Profiler data")
    profile_info = kg.fetch_profile_run_info(selected_profile_run)
    st.write(profile_info)
