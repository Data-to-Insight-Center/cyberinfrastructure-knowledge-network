import os
import time
import csv
import logging
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def get_model_id(url: str) -> str:
    """
    Extracts and returns the model_id from the given URL string.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    uuid_list = query_params.get("id")
    if not uuid_list:
        raise ValueError("UUID not found in the URL.")
    return uuid_list[0] + '-model'

def check_file_extension(filename: str, accepted_extensions: set) -> bool:
    """Ensure the uploaded file has one of the accepted image extensions."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in accepted_extensions

async def save_file(file, upload_folder: str) -> str:
    """
    Saves the uploaded file to the given folder using a secure filename.
    Waits until the file exists before returning its path.
    """
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    os.makedirs(upload_folder, exist_ok=True)
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    # Wait until file is written to disk
    while not os.path.exists(file_path):
        time.sleep(0.1)
    return file_path

def send_model_change(new_model: str, model_producer, server_id: str):
    """
    Sends a model change event via Kafka.
    """
    model_change = {"server_id": server_id, "model": new_model}
    model_producer.send_request(model_change, key=server_id)
    logger.info(f"Model change to {new_model} sent to CKN")

def calculate_acc_qoe(req_acc: float, provided_acc: float) -> float:
    """Calculates the accuracy QoE as the ratio of provided to required accuracy."""
    return min(1.0, provided_acc / req_acc)

def calculate_delay_qoe(req_delay: float, provided_delay: float) -> float:
    """Calculates the delay QoE as the ratio of required to provided delay."""
    return min(1.0, req_delay / provided_delay)

def process_qoe(probability: float, compute_time: float, req_delay: float, req_accuracy: float):
    """
    Processes QoE values using the provided prediction accuracy (probability)
    and compute time against the required QoE constraints.
    Returns a tuple: (total_qoe, acc_qoe, delay_qoe)
    """
    acc_qoe = calculate_acc_qoe(req_accuracy, probability)
    delay_qoe = calculate_delay_qoe(req_delay, compute_time)
    total_qoe = 0.5 * acc_qoe + 0.5 * delay_qoe
    return total_qoe, acc_qoe, delay_qoe

def send_summary_event(data: dict, qoe: float, compute_time: float, probability: float,
                       prediction: str, acc_qoe: float, delay_qoe: float,
                       model_name: str, producer):
    """
    Packages the QoE event data and sends it via Kafka.
    """
    req_acc = float(data['accuracy'])
    req_delay = float(data['delay'])
    qoe_event = {
        "server_id": data['server_id'],
        "service_id": data['service_id'],
        "client_id": data['client_id'],
        "prediction": prediction,
        "compute_time": compute_time,
        "pred_accuracy": probability,
        "total_qoe": qoe,
        "accuracy_qoe": acc_qoe,
        "delay_qoe": delay_qoe,
        "req_acc": req_acc,
        "req_delay": req_delay,
        "model": model_name,
        "added_time": data['added_time']
    }
    producer.send_request(qoe_event, key="ckn-edge")
    logger.info(f"Sent summary event: {qoe_event}")
    return qoe_event

def write_perf_file(data: list, filename: str):
    """
    Appends performance data to a CSV file.
    """
    csv_columns = ['compute_time', 'pub_time', 'dnn_time']
    with open(filename, "a") as file:
        csvwriter = csv.DictWriter(file, fieldnames=csv_columns)
        csvwriter.writerows(data)

class Window:
    """
    Maintains a window of QoE events.
    """
    def __init__(self):
        self.total_acc = 0.0
        self.total_delay = 0.0
        self.num_requests = 0
        self.avg_acc = 0.0
        self.avg_delay = 0.0
        self.model_name = 'SqueezeNet'
