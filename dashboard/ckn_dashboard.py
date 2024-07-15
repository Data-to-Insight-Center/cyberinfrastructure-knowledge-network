import time
from ckn_kg import CKNKnowledgeGraph
import neo4j
import streamlit as st
import pandas as pd
import os
import json

CKN_KG_URI = os.getenv('CKN_KG_URI', 'bolt://localhost:7687')
CKN_KG_USER = os.getenv('CKN_KG_USER', 'neo4j')
CKN_KG_PWD = os.getenv('CKN_KG_PWD', 'neo4jpwd')

st.set_page_config(layout="wide")
st.title('CKN Analytics Dashboard')
left_pane, right_pane = st.columns([1, 1])

ckn_kg = CKNKnowledgeGraph(CKN_KG_URI, CKN_KG_USER, CKN_KG_PWD)


def load_raw_data(nrows=50):
    latest_edges = ckn_kg.fetch_latest_served_by_edges(nrows)
    df = pd.DataFrame(latest_edges)
    return df


def load_alerts(nrows=10):
    return ckn_kg.fetch_alerts(nrows)


st.session_state.data = load_raw_data()
st.session_state.alerts = load_alerts()

left_pane.subheader('Raw events')
left_pane.write(st.session_state.data)

right_pane.subheader('Latest Alerts')
right_pane.write(st.session_state.alerts)


def get_max_probability(scores):
    scores_list = json.loads(scores)
    max_prob = max(score['probability'] for score in scores_list)
    return max_prob


st.session_state.data['image_receiving_timestamp'] = st.session_state.data['image_receiving_timestamp'].apply(
    lambda x: ckn_kg.convert_to_datetime(x) if isinstance(x, neo4j.time.DateTime) else x
)

# Apply the function to get the maximum probability for each row
st.session_state.data['max_probability'] = st.session_state.data['scores'].apply(get_max_probability)

average_max_probability = st.session_state.data[st.session_state.data['image_decision'] == 'Save'][
    'max_probability'].mean()
average_max_probability = round(average_max_probability, 2) * 100

total_saved = st.session_state.data[st.session_state.data['image_decision'] == 'Save'].shape[0]
total_deleted = st.session_state.data[st.session_state.data['image_decision'] == 'Deleted'].shape[0]


def load_acc_chart(data):
    saved_events_df = data[data['image_decision'] == 'Save']
    max_probabilities_df = saved_events_df[['image_scoring_timestamp', 'max_probability']]
    max_probabilities_df.columns = ['Timestamp', 'Accuracy']
    max_probabilities_df = max_probabilities_df.dropna(subset=['Timestamp'])
    max_probabilities_df = max_probabilities_df.sort_values(by='Timestamp')
    max_probabilities_df = max_probabilities_df.reset_index(drop=True)
    return max_probabilities_df


line_chart_data = load_acc_chart(st.session_state.data)

left_pane.subheader('Metadata for loaded events:')
col1, col2, col3, col4 = left_pane.columns(4)

col1.metric("Events loaded:", st.session_state.data.shape[0])
col2.metric("Total Saved:", total_saved)
col3.metric("Average accuracy", f'{average_max_probability}%')

right_pane.subheader('Accuracy variation for cameratraps events')
right_pane.line_chart(line_chart_data, x="Timestamp", y="Accuracy", height=600)


while True:
    time.sleep(10)
    st.rerun()
