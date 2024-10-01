import csv
import json
import os
import time
from datetime import datetime

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


def process_w_qoe(file, data):
    """
    Saves the file into the uploads directory and returns the prediction and calculates and pushes the qoe parameters.
    :param file:
    :return: {prediction, compute_time}
    """
    total_start_time = time.time()

    filename = save_file(file)
    req_acc = float(data['accuracy'])
    req_delay = float(data['delay'])
    ground_truth = data['ground_truth']

    # Computation
    compute_start_time = time.time()
    preprocessed_input = pre_process(filename)
    prediction, probability = predict(preprocessed_input)
    compute_end_time = time.time()
    compute_time = compute_end_time - compute_start_time

    accuracy = int(ground_truth == prediction)
    qoe, acc_qoe, delay_qoe = process_qoe(probability, compute_time, req_delay, req_acc)
    current_model_id = model_store.get_current_model_id()

    timestamp = datetime.fromtimestamp(compute_end_time).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    qoe_event = {'server_id': SERVER_ID, 'service_id': data['service_id'], 'client_id': data['client_id'],
                 'prediction': prediction, 'compute_time': compute_time, 'probability': probability, 'total_qoe': qoe,
                 'accuracy_qoe': acc_qoe, 'delay_qoe': delay_qoe, 'req_acc': req_acc, 'req_delay': req_delay,
                 'model': current_model_id, 'timestamp': timestamp, 'accuracy': accuracy, 'ground_truth': ground_truth}

    pub_start_time = time.time()
    producer.produce(KAFKA_TOPIC, json.dumps(qoe_event), callback=delivery_report)
    producer.flush(timeout=1)
    pub_time = time.time() - pub_start_time

    total_time = time.time() - total_start_time

    qoe_event['pub_time'] = pub_time
    qoe_event['total_time'] = total_time
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
