import csv
import json
import os
import time
import threading
from datetime import datetime

from queue import Queue
from jtop import jtop
from confluent_kafka import Producer
from dotenv import load_dotenv
from flask import Flask, flash, request, redirect, jsonify
from werkzeug.utils import secure_filename

from model import predict, pre_process, model_store

load_dotenv(".env")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
SERVER_ID = os.getenv('SERVER_ID', 'd2iedgeai3')
KAFKA_TOPIC = os.getenv('CKN_KAFKA_TOPIC', 'ckn-qoe')
KAFKA_BROKER = os.getenv('CKN_KAFKA_BROKER', '10.20.39.102:9092')
RESULTS_CSV = os.getenv('RESULTS_CSV', '/logs/results.csv')

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")

@app.route("/")
def home():
    """
    Home page.
    :return:
    """
    return "Welcome to the SqueezeNet containerized REST server!"


@app.route("/load/", methods=['GET'])
def deploy_model():
    """
    Loads a given model in the system.
    """
    model_name = request.args['model_name']
    model_store.load_model(model_name)

    # send the model changed info to the knowledge graph
    send_model_change(model_name)

    return "Model Loaded " + str(model_name)


@app.route("/changetimestep/", methods=['GET'])
def changeTimestep():
    """
    Run the changing of the model evaluation
    Returns:

    """

    # Placement of the model
    # new_model = random_placement()
    # new_model = optimal_placement(avg_acc, avg_delay)
    new_model, new_model_id = model_store.load_next_model()

    print("Model Loaded " + str(new_model))

    # send the model changed info to the knowledge graph
    send_model_change(new_model_id)
    return 'OK'


def send_model_change(new_model):
    # send the model changed info to the knowledge graph
    model_change = {"server_id": SERVER_ID, "model": new_model}
    # model_producer.send_request(model_change, key=SERVER_ID)
    print("Model change to {} sent to CKN".format(new_model))


def check_file_extension(filename):
    """
    Validates the file uploaded is an image.
    :param filename:
    :return: if the file extension is of an image or not.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


@app.route('/predict', methods=['POST'])
def qoe_predict():
    """
    Prediction endpoint with QoE parameters as input
    Allows the images to be uploaded, pre-processed and returns the result using the designated model and saves the QoE
    :return: {prediction, compute_time}
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


@app.route('/predict', methods=['POST'])
def upload_predict():
    """
    Prediction endpoint.
    Allows the images to be uploaded, pre-processed and returns the result using the designated model.
    :return: {prediction, compute_time}
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
            return process_only_file(file)
    return ''

def measure_average_power(jetson, stop_event, cpu_power_queue):
    cpu_power = 0.0
    while not stop_event.is_set():
        cpu_power += jetson.power['rail']['POM_5V_CPU']['volt']
        time.sleep(0.1)

    cpu_power_queue.put(cpu_power)


def process_w_qoe(file, data):
    """
    Processes the image with the QoE parameters.
    """
    total_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    filename = save_file(file)

    with jtop() as jetson:
        if jetson.ok():
            stop_event = threading.Event()
            cpu_power_queue = Queue()

            power_thread = threading.Thread(target=measure_average_power, args=(jetson, stop_event, cpu_power_queue))
            power_thread.start()

            try:
                compute_start_time = time.time()
                preprocessed_input = pre_process(filename)
                prediction, probability = predict(preprocessed_input)
                compute_end_time = time.time()
            finally:
                stop_event.set()
                power_thread.join()

            cpu_power = cpu_power_queue.get() if not cpu_power_queue.empty() else 0

    compute_time = compute_end_time - compute_start_time
    accuracy = int(data['ground_truth'] == prediction)
    qoe, acc_qoe, delay_qoe = process_qoe(probability, compute_time, float(data['delay']), float(data['accuracy']))
    model = model_store.get_current_model_id()

    qoe_event = {'server_id': SERVER_ID, 'service_id': data['service_id'], 'client_id': data['client_id'],
                 'ground_truth': data['ground_truth'], 'req_delay': data['delay'], 'req_acc': data['accuracy'],
                 'prediction': prediction, 'compute_time': compute_time, 'probability': probability,
                 'accuracy': accuracy, 'total_qoe': qoe, 'accuracy_qoe': acc_qoe, 'delay_qoe': delay_qoe,
                 'cpu_power': cpu_power, 'model': model, 'start_time': total_start_time,
                 'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}

    pub_start_time = time.time()
    producer.produce(KAFKA_TOPIC, json.dumps(qoe_event), callback=delivery_report)
    producer.flush(timeout=1)
    qoe_event['pub_time'] = time.time() - pub_start_time

    # Write to csv
    write_csv_file(qoe_event, RESULTS_CSV)

    return jsonify({"STATUS": "OK"})


def write_csv_file(data, filename):
    csv_columns = data.keys()
    with open(filename, "a") as file:
        csvwriter = csv.DictWriter(file, csv_columns)
        # csvwriter.writeheader()
        csvwriter.writerows([data])



def process_qoe(probability, compute_time, req_delay, req_accuracy):
    """
    Processes the QoE value for a given inference.
    :param probability:
    :param compute_time:
    :param req_delay:
    :param req_accuracy:
    :return: total QoE, accuracy QoE, delay QoE
    """
    acc_qoe = min(1.0, req_accuracy / probability)
    delay_qoe = min(1.0, req_delay / compute_time)
    return 0.5 * acc_qoe + 0.5 * delay_qoe, acc_qoe, delay_qoe



def process_only_file(file):
    """
    Saves the file into the uploads directory and returns the prediction.
    :param file:
    :return: {prediction, compute_time}
    """
    filename = save_file(file)

    start_time = time.time()
    # pre-processing the image
    preprocessed_input = pre_process(filename)
    # prediction on the pre-processed image
    prediction, probability = predict(preprocessed_input)
    compute_time = time.time() - start_time

    result = {'prediction': prediction, "compute_time": compute_time, "probability": probability}
    return jsonify(result)


def save_file(file):
    """
    Saves a given file and waits for it to be saved before returning.
    :param file:
    :return: relative file path of the image saved.
    """
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    while not os.path.exists(file_path):
        time.sleep(0.1)
    return file_path


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
