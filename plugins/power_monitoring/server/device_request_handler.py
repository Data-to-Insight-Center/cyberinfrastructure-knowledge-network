import datetime
import json
import os
from flask import Flask, request, jsonify
import logging
import requests
from utils import check_file_extension, pre_process, get_prediction_probability, save_file, process_qoe
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv(".env")

CLOUD_URL = os.getenv("CLOUD_URL")  # Ensure this is set in your .env file
app = Flask(__name__)

@app.route("/")
def home():
    """
    Home page.
    :return:
    """
    return "Welcome to the CKN Edge Daemon!"

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file and check_file_extension(file.filename):
            filename = save_file(file)
            start_time = datetime.datetime.now()

            # Preprocess and Predict
            preprocessed_input = pre_process(filename)
            prediction, probability = get_prediction_probability(preprocessed_input)

            end_time = datetime.datetime.now()
            compute_time = end_time - start_time

            # Retrieve JSON data from form field
            json_data = request.form.get('json')
            if json_data is None:
                return jsonify({"error": "No JSON data provided"}), 400

            try:
                data = json.loads(json_data)
                req_acc = float(data['accuracy'])
                req_delay = float(data['delay'])
            except (KeyError, ValueError) as e:
                return jsonify({"error": f"Invalid or missing data: {str(e)}"}), 400

            qoe, acc_qoe, delay_qoe = process_qoe(probability, compute_time, req_delay, req_acc)

            # Prepare data for POST request
            post_data = {
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "req_delay": req_delay,
                "req_acc": req_acc,
                "prediction": prediction,
                "probability": probability,
                "qoe": qoe,
                "acc_qoe": acc_qoe,
                "delay_qoe": delay_qoe
            }

            # Send POST request to cloud endpoint
            try:
                response = requests.post(f"{CLOUD_URL}/upload_predictions", json=post_data)
                response.raise_for_status()  # Raise an error for bad responses
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to send data to cloud: {e}")
                return jsonify({"error": "Failed to send data to cloud"}), 500

            return 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)