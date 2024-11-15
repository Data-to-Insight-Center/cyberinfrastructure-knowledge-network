import json
import os
import threading
import time
import uuid
from datetime import datetime
from queue import Queue

from confluent_kafka import Producer
from dotenv import load_dotenv
from flask import Flask, flash, request, redirect, jsonify
# from jtop import jtop

from model import predict, pre_process, model_store
from server_utils import save_file, process_qoe, check_file_extension

load_dotenv(".env")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
SERVER_ID = os.getenv('SERVER_ID', 'd2iedgeai3')

KAFKA_BROKER = os.getenv('CKN_KAFKA_BROKER', '149.165.170.250:9092')

RAW_EVENT_TOPIC = os.getenv('RAW_EVENT_TOPIC', 'ckn_raw')
START_DEPLOYMENT_TOPIC = os.getenv('START_DEPLOYMENT_TOPIC', 'ckn_start_deployment')
END_DEPLOYMENT_TOPIC = os.getenv('END_DEPLOYMENT_TOPIC', 'ckn_end_deployment')

producer = Producer({'bootstrap.servers': KAFKA_BROKER})
previous_deployment_id = None
last_model_id = None
deployment_id = None

def delivery_report(err, msg):
    """
    Delivery report callback function.
    :param err: Delivery error (if any).
    :param msg: Message object.
    """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

@app.route("/")
def home():
    """
    Home endpoint.
    """
    return "Welcome to the SqueezeNet containerized REST vanilla_server!"


@app.route("/load/", methods=['GET'])
def deploy_model():
    """
    Model deployment endpoint.
    """
    model_name = request.args['model_name']
    model_store.load_model(model_name)

    # send the model changed info to the knowledge graph
    send_model_change(model_name)

    return "Model Loaded " + str(model_name)


@app.route("/changetimestep/", methods=['GET'])
def changeTimestep():
    """
    Change the timestep of the model
    """
    new_model, new_model_id = model_store.load_next_model()
    print("Model Loaded " + str(new_model))
    send_model_change(new_model_id)
    return 'OK'

def send_model_change(new_model_id):
    """
    Send the model change event to the Kafka topic
    """
    global previous_deployment_id, deployment_id

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    # Prepare the start event with the current deployment ID
    start_event = {
        "server_id": SERVER_ID,
        "service_id": "imagenet_image_classification",
        "device_id": device_id,
        "deployment_id": deployment_id,
        "status": "RUNNING",
        "model_id": new_model_id,
        "start_time": timestamp
    }
    producer.produce(START_DEPLOYMENT_TOPIC, json.dumps(start_event), callback=delivery_report, key=deployment_id)
    producer.flush(timeout=1)

    # Produce an end event for the previous deployment if it exists
    if previous_deployment_id:
        end_event = {
            "deployment_id": previous_deployment_id,
            "status": "STOPPED",
            "end_time": timestamp
        }
        producer.produce(END_DEPLOYMENT_TOPIC, json.dumps(end_event), callback=delivery_report, key=previous_deployment_id)
        producer.flush(timeout=1)

    # Update the previous_deployment_id with the current deployment_id
    previous_deployment_id = deployment_id


@app.route('/predict', methods=['POST'])
def qoe_predict():
    """
    Prediction endpoint.
    """
    if request.method == 'POST':
        # if the request contains a file or not
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        # if the file field is empty
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and check_file_extension(file.filename):
            # getting the QoE constraints
            data = request.form
        return process_w_qoe(file, data)

    return ''


def measure_average_power(jetson, stop_event, cpu_power_queue, gpu_power_queue, tot_power_queue):
    """
    Measure the average power consumption of the CPU, GPU, and the total power consumption.
    """
    cpu_power = 0.0
    gpu_power = 0.0
    total_power = 0.0

    while not stop_event.is_set():
        cpu_power += jetson.power['rail']['POM_5V_CPU']['volt']
        gpu_power += jetson.power['rail']['POM_5V_GPU']['volt']
        total_power += jetson.power['tot']['power']
        time.sleep(0.1)

    cpu_power_queue.put(cpu_power)
    gpu_power_queue.put(gpu_power)
    tot_power_queue.put(total_power)


