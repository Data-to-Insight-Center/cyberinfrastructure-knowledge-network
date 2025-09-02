import logging
import sys
import time
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from confluent_kafka import Producer, KafkaError
from confluent_kafka.admin import AdminClient
from power_processor import PowerProcessor

ORACLE_EVENTS_FILE = os.getenv('ORACLE_CSV_PATH', 'plugins/oracle_ckn_daemon/events/image_mapping_final.json')
CKN_LOG_FILE = os.getenv('CKN_LOG_FILE', './ckn_daemon.log')
KAFKA_BROKER = os.getenv('CKN_KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('CKN_KAFKA_TOPIC', 'oracle-events')
DEVICE_ID = os.getenv('CAMERA_TRAPS_DEVICE_ID', 'iu-edge-server-cib')
USER_ID = os.getenv('USER_ID', 'jstubbs')
EXPERIMENT_ID = os.getenv('EXPERIMENT_ID', 'googlenet-iu-animal-classification')
EXPERIMENT_END_SIGNAL = os.getenv('EXPERIMENT_END_SIGNAL', '6e153711-9823-4ee6-b608-58e2e801db51')

POWER_SUMMARY_FILE = os.getenv('POWER_SUMMARY_FILE', 'plugins/oracle_ckn_daemon/events/power_summary_report.json')
POWER_SUMMARY_TOPIC = os.getenv('POWER_SUMMARY_TOPIC', 'cameratraps-power-summary')
POWER_SUMMARY_TIMOUT = os.getenv('POWER_SUMMARY_TIMOUT', 10)
POWER_SUMMARY_MAX_TRIES = os.getenv('POWER_SUMMARY_TIMOUT', 5)
ENABLE_POWER_MONITORING = os.getenv('ENABLE_POWER_MONITORING', "false")


class OracleEventHandler(FileSystemEventHandler):
    """
    Event handler class to handle events received from the Oracle plugin through the output.json.
    """

    def __init__(self, file_path, producer, topic, device_id, experiment_id, user_id):
        self.file_path = file_path
        self.producer = producer
        self.topic = topic
        self.device_id = device_id
        self.experiment_id = experiment_id
        self.user_id = user_id
        self.processed_images = set()
        self.stop_daemon = False
        # Running experiment-level metrics
        self.metrics = {
            "total_images": 0,
            "total_predictions": 0,
            "total_ground_truth_objects": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "mean_iou": None,
            "map_50": None,
            "map_50_95": None,
            # Internal accumulators for IoU/mAP
            "sum_iou": 0.0,
            "num_iou_pairs": 0,
            "gt_boxes_count": 0,
        }
        # For mAP: keep per-threshold prediction lists of (score, is_tp)
        self.map_thresholds = [round(t, 2) for t in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]]
        self.map_data = {t: [] for t in self.map_thresholds}

    def _compute_iou(self, box_a, box_b):
        """
        Compute IoU between two boxes in [x, y, w, h] format with normalized coordinates.
        """
        ax, ay, aw, ah = box_a
        bx, by, bw, bh = box_b
        ax2, ay2 = ax + aw, ay + ah
        bx2, by2 = bx + bw, by + bh
        inter_x1 = max(ax, bx)
        inter_y1 = max(ay, by)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        area_a = max(0.0, aw) * max(0.0, ah)
        area_b = max(0.0, bw) * max(0.0, bh)
        union = area_a + area_b - inter_area
        return (inter_area / union) if union > 0 else 0.0

    def _greedy_match(self, preds, gts, iou_threshold):
        """
        Greedy 1-1 matching between predictions and ground truths by IoU threshold.
        Returns list of (pred_idx, gt_idx, iou) for matches.
        """
        matches = []
        used_preds = set()
        used_gts = set()
        # Precompute IoU matrix
        iou_matrix = []
        for pi, p in enumerate(preds):
            pbox = p.get("bounding_box")
            prow = []
            for gi, g in enumerate(gts):
                gbox = g.get("bounding_box")
                iou = self._compute_iou(pbox, gbox)
                prow.append((gi, iou))
            iou_matrix.append((pi, prow))
        # Iterate by descending IoU candidates
        candidates = []
        for pi, prow in iou_matrix:
            for gi, iou in prow:
                candidates.append((iou, pi, gi))
        candidates.sort(reverse=True)
        for iou, pi, gi in candidates:
            if iou < iou_threshold:
                break
            if pi in used_preds or gi in used_gts:
                continue
            matches.append((pi, gi, iou))
            used_preds.add(pi)
            used_gts.add(gi)
        return matches, used_preds, used_gts

    def _update_map_structures(self, predictions, gt_boxes):
        """
        Update per-threshold AP structures using label-aware matches.
        """
        for thr in self.map_thresholds:
            matches, used_preds, used_gts = self._greedy_match(predictions, gt_boxes, thr)
            # Label-aware: only count as TP if labels match
            matched_gt_by_pred = {pi: gi for pi, gi, _ in matches}
            for pi, pred in enumerate(predictions):
                score = float(pred.get("probability", 0.0))
                if pi in matched_gt_by_pred:
                    gi = matched_gt_by_pred[pi]
                    if str(pred.get("label")) == str(gt_boxes[gi].get("label")):
                        self.map_data[thr].append((score, True))
                    else:
                        self.map_data[thr].append((score, False))
                else:
                    self.map_data[thr].append((score, False))

    def _compute_ap(self, preds_list, num_gt):
        """
        Compute AP given list of (score, is_tp) and total GT count.
        Uses standard 11-point interpolation-like precision envelope integration.
        """
        if num_gt <= 0 or not preds_list:
            return 0.0
        # Sort by score desc
        preds_sorted = sorted(preds_list, key=lambda x: x[0], reverse=True)
        tp_cum = 0
        fp_cum = 0
        precisions = []
        recalls = []
        for score, is_tp in preds_sorted:
            if is_tp:
                tp_cum += 1
            else:
                fp_cum += 1
            precision = tp_cum / max(tp_cum + fp_cum, 1)
            recall = tp_cum / num_gt
            precisions.append(precision)
            recalls.append(recall)
        # Precision envelope
        for i in range(len(precisions) - 2, -1, -1):
            if precisions[i] < precisions[i + 1]:
                precisions[i] = precisions[i + 1]
        # Integrate AP over recall from 0 to 1 based on observed points
        ap = 0.0
        prev_recall = 0.0
        for p, r in zip(precisions, recalls):
            if r > prev_recall:
                ap += p * (r - prev_recall)
                prev_recall = r
        return ap

    def _update_experiment_metrics(self, ground_truth_label, scores_list, ground_truth_boxes=None):
        """
        Update running experiment metrics based on a single image's ground truth label and predictions.
        If ground-truth bounding boxes are provided as a list of {label, bounding_box}, compute IoU and mAP.
        """
        # Normalize inputs
        gt = None if ground_truth_label is None else str(ground_truth_label)
        has_gt_object = gt is not None and gt.lower() not in ["empty", "unknown"]

        predictions = scores_list if isinstance(scores_list, list) else []
        num_predictions = len(predictions)
        predicted_labels = [str(p.get("label")) for p in predictions if p and p.get("label") is not None]

        # If GT boxes exist, use detection-based accounting; else use classification fallback
        detection_mode = isinstance(ground_truth_boxes, list) and len(ground_truth_boxes) > 0
        increment_true_positive = 0
        increment_false_negative = 0
        increment_false_positive = 0
        if detection_mode:
            # Ensure GT boxes have label and bounding_box
            gt_boxes = [g for g in ground_truth_boxes if g and g.get("bounding_box") is not None]
            self.metrics["gt_boxes_count"] += len(gt_boxes)
            # Update mAP structures
            self._update_map_structures(predictions, gt_boxes)
            # Compute matches at IoU 0.5 for TP/FP/FN and IoU accumulation
            matches, used_preds, used_gts = self._greedy_match(predictions, gt_boxes, 0.5)
            # Label-aware TP
            tp_count = 0
            sum_iou_img = 0.0
            for pi, gi, iou in matches:
                if str(predictions[pi].get("label")) == str(gt_boxes[gi].get("label")):
                    tp_count += 1
                    sum_iou_img += iou
            fp_count = max(num_predictions - len(used_preds), 0)
            fn_count = max(len(gt_boxes) - len(used_gts), 0)
            increment_true_positive = tp_count
            increment_false_positive = fp_count
            increment_false_negative = fn_count
            # Update IoU accumulators
            if tp_count > 0:
                self.metrics["sum_iou"] += sum_iou_img
                self.metrics["num_iou_pairs"] += tp_count
        else:
            # Classification-based TP/FP/FN (1 GT object at most per image in current data)
            has_correct_prediction = has_gt_object and any(lbl == gt for lbl in predicted_labels)
            increment_true_positive = 1 if has_correct_prediction else 0
            increment_false_negative = 1 if has_gt_object and not has_correct_prediction else 0
            increment_false_positive = max(num_predictions - (1 if has_correct_prediction else 0), 0)

        # Update totals
        self.metrics["total_images"] += 1
        self.metrics["total_predictions"] += num_predictions
        if detection_mode:
            self.metrics["total_ground_truth_objects"] += len(ground_truth_boxes)
        else:
            self.metrics["total_ground_truth_objects"] += 1 if has_gt_object else 0
        self.metrics["true_positives"] += increment_true_positive
        self.metrics["false_negatives"] += increment_false_negative
        self.metrics["false_positives"] += increment_false_positive

        # Derived metrics
        tp = float(self.metrics["true_positives"]) 
        fp = float(self.metrics["false_positives"]) 
        fn = float(self.metrics["false_negatives"]) 
        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        self.metrics["precision"] = precision
        self.metrics["recall"] = recall
        self.metrics["f1_score"] = f1
        # Mean IoU
        if self.metrics["num_iou_pairs"] > 0:
            self.metrics["mean_iou"] = self.metrics["sum_iou"] / self.metrics["num_iou_pairs"]
        # mAP@0.5 and mAP@0.5:0.95 using accumulated predictions
        if self.metrics["gt_boxes_count"] > 0:
            # AP at 0.5
            ap50 = self._compute_ap(self.map_data[0.5], self.metrics["gt_boxes_count"]) if 0.5 in self.map_data else 0.0
            # Mean AP across thresholds
            ap_values = []
            for t in self.map_thresholds:
                ap_values.append(self._compute_ap(self.map_data[t], self.metrics["gt_boxes_count"]))
            map_50_95 = sum(ap_values) / len(ap_values) if ap_values else 0.0
            self.metrics["map_50"] = ap50
            self.metrics["map_50_95"] = map_50_95

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        """
        When the file is modified, execute the event handler.
        """
        if event.src_path == self.file_path:
            logging.debug(f"File {self.file_path} modified.")
            self.read_json_events()

    def read_json_events(self):
        """
        Reads the JSON events from the file.
        Only sends events if the image_decision component is present in the JSON entry.
        This is to make sure only the processed images are extracted.
        """
        logging.debug(f"Reading new image data from {self.file_path}")
        # Load the JSON data from the file. If the file is not yet written fully, wait for it to be written.
        while True:
            try:
                with open(self.file_path, 'r') as file:
                    data = json.load(file)
                    break
            except json.JSONDecodeError:
                logging.debug("File not complete. Waiting for the file to be completely written")
                time.sleep(1)

        shutdown_signal = False
        # Process each entry in the JSON data
        for key, value in data.items():

            # shutdown signal received from oracle. process the rest of the images you haven't processed and exit.
            if key == EXPERIMENT_END_SIGNAL:
                shutdown_signal = True

            # if the full image processing workflow is not yet completed, don't read the json
            if "image_decision" not in value:
                continue

            uuid = value.get("UUID")
            # if the uuid has been processed earlier, skip it
            if uuid in self.processed_images:
                continue

            # Extract the rest of the fields
            image_count = value.get("image_count")
            image_name = value.get("image_name")
            ground_truth = value.get("ground_truth")
            ground_truth_boxes = value.get("ground_truth_boxes") or value.get("ground_truth_bboxes")
            image_receiving_timestamp = value.get("image_receiving_timestamp")
            image_scoring_timestamp = value.get("image_scoring_timestamp")
            image_store_delete_time = value.get("image_store_delete_time", value.get("image_delete_time"))
            image_decision = value.get("image_decision")
            model_id = value.get("model_id")

            # Extract the label with max probability for event processing.
            scores = value.get("score", [])
            if scores:
                highest_score = max(scores, key=lambda x: x["probability"])
                label = highest_score["label"]
                probability = highest_score["probability"]

                # Flatten the scores component as a JSON string for storing.
                flattened_scores = json.dumps(scores)
            else:
                label = None
                probability = 0
                flattened_scores = None

            # Update experiment metrics (include GT boxes if available)
            self._update_experiment_metrics(ground_truth, scores, ground_truth_boxes)

            # Generate the event (include running experiment metrics)
            event = {
                "image_count": image_count,
                "UUID": uuid,
                "image_name": image_name,
                "ground_truth": ground_truth,
                "image_receiving_timestamp": image_receiving_timestamp,
                "image_scoring_timestamp": image_scoring_timestamp,
                "model_id": model_id,
                "label": label,
                "probability": probability,
                "image_store_delete_time": image_store_delete_time,
                "image_decision": image_decision,
                "flattened_scores": flattened_scores,
                # Running totals for the experiment at the moment of this event
                "total_images": self.metrics["total_images"],
                "total_predictions": self.metrics["total_predictions"],
                "total_ground_truth_objects": self.metrics["total_ground_truth_objects"],
                "true_positives": self.metrics["true_positives"],
                "false_positives": self.metrics["false_positives"],
                "false_negatives": self.metrics["false_negatives"],
                "precision": self.metrics["precision"],
                "recall": self.metrics["recall"],
                "f1_score": self.metrics["f1_score"],
                "mean_iou": self.metrics["mean_iou"],
                "map_50": self.metrics["map_50"],
                "map_50_95": self.metrics["map_50_95"],
            }
            self.produce_event(event)

        # shut down if the signal was received
        if shutdown_signal:
            logging.info("Shutdown signal from Oracle received... Shutting down CKN Daemon.")
            self.stop_daemon = True

    def produce_event(self, event):
        """
        Adds the device_id to the event and sends it to the CKN broker.
        """
        try:
            # add the device id
            event['device_id'] = self.device_id
            event['experiment_id'] = self.experiment_id
            event['user_id'] = self.user_id
            logging.info(f"New oracle event: {event}")
            row_json = json.dumps(event)

            # send the event
            self.producer.produce(self.topic, key=EXPERIMENT_ID, value=row_json)

            # add line to the processed set only if the produce succeeds
            self.processed_images.add(event['UUID'])
            self.producer.flush()

        except BufferError as e:
            logging.error(f"Buffer error: {e}")
        except KafkaError as e:
            logging.error(f"Kafka error: {e}")


