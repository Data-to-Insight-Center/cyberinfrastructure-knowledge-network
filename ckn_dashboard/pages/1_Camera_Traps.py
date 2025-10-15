import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import json

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

    # Set average_accuracy to N/A since we removed the accuracy column
    average_accuracy = 'N/A'

    model_name = kg.get_mode_name_version(model_id)
    if model_name is None:
        model_name = "BioCLIP:1.0"

    # get device information
    device_info = kg.get_device_type(experiment_id)

    return date_str, time_str, model_name, device_info, average_accuracy

def _is_number(value):
    return isinstance(value, (int, float))


def _fmt_dec(value, decimals=4):
    return f"{value:.{decimals}f}" if _is_number(value) else "-"


def _progress_if_number(value):
    if _is_number(value):
        v = max(0.0, min(1.0, float(value)))
        st.progress(v)


def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    Box format: [x1, y1, x2, y2] where (x1,y1) is top-left and (x2,y2) is bottom-right.
    """
    # Calculate intersection coordinates
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    # Calculate intersection area
    intersection = max(0, x2 - x1) * max(0, y2 - y1)

    # Calculate union area
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0


def get_power_info(deployment_info):
    """
    Parameters
    ----------
    deployment_info : dict
        Deployment information for an experiment.

    Returns
    -------
    total_cpu : float
        Total CPU power consumption.
    total_gpu : float
        Total GPU power consumption.
    end_date : str
        End date of the experiment.
    end_time : str
        End time of the experiment.
    plugins_df : pd.DataFrame
        DataFrame containing plugin information.
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

        # Fetch experiment-level detection metrics from DB
        db_metrics = kg.get_experiment_metrics(selected_experiment) or {}

        # Normalize dataset metrics expected by the UI using DB values
        dataset_metrics = {
            "total_images": db_metrics.get("total_images"),
            "total_ground_truth_objects": db_metrics.get("total_ground_truth_objects"),
            "total_predictions": db_metrics.get("total_predictions"),
            "true_positives": db_metrics.get("true_positives"),
            "false_positives": db_metrics.get("false_positives"),
            "false_negatives": db_metrics.get("false_negatives"),
            "mean_iou": db_metrics.get("mean_iou"),
            "precision": db_metrics.get("precision"),
            "recall": db_metrics.get("recall"),
            "f1_score": db_metrics.get("f1_score"),
            "map_50": db_metrics.get("map_50"),
            "map_75": db_metrics.get("map_75"),
            "map_50_95": db_metrics.get("map_50_95"),
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


        # Detection Metrics (Collapsible)
        if dataset_metrics["true_positives"] and dataset_metrics["total_images"] and dataset_metrics["total_ground_truth_objects"] and dataset_metrics["total_predictions"] is not None:
            with st.expander("Detection Metrics", expanded=True):
                # First row - Basic counts
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="Total Images",
                        value=str(dataset_metrics["total_images"]) if dataset_metrics["total_images"] is not None else "-",
                        help="Number of images processed in this experiment"
                    )

                with col2:
                    st.metric(
                        label="Ground Truth Objects",
                        value=str(dataset_metrics["total_ground_truth_objects"]) if dataset_metrics["total_ground_truth_objects"] is not None else "-",
                        help="Number of objects in ground truth annotations"
                    )

                with col3:
                    st.metric(
                        label="Total Predictions",
                        value=str(dataset_metrics["total_predictions"]) if dataset_metrics["total_predictions"] is not None else "-",
                        help="Total number of predictions made by the model"
                    )

                # Second row - Performance metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="True Positives",
                        value=str(dataset_metrics["true_positives"]) if dataset_metrics["true_positives"] is not None else "-",
                        help="Correctly detected objects (IoU > 0.5)"
                    )

                with col2:
                    st.metric(
                        label="False Positives",
                        value=str(dataset_metrics["false_positives"]) if dataset_metrics["false_positives"] is not None else "-",
                        help="Incorrect detections"
                    )

                with col3:
                    st.metric(
                        label="False Negatives",
                        value=str(dataset_metrics["false_negatives"]) if dataset_metrics["false_negatives"] is not None else "-",
                        help="Missed ground truth objects"
                    )


        # Precision & Recall (Collapsible)
        if dataset_metrics["precision"] and dataset_metrics["recall"] and dataset_metrics["f1_score"] is not None:
            with st.expander("Precision & Recall", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="Precision",
                        value=_fmt_dec(dataset_metrics.get('precision'), 4),
                        help="TP / (TP + FP) - Accuracy of positive predictions"
                    )
                    _progress_if_number(dataset_metrics.get('precision'))

                with col2:
                    st.metric(
                        label="Recall",
                        value=_fmt_dec(dataset_metrics.get('recall'), 4),
                        help="TP / (TP + FN) - Ability to find all positive instances"
                    )
                    _progress_if_number(dataset_metrics.get('recall'))

                with col3:
                    st.metric(
                        label="F1 Score",
                        value=_fmt_dec(dataset_metrics.get('f1_score'), 4),
                        help="Harmonic mean of precision and recall"
                    )
                    _progress_if_number(dataset_metrics.get('f1_score'))

        # mAP Metrics (Collapsible)
        if dataset_metrics["map_50"] and dataset_metrics["map_75"] and dataset_metrics["map_50_95"] is not None:
                with st.expander("mAP Metrics", expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            label="mAP@0.5",
                            value=_fmt_dec(dataset_metrics.get('map_50'), 3),
                            help="Mean Average Precision at IoU threshold 0.5"
                        )
                        _progress_if_number(dataset_metrics.get('map_50'))

                    with col2:
                        st.metric(
                            label="mAP@0.75",
                            value=_fmt_dec(dataset_metrics.get('map_75'), 3),
                            help="Mean Average Precision at IoU threshold 0.75"
                        )
                        _progress_if_number(dataset_metrics.get('map_75'))

                    with col3:
                        st.metric(
                            label="mAP@[0.5:0.95]",
                            value=_fmt_dec(dataset_metrics.get('map_50_95'), 3),
                            help="Mean Average Precision across IoU thresholds 0.5 to 0.95"
                        )
                        _progress_if_number(dataset_metrics.get('map_50_95'))

        # Image Classification Metrics
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
