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

def calculate_accuracy_from_experiment(experiment_details):
    """
    Calculate the accuracy of model predictions against ground truth labels.
    """

    total = 0
    correct = 0
    missing_ground_truth = 0
    missing_or_invalid_scores = 0

    for index, row in experiment_details.iterrows():
        ground_truth = row.get("Ground Truth")
        scores_str = row.get("Scores", "")

        # Check for missing Ground Truth
        if pd.isna(ground_truth):
            missing_ground_truth += 1
            continue

        # Check for missing or empty Scores
        if pd.isna(scores_str) or not isinstance(scores_str, str) or not scores_str.strip():
            missing_or_invalid_scores += 1
            continue

        try:
            # Parse the JSON string in Scores
            scores = json.loads(scores_str)
        except json.JSONDecodeError:
            missing_or_invalid_scores += 1
            continue

        # Aggregate probabilities per label
        label_prob = {}
        for entry in scores:
            label = entry.get("label")
            probability = entry.get("probability", 0)
            if label:
                label_prob[label] = label_prob.get(label, 0) + probability

        if not label_prob:
            missing_or_invalid_scores += 1
            continue

        # Determine the predicted label with the highest aggregated probability
        predicted_label = max(label_prob, key=label_prob.get)

        # Update total and correct counts
        total += 1
        if predicted_label.lower() == ground_truth.lower():
            correct += 1

    # Calculate accuracy
    accuracy = (correct / total) * 100 if total > 0 else 0

    return accuracy


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


