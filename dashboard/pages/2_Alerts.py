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
    page_title="CKN Alerts",
    page_icon="⚠️",
    layout="wide")

st.header("CKN Alerts")
st.sidebar.header("Alerts from CKN Topics")

alerts = kg.fetch_alerts()

# Filter by topic
topic_filter = st.sidebar.multiselect("Select Topic", options=alerts['Source Topic'].unique(), default=alerts['Source Topic'].unique())

# Filter by priority
priority_filter = st.sidebar.multiselect("Select Priority", options=alerts['Priority'].unique(), default=alerts['Priority'].unique())

min_date = alerts.index.min().date()
max_date = alerts.index.max().date()
# date_range = st.sidebar.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# start_date = pd.to_datetime(date_range[0])
# end_date = pd.to_datetime(date_range[1])

# Apply Filters
filtered_df = alerts[
    (alerts['Source Topic'].isin(topic_filter)) &
    (alerts['Priority'].isin(priority_filter))
    # (alerts.index >= start_date) &
    # (alerts.index <= end_date)
]

st.write(filtered_df)
