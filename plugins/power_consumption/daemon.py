import logging
import os
import time
from json import dumps

import connexion
from flask import Flask, flash, request, redirect, jsonify
from kafka import KafkaProducer

from model import predict, pre_process, load_model


class KafkaIngester:
    """
    Library class for ingesting information into CKN through Kafka.
    """

    def __init__(self, server_list, ckn_topic):
        self.producer = KafkaProducer(bootstrap_servers=[server_list],
                                      value_serializer=lambda x: dumps(x).encode('utf-8'))

        self.topic = ckn_topic

    def send_request(self, request, key=None):
        """
        Sends requests to CKN
        """
        self.producer.send(topic=self.topic, value=request, key=key.encode())

    def send_qoe(self, request):
        """
        Sends QoE events to CKN
        """
        self.producer.send(topic=self.topic, value=request)


app = connexion.App(__name__, specification_dir="./")
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
ACCEPTED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TESTING'] = True
app.config['SECRET_KEY'] = "ckn-edge-ai"

SERVER_ID = "EDGE-1"
server_list = os.getenv('CKN_KAFKA_BROKER', 'localhost:9092')
inference_topic = 'inference-qoe-test'
model_deployment_topic = 'model-deployments'

producer = KafkaIngester(server_list, inference_topic)
model_producer = KafkaIngester(server_list, model_deployment_topic)


class Window:
    total_acc = 0
    total_delay = 0
    num_requests = 0
    avg_acc = 0
    avg_delay = 0
    model_name = 'SqueezeNet'


prev_window = Window()
current_window = Window()


@app.route("/")
def home():
    """
    Home page.
    :return:
    """
    return "Welcome to the containerized REST server!"


@app.route("/load/", methods=['GET'])
def deploy_model():
    """
    Loads a given model in the system.
    """
    model_name = request.args['model_name']
    load_model(model_name)
    current_window.model_name = model_name

    # send the model changed info to the knowledge graph
    send_model_change(model_name)

    return "Model Loaded " + str(model_name)


def send_model_change(new_model):
    # send the model changed info to the knowledge graph
    model_change = {"server_id": SERVER_ID, "model": new_model}
    model_producer.send_request(model_change, key=SERVER_ID)
    print("Model change to {} sent to CKN".format(new_model))


def check_file_extension(filename):
    """
    Validates the file uploaded is an image.
    :param filename:
    :return: if the file extension is of an image or not.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ACCEPTED_EXTENSIONS


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
    app.run(host="0.0.0.0", port=8080, debug=True)
