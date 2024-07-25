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
    page_title="Camera Traps Experiments",
    page_icon="📸",
    layout="wide")

st.header("Camera Traps Experiments")
st.sidebar.header("Camera Traps Analytics")

users = kg.fetch_distinct_users()

def display_experiment_indicators(experiment_id, experiment_df):
    selected_experiment = experiment_df.loc[experiment_id]
    start_time = selected_experiment['Start Time']
    date_str = start_time.strftime("%Y-%m-%d")
    time_str = start_time.strftime("%H:%M:%S")
    average_accuracy = round(selected_experiment['Accuracy [%]'], 2)
    total_images = selected_experiment['Total Images']
    saved_images = selected_experiment['Saved Images']
    deleted_images = total_images - saved_images

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Start Date", value=date_str)
    col2.metric(label="Start Time", value=time_str)
    col3.metric(label="Average Accuracy [%]", value=average_accuracy)
    col4.metric(label="Saved / Deleted Images", value=f"{saved_images} / {deleted_images}")



# Create three columns
col1, col2= st.columns(2)

# Display DataFrames in columns
with col1:
    selected_user = st.selectbox("Select User", users)
    st.write("#")

if selected_user:
    experiments = kg.fetch_experiments(selected_user)
    with col2:
        selected_experiment = st.selectbox("Select Experiment", experiments['experiment_id'])
        st.write("#")

if selected_user:
    with col1:
        st.subheader(f"Experiment details for user: {selected_user}")
        exp_summary_user = kg.get_experiment_info_for_user(selected_user)
        st.write(exp_summary_user)

# Load user-specific data
if selected_experiment:
    with col2:
        # accuracy_trend = kg.fetch_accuracy_for_experiment(selected_experiment)
        # fig = px.line(accuracy_trend, x='Timestamp', y='Accuracy', title='Accuracy of saved images')
        # st.plotly_chart(fig)

        display_experiment_indicators(selected_experiment, exp_summary_user)

        st.subheader(f"Experiment data")
        experiment_info = kg.get_exp_info_raw(selected_experiment)
        st.write(experiment_info)