def setup_logging():
    """
    Logs to both console and file.
    """
    log_formatter = logging.Formatter('%(asctime)s - %(message)s')

    # Create the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Logs all INFO, DEBUG and ERROR to the CKN_LOG_FILE
    file_handler = logging.FileHandler(CKN_LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # Logs INFO and ERROR to stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


def test_ckn_broker_connection(configuration, timeout=10, num_tries=5):
    """
    Checks if the CKN broker is up and running.
    """
    for i in range(num_tries):
        try:
            admin_client = AdminClient(configuration)
            # Access the topics, if not successful wait
            topics = admin_client.list_topics(timeout=timeout)
            return True
        except Exception as e:
            logging.info(f"CKN broker not available yet: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    logging.info(f"Could not connect to the CKN broker...")
    return False

if __name__ == "__main__":
    setup_logging()
    logging.basicConfig(filename=CKN_LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

    # Wait until the file exists
    while not os.path.exists(ORACLE_EVENTS_FILE):
        logging.info(f"Waiting for {ORACLE_EVENTS_FILE} to exist...")
        time.sleep(1)

    # Configure Kafka producer.
    kafka_conf = {'bootstrap.servers': KAFKA_BROKER, 'log_level': 0}

    logging.info("Connecting to the CKN broker at %s", KAFKA_BROKER)

    # Wait for CKN broker to be available
    ckn_broker_available = test_ckn_broker_connection(kafka_conf)

    if not ckn_broker_available:
        logging.info(f"Shutting down CKN Daemon due to broker not being available")
        sys.exit(0)

    # Successful connection to CKN broker
    logging.info("Successfully connected to the CKN broker at %s", KAFKA_BROKER)

    # Initialize the Kafka producer
    producer = Producer(**kafka_conf)

    # Start the event handler for listening to the file modifications.
    event_handler = OracleEventHandler(file_path=ORACLE_EVENTS_FILE, producer=producer, topic=KAFKA_TOPIC,
                                       device_id=DEVICE_ID, experiment_id=EXPERIMENT_ID, user_id=USER_ID)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(ORACLE_EVENTS_FILE), recursive=False)

    logging.info(f"Watching file: {ORACLE_EVENTS_FILE}")
    observer.start()


    try:
        while not event_handler.stop_daemon:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Stopping the oracle observer.")

    # wait for oracle thread to finish
    observer.stop()
    observer.join()
    

    if ENABLE_POWER_MONITORING != 'false':
        # Experiment is shutting down. Streaming power information before shutting down.
        power_processor = PowerProcessor(POWER_SUMMARY_FILE, producer, POWER_SUMMARY_TOPIC, EXPERIMENT_ID, POWER_SUMMARY_MAX_TRIES, POWER_SUMMARY_TIMOUT)
        power_processor.process_summary_events()
        logging.info("Power summary processed. Exiting the CKN Daemon...")
