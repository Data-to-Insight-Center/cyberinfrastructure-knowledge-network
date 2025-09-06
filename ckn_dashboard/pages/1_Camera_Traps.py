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
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'About': 'Camera Traps Experiment Dashboard'
    }
)
st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 20px;
}
[data-testid="stMetricLabel"] {
    font-size: 16px !important;
    font-weight: 600 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 14px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

st.header("Camera Traps Experiments")

users = kg.fetch_distinct_users()
if not users:
    st.write("Knowledge Graph is empty.")
    st.stop()

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
        # Try to get data with bounding boxes first, fallback to raw data
        try:
            experiment_info = kg.get_exp_info_with_bbox(selected_experiment)
        except:
            experiment_info = kg.get_exp_info_raw(selected_experiment)

        # Get experiment metrics directly from the Experiment node
        dataset_metrics = kg.get_experiment_metrics(selected_experiment)
        
        # Create image classification metrics from dataset metrics
        if dataset_metrics and dataset_metrics["total_images"] > 0:
            # For image classification, we'll use the overall detection accuracy as a proxy
            overall_accuracy = (dataset_metrics["true_positives"] / dataset_metrics["total_predictions"]) * 100 if dataset_metrics["total_predictions"] > 0 else 0
            correct_predictions = int((overall_accuracy / 100) * dataset_metrics["total_images"])
            incorrect_predictions = dataset_metrics["total_images"] - correct_predictions
            
            image_classification_metrics = {
                "total_images": dataset_metrics["total_images"],
                "correct_predictions": correct_predictions,
                "incorrect_predictions": incorrect_predictions,
                "accuracy": overall_accuracy
            }
        else:
            image_classification_metrics = {
                "total_images": 0,
                "correct_predictions": 0,
                "incorrect_predictions": 0,
                "accuracy": 0
            }

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
        columns = st.columns(4 if end_date and end_time else 3)
        columns[0].metric(label="Start Time", value=f"{date_str} {time_str} EDT")
        columns[1].metric(label="Model", value=model_name)
        columns[2].metric(label="Device Type", value=device_info)
        # columns[3].metric(label="Average Accuracy [%]", value=average_accuracy)

        if end_date and end_time:
            columns[-1].metric(label="End time", value=f"{end_date} {end_time} EDT")

        # Object Detection Metrics Section

        # Performance Summary with Progress Bars
        if dataset_metrics and dataset_metrics["total_predictions"] > 0:
            overall_accuracy = (dataset_metrics["true_positives"] / dataset_metrics["total_predictions"]) * 100

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="Overall Detection Accuracy",
                    value=f"{overall_accuracy:.1f}%",
                    delta=f"{dataset_metrics['true_positives']}/{dataset_metrics['total_predictions']} correct",
                    help="Percentage of correct predictions out of all predictions made by the model (True Positives / Total Predictions)"
                )
                st.progress(overall_accuracy / 100)

            with col2:
                if dataset_metrics["total_ground_truth_objects"] > 0:
                    detection_rate = (dataset_metrics["true_positives"] / dataset_metrics["total_ground_truth_objects"]) * 100
                    st.metric(
                        label="Detection Rate",
                        value=f"{detection_rate:.1f}%",
                        delta=f"{dataset_metrics['true_positives']}/{dataset_metrics['total_ground_truth_objects']} detected",
                        help="Percentage of ground truth objects that were successfully detected by the model (True Positives / Ground Truth Objects)"
                    )
                    st.progress(detection_rate / 100)

            with col3:
                if image_classification_metrics["total_images"] > 0:
                    classification_accuracy = image_classification_metrics["accuracy"] * 100

                    # Single accuracy metric with progress bar
                    st.metric(
                        label="Classification Accuracy",
                        value=f"{classification_accuracy:.1f}%",
                        delta=f"{image_classification_metrics['correct_predictions']}/{image_classification_metrics['total_images']} correct",
                        help="Percentage of images correctly classified by selecting the highest-confidence prediction per image"
                    )
                    st.progress(classification_accuracy / 100)

        else:
            if dataset_metrics is None:
                st.warning("No experiment metrics found in the database")
            else:
                st.warning("No predictions found in the data")

        # Detection Metrics (Collapsible)
        with st.expander("Detection Metrics", expanded=True):
            if dataset_metrics:
                # First row - Basic counts
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="Total Images",
                        value=dataset_metrics["total_images"],
                        help="Number of images processed in this experiment"
                    )

                with col2:
                    st.metric(
                        label="Ground Truth Objects",
                        value=dataset_metrics["total_ground_truth_objects"],
                        help="Number of objects in ground truth annotations"
                    )

                with col3:
                    st.metric(
                        label="Total Predictions",
                        value=dataset_metrics["total_predictions"],
                        help="Total number of predictions made by the model"
                    )

                # Second row - Performance metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="True Positives",
                        value=dataset_metrics["true_positives"],
                        help="Correctly detected objects (IoU > 0.5)"
                    )

                with col2:
                    st.metric(
                        label="False Positives",
                        value=dataset_metrics["false_positives"],
                        help="Incorrect detections"
                    )

                with col3:
                    st.metric(
                        label="False Negatives",
                        value=dataset_metrics["false_negatives"],
                        help="Missed ground truth objects"
                    )
            else:
                st.warning("No detection metrics available for this experiment")


        # Precision & Recall (Collapsible)
        with st.expander("Precision & Recall", expanded=False):
            if dataset_metrics:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="Precision",
                        value=f"{dataset_metrics['precision']:.4f}",
                        help="TP / (TP + FP) - Accuracy of positive predictions"
                    )
                    st.progress(dataset_metrics['precision'])

                with col2:
                    st.metric(
                        label="Recall",
                        value=f"{dataset_metrics['recall']:.4f}",
                        help="TP / (TP + FN) - Ability to find all positive instances"
                    )
                    st.progress(dataset_metrics['recall'])

                with col3:
                    st.metric(
                        label="F1 Score",
                        value=f"{dataset_metrics['f1_score']:.4f}",
                        help="Harmonic mean of precision and recall"
                    )
                    st.progress(dataset_metrics['f1_score'])
            else:
                st.warning("No precision/recall metrics available for this experiment")

        # mAP Metrics (Collapsible)
        with st.expander("mAP Metrics", expanded=False):
            if dataset_metrics:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="mAP@0.5",
                        value=f"{dataset_metrics['map_50']:.3f}",
                        help="Mean Average Precision at IoU threshold 0.5"
                    )
                    st.progress(dataset_metrics['map_50'])

                with col2:
                    st.metric(
                        label="mAP@0.75",
                        value=f"{dataset_metrics['map_75']:.3f}",
                        help="Mean Average Precision at IoU threshold 0.75"
                    )
                    st.progress(dataset_metrics['map_75'])

                with col3:
                    st.metric(
                        label="mAP@[0.5:0.95]",
                        value=f"{dataset_metrics['map_50_95']:.3f}",
                        help="Mean Average Precision across IoU thresholds 0.5 to 0.95"
                    )
                    st.progress(dataset_metrics['map_50_95'])
            else:
                st.warning("No mAP metrics available for this experiment")

        # Image Classification Metrics
        st.markdown("---")
        st.markdown("Experiment Raw Data")


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