def calculate_object_detection_metrics(experiment_details):
    """
    Calculate comprehensive object detection metrics for camera traps experiments.
    Returns both dataset-level and image-level classification metrics.
    """

    # Initialize counters for dataset metrics
    total_images = 0
    total_ground_truth_objects = 0
    total_predictions = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    iou_scores = []

    # Initialize counters for image classification metrics
    correct_predictions = 0
    incorrect_predictions = 0

    # Debug: Print first few rows to understand data structure (only in debug mode)
    debug_mode = False  # Set to True to see debug output
    if debug_mode:
        print("DEBUG: First few rows of experiment_details:")
        for idx, row in experiment_details.head(3).iterrows():
            print(f"Row {idx}:")
            print(f"  Ground Truth: {row.get('Ground Truth')}")
            print(f"  Scores: {row.get('Scores')[:200]}...")  # First 200 chars
            print(f"  Ground Truth BBox: {row.get('Ground Truth BBox', 'Not available')}")
            print()

    for index, row in experiment_details.iterrows():
        ground_truth = row.get("Ground Truth")
        scores_str = row.get("Scores", "")
        ground_truth_bbox = row.get("Ground Truth BBox", None)

        # Skip if missing ground truth or scores
        if pd.isna(ground_truth) or pd.isna(scores_str) or not isinstance(scores_str, str):
            continue

        try:
            scores = json.loads(scores_str)
        except json.JSONDecodeError:
            continue

        total_images += 1

        # Parse predictions from scores
        predictions = []
        if debug_mode:
            print(f"DEBUG: Processing {len(scores)} scores for image {total_images + 1}")

        for i, entry in enumerate(scores):
            label = entry.get("label")
            probability = entry.get("probability", 0)
            bbox = entry.get("bbox", [])  # [x1, y1, x2, y2] format

            if debug_mode:
                print(f"  Score {i}: label='{label}', probability={probability}, bbox={bbox}")

            # Accept predictions with valid labels (bbox is optional)
            if label:
                # If bbox is missing or invalid, use placeholder
                if not isinstance(bbox, list) or len(bbox) != 4:
                    bbox = [0, 0, 100, 100]  # Placeholder bbox

                predictions.append({
                    "label": label,
                    "probability": probability,
                    "bbox": bbox
                })
                if debug_mode:
                    print(f"    -> Added to predictions")
            else:
                if debug_mode:
                    print(f"    -> Skipped (no valid label)")

        if debug_mode:
            print(f"DEBUG: Found {len(predictions)} valid predictions")

        # Sort predictions by probability (highest first)
        predictions.sort(key=lambda x: x["probability"], reverse=True)

        # For image classification, use the highest confidence prediction
        if predictions:
            best_prediction = predictions[0]
            predicted_label = best_prediction["label"]

            # Compare with ground truth for image classification
            if predicted_label.lower() == ground_truth.lower():
                correct_predictions += 1
            else:
                incorrect_predictions += 1

        # For object detection metrics, parse ground truth bounding boxes
        gt_objects = []
        if ground_truth and ground_truth.lower() != "empty":
            if ground_truth_bbox and not pd.isna(ground_truth_bbox):
                try:
                    # Try to parse ground truth bounding box if available
                    if isinstance(ground_truth_bbox, str):
                        gt_bbox = json.loads(ground_truth_bbox)
                    else:
                        gt_bbox = ground_truth_bbox

                    if isinstance(gt_bbox, list) and len(gt_bbox) == 4:
                        gt_objects.append({
                            "label": ground_truth,
                            "bbox": gt_bbox
                        })
                    else:
                        # Fallback to placeholder bbox
                        gt_objects.append({
                            "label": ground_truth,
                            "bbox": [0, 0, 100, 100]
                        })
                except (json.JSONDecodeError, TypeError):
                    # Fallback to placeholder bbox
                    gt_objects.append({
                        "label": ground_truth,
                        "bbox": [0, 0, 100, 100]
                    })
            else:
                # No bounding box data available, use placeholder
                gt_objects.append({
                    "label": ground_truth,
                    "bbox": [0, 0, 100, 100]
                })

        total_ground_truth_objects += len(gt_objects)

        # Match predictions to ground truth objects using IoU
        matched_gt = set()
        matched_pred = set()

        for pred_idx, prediction in enumerate(predictions):
            best_iou = 0
            best_gt_idx = -1

            for gt_idx, gt_object in enumerate(gt_objects):
                if gt_idx in matched_gt:
                    continue

                if prediction["label"].lower() == gt_object["label"].lower():
                    iou = calculate_iou(prediction["bbox"], gt_object["bbox"])
                    if iou > best_iou and iou > 0.5:  # IoU threshold
                        best_iou = iou
                        best_gt_idx = gt_idx

            if best_gt_idx >= 0:
                true_positives += 1
                matched_gt.add(best_gt_idx)
                matched_pred.add(pred_idx)
                iou_scores.append(best_iou)
            else:
                false_positives += 1

        # Count unmatched ground truth objects as false negatives
        false_negatives += len(gt_objects) - len(matched_gt)

        # Total predictions is the sum of predictions with valid bounding boxes
        total_predictions += len(predictions)

    # Calculate dataset metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    mean_iou = sum(iou_scores) / len(iou_scores) if iou_scores else 0

    # Calculate mAP (simplified - in practice you'd need per-class AP calculations)
    map_50 = precision  # Simplified mAP@0.5
    map_75 = precision * 0.9  # Simplified mAP@0.75 (assume 90% of mAP@0.5)
    map_50_95 = (map_50 + map_75) / 2  # Simplified mAP@[0.5:0.95]

    # Calculate image classification accuracy
    image_accuracy = correct_predictions / total_images if total_images > 0 else 0

    dataset_metrics = {
        "total_images": total_images,
        "total_ground_truth_objects": total_ground_truth_objects,
        "total_predictions": total_predictions,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "mean_iou": round(mean_iou, 3),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "average_precision": round(map_50, 3),
        "map_50": round(map_50, 3),
        "map_75": round(map_75, 3),
        "map_50_95": round(map_50_95, 3)
    }

    image_classification_metrics = {
        "total_images": total_images,
        "correct_predictions": correct_predictions,
        "incorrect_predictions": incorrect_predictions,
        "accuracy": round(image_accuracy, 2)
    }

    return dataset_metrics, image_classification_metrics


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

        # Calculate object detection metrics
        dataset_metrics, image_classification_metrics = calculate_object_detection_metrics(experiment_info)

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
        if dataset_metrics["total_predictions"] > 0:
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
            st.warning("No predictions found in the data")

        # Detection Metrics (Collapsible)
        with st.expander("Detection Metrics", expanded=True):
            # First row - Basic counts
            col1, col2, col3, col4 = st.columns(4)

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

            with col4:
                st.metric(
                    label="True Positives",
                    value=dataset_metrics["true_positives"],
                    help="Correctly detected objects (IoU > 0.5)"
                )

            # Second row - Performance metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="False Positives",
                    value=dataset_metrics["false_positives"],
                    help="Incorrect detections"
                )

            with col2:
                st.metric(
                    label="False Negatives",
                    value=dataset_metrics["false_negatives"],
                    help="Missed ground truth objects"
                )

            with col3:
                st.metric(
                    label="Mean IoU",
                    value=f"{dataset_metrics['mean_iou']:.3f}",
                    help="Average Intersection over Union for true positives"
                )

            with col4:
                st.metric(
                    label="Precision",
                    value=f"{dataset_metrics['precision']:.4f}",
                    help="TP / (TP + FP) - Accuracy of positive predictions"
                )

        # Precision & Recall (Collapsible)
        with st.expander("Precision & Recall", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Recall",
                    value=f"{dataset_metrics['recall']:.4f}",
                    help="TP / (TP + FN) - Ability to find all positive instances"
                )
                st.progress(dataset_metrics['recall'])

            with col2:
                st.metric(
                    label="F1 Score",
                    value=f"{dataset_metrics['f1_score']:.4f}",
                    help="Harmonic mean of precision and recall"
                )
                st.progress(dataset_metrics['f1_score'])

        # mAP Metrics (Collapsible)
        with st.expander("mAP Metrics", expanded=False):
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

        # Image Classification Metrics
        st.markdown("---")


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
