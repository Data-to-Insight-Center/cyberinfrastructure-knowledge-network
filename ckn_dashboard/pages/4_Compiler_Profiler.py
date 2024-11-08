import os
import streamlit as st
from dotenv import load_dotenv
from ckn_kg import CKNKnowledgeGraph

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PWD = os.getenv('NEO4J_PWD', 'neo4jpwd')

kg = CKNKnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PWD)

st.set_page_config(
    page_title="Compiler profiling application",
    page_icon="📸",
    layout="wide"
)

st.header("Compiler profiling application")

try:
    application = kg.fetch_distinct_compiler_applications()

    # Check if there are applications to display
    if not application:
        st.write("Knowledge Graph is empty.")
    else:
        # Create two columns
        col1, col2 = st.columns(2)

        with col1:
            selected_application = st.selectbox("Select application", application)

        if selected_application:
            profile_runs = kg.fetch_profile_runs(selected_application)
            if not profile_runs.empty:
                with col2:
                    selected_profile_run = st.selectbox("Select Profile Run", profile_runs['profile_run'])

                # Display profile data if a profile run is selected
                if selected_profile_run:
                    st.subheader("Profiler data")
                    profile_info = kg.fetch_profile_run_info(selected_profile_run)
                    st.write(profile_info)
            else:
                st.write("No profile runs available for the selected application.")
except Exception as e:
    st.write("Knowledge Graph is empty")
