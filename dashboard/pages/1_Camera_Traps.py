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

    average_accuracy = selected_experiment['Accuracy [%]']

    if average_accuracy is None:
        average_accuracy = 'N/A'
    else:
        average_accuracy = round(average_accuracy, 2)

    total_images = selected_experiment['Total Images']
    saved_images = selected_experiment['Saved Images']
    deleted_images = total_images - saved_images

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Start Date", value=date_str)
    col2.metric(label="Start Time", value=time_str)
    col3.metric(label="Average Accuracy [%]", value=average_accuracy)
    col4.metric(label="Saved / Deleted Images", value=f"{saved_images} / {deleted_images}")

def show_model_device_info(model_id, experiment_id):
    col1, col2 = st.columns(2)
    # get model information
    model_name = kg.get_mode_name_version(model_id)

    if model_name is None:
        model_name = "BioCLIP:1.0"

    # get device information
    device_info = kg.get_device_type(experiment_id)

    col1.metric(label="Model:", value=model_name)
    col2.metric(label="Device Type:", value=device_info)



# Create three columns
col1, col2= st.columns(2)

# Display DataFrames in columns
with col1:
    selected_user = st.selectbox("Select User", users)
    st.write(" ")

if selected_user:
    experiments = kg.fetch_experiments(selected_user)
    with col2:
        selected_experiment = st.selectbox("Select Experiment", experiments['experiment_id'])
        st.write(" ")

if selected_user:
    with col1:
        st.subheader(f"Experiment details for user: {selected_user}")
        exp_summary_user = kg.get_experiment_info_for_user(selected_user)
        st.write(exp_summary_user)


def show_power_info(deployment_info):
    """
    Retrieve and show power information for a given experiment.
    :param deployment_info:
    :return:
    """
    if deployment_info is None:
        st.write("No deployment info found for the experiment.")
    else:
        st.markdown("##### Power information")
        total_cpu = round(deployment_info['total_cpu_power_consumption'][0], 3)
        total_gpu = round(deployment_info['total_gpu_power_consumption'][0], 3)
        end_timestamp = str(deployment_info['End Time'][0].strftime('%Y-%m-%d %H:%M:%S'))
        end_date, end_time = end_timestamp.split(' ')

        col10, col11, col12, col13 = st.columns(4)
        # col11.write("Start Time:", deployment_info['Start Time'][0])
        col10.metric(label="End Date", value=end_date)
        col11.metric(label="End time", value=end_time)
        col12.metric(label="Total CPU (W)", value=total_cpu)
        col13.metric(label="Total GPU (W)", value=total_gpu)

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
        st.dataframe(plugins_df)


# Load user-specific data
if selected_experiment:
    with col2:
        # Display experiment summary
        display_experiment_indicators(selected_experiment, exp_summary_user)

        # get the experiment details for the selected experiment
        experiment_info = kg.get_exp_info_raw(selected_experiment)

        # extracting model id
        model_id = experiment_info['Model'].iloc[0]

        # dropping the model from the dataframe
        experiment_info = experiment_info.drop(columns=['Model'])
        experiment_info = experiment_info.drop(columns=['Delete Time'])

        # show model and device information
        show_model_device_info(model_id, selected_experiment)

        # Display experiment raw data
        st.markdown("##### Experiment data")
        st.write(experiment_info)

        # Display deployment information
        deployment_info = kg.get_exp_deployment_info(selected_experiment)
        show_power_info(deployment_info)

