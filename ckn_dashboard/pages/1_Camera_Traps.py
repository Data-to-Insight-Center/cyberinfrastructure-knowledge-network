import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ckn_kg import CKNKnowledgeGraph

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PWD = os.getenv('NEO4J_PWD', 'neo4jpwd')

kg = CKNKnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PWD)

st.set_page_config(
    page_title="Camera Traps Experiments",
    page_icon="📸",
    layout="wide")
st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 20px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.header("Camera Traps Experiments")
st.sidebar.header("Camera Traps Analytics")

users = kg.fetch_distinct_users()

def get_experiment_indicators(experiment_id, experiment_df, model_id):
    selected_experiment = experiment_df.loc[experiment_id]
    start_time = selected_experiment['Start Time']
    date_str = start_time.strftime("%Y-%m-%d")
    time_str = start_time.strftime("%H:%M:%S")

    average_accuracy = selected_experiment['Accuracy [%]']

    if average_accuracy is None:
        average_accuracy = 'N/A'
    else:
        average_accuracy = round(average_accuracy, 2)

    model_name = kg.get_mode_name_version(model_id)
    if model_name is None:
        model_name = "BioCLIP:1.0"

    # get device information
    device_info = kg.get_device_type(experiment_id)

    return date_str, time_str, model_name, device_info, average_accuracy

def get_power_info(deployment_info):
    """
    Retrieve and show power information for a given experiment.
    :param deployment_info:
    :return:
    """
    if deployment_info is None:
        return None, None, None, None, None
    else:
        total_cpu = round(deployment_info['total_cpu_power_consumption'][0], 3)
        total_gpu = round(deployment_info['total_gpu_power_consumption'][0], 3)
        end_timestamp = str(deployment_info['End Time'][0].strftime('%Y-%m-%d %H:%M:%S'))
        end_date, end_time = end_timestamp.split(' ')

        # Showing the plugin information separately
        plugin_metrics = deployment_info.drop(
            columns=["Experiment", "start_time", "end_time", "deployment_id", "Start Time", "End Time",
                     "total_cpu_power_consumption", "total_gpu_power_consumption"])

        plugins = []
        for column in plugin_metrics.columns:
            if "cpu_power_consumption" in column or "gpu_power_consumption" in column:
                plugin_name = column.split('_plugin_')[0].replace('_', ' ').capitalize()
                if "cpu_power_consumption" in column:
                    cpu_power = plugin_metrics[column][0]
                    gpu_power = plugin_metrics[column.replace('cpu_power_consumption', 'gpu_power_consumption')][0]
                else:
                    continue

                plugins.append({
                    "Plugin Name": plugin_name,
                    "Total CPU Consumption (W)": round(cpu_power, 3),
                    "Total GPU Consumption (W)": round(gpu_power, 3)
                })
        plugins_df = pd.DataFrame(plugins)
        plugins_df.set_index("Plugin Name", inplace=True)

        return end_date, end_time, total_cpu, total_gpu, plugins_df


col1 = st.container()

# Display DataFrames in columns
with col1:
    selected_user = st.selectbox("Select User", users)

if selected_user:
    with col1:
        exp_summary_user = kg.get_experiment_info_for_user(selected_user)

        default_rows = 3
        height = min(50 * default_rows, 50 * len(exp_summary_user))
        st.dataframe(exp_summary_user, use_container_width=True, height=height)

if selected_user:
    experiments = kg.fetch_experiments(selected_user)
    with col1:
        selected_experiment = st.selectbox(f"Select Experiment performed by {selected_user}", experiments['experiment_id'])

# Load user-specific data
if selected_experiment:
    with col1:
        # get the experiment details for the selected experiment
        experiment_info = kg.get_exp_info_raw(selected_experiment)

        # extracting model id and drop
        model_id = experiment_info['Model'].iloc[0]
        experiment_info = experiment_info.drop(columns=['Model'])
        experiment_info = experiment_info.drop(columns=['Delete Time'])

        # Get experiment summary
        date_str, time_str, model_name, device_info, average_accuracy = get_experiment_indicators(selected_experiment, exp_summary_user, model_id)

        # Get deployment information
        deployment_info = kg.get_exp_deployment_info(selected_experiment)
        end_date, end_time, total_cpu, total_gpu, plugins_df = get_power_info(deployment_info)

        # Create columns based on whether end_date and end_time are provided
        columns = st.columns(5 if end_date and end_time else 4)
        columns[0].metric(label="Start Time", value=f"{date_str} {time_str} EDT")
        columns[1].metric(label="Model", value=model_name)
        columns[2].metric(label="Device Type", value=device_info)
        columns[3].metric(label="Average Accuracy [%]", value=average_accuracy)

        if end_date and end_time:
            columns[-1].metric(label="End time", value=f"{end_date} {end_time} EDT")

        # Display experiment raw data
        st.dataframe(experiment_info, use_container_width=True)

        if plugins_df is not None:
            st.markdown("#### Power Information")
            col1, col2 = st.columns(2)
            col1.metric(label="Total CPU Consumption (W)", value=total_cpu)
            col2.metric(label="Total GPU Consumption (W)", value=total_gpu)
            st.dataframe(plugins_df, use_container_width=True)

        else:
            st.write("No power information available for this experiment.")