def process_w_qoe(file, data):
    """
    Process the request with QoE constraints.
    """
    global last_model_id, deployment_id, device_id

    total_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    filename = save_file(file)

    # with jtop() as jetson:
    #     if jetson.ok():
    #         stop_event = threading.Event()
    cpu_power_queue = Queue()
    gpu_power_queue = Queue()
    tot_power_queue = Queue()
    #
    #         power_thread = threading.Thread(target=measure_average_power, args=(jetson, stop_event, cpu_power_queue, gpu_power_queue, tot_power_queue))
    #         power_thread.start()
    #
    #         try:
    preprocessed_input = pre_process(filename)
    compute_start_time = time.time()
    prediction, probability = predict(preprocessed_input)
    compute_end_time = time.time()
    #         finally:
    #             stop_event.set()
    #             power_thread.join()
    #
    cpu_power = cpu_power_queue.get() if not cpu_power_queue.empty() else 0
    gpu_power = gpu_power_queue.get() if not gpu_power_queue.empty() else 0
    total_power = tot_power_queue.get() if not tot_power_queue.empty() else 0

    compute_time = compute_end_time - compute_start_time
    device_id = data['client_id']
    accuracy = int(data['ground_truth'] == prediction)
    req_delay, req_acc = float(data['delay']), float(data['accuracy'])
    qoe, acc_qoe, delay_qoe = process_qoe(probability, compute_time, req_delay, req_acc)
    current_model_id = model_store.get_current_model_id()

    # Check if the model has changed
    if current_model_id != last_model_id:
        deployment_id = str(uuid.uuid4())  # Generate new deployment_id
        last_model_id = current_model_id   # Update last_model_id

    payload = {'timestamp': total_start_time, 'server_id': SERVER_ID, 'model_id': current_model_id,
               'deployment_id': deployment_id, 'service_id': data['service_id'], 'device_id': device_id,
               'ground_truth': data['ground_truth'], 'req_delay': req_delay, 'req_acc': req_acc,
               'prediction': prediction, 'compute_time': compute_time, 'probability': probability,
               'accuracy': accuracy, 'total_qoe': qoe, 'accuracy_qoe': acc_qoe, 'delay_qoe': delay_qoe,
               'cpu_power': cpu_power, 'gpu_power': gpu_power, 'total_power': total_power}

    schema = {
        "type": "struct",
        "fields": [
            {"type":"string", "optional": True, "field": "timestamp"},
            {"type": "string", "optional": True, "field": "server_id"},
            {"type":"string",  "optional": True, "field": "model_id"},
            {"type": "string", "optional": True, "field": "deployment_id"},
            {"type": "string", "optional": True, "field": "service_id"},
            {"type": "string", "optional": True, "field": "device_id"},
            {"type": "string", "optional": True, "field": "ground_truth"},
            {"type": "float", "optional": True, "field": "req_delay"},
            {"type": "float", "optional": True, "field": "req_acc"},
            {"type": "string", "optional": True, "field": "prediction"},
            {"type": "float", "optional": True, "field": "compute_time"},
            {"type": "float", "optional": True, "field": "probability"},
            {"type": "int32", "optional": True, "field": "accuracy"},
            {"type": "float", "optional": True, "field": "total_qoe"},
            {"type": "float", "optional": True, "field": "accuracy_qoe"},
            {"type": "float", "optional": True, "field": "delay_qoe"},
            {"type": "float", "optional": True, "field": "cpu_power"},
            {"type": "float", "optional": True, "field": "gpu_power"},
            {"type": "float", "optional": True, "field": "total_power"}
        ],
        "optional": False,
        "name": "d2i"
    }

    producer.produce(RAW_EVENT_TOPIC, json.dumps({'schema': schema, 'payload': payload}), callback=delivery_report, key=payload["device_id"])
    producer.flush(timeout=1)
    return jsonify({"STATUS": "OK"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)