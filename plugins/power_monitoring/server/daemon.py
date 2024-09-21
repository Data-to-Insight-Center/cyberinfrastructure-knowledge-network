import datetime
import json
import os
import csv
from flask import Flask, request, jsonify

from utils import check_file_extension, pre_process, get_prediction_probability, save_file, process_qoe

app = Flask(__name__)
app.config['TESTING'] = True
app.config['SECRET_KEY'] = "ckn-edge-ai"

SERVER_ID = "EDGE-1"
server_list = os.getenv('CKN_KAFKA_BROKER', 'localhost:9092')
inference_topic = 'inference-qoe-test'
model_deployment_topic = 'model-deployments'

config = {
    'bootstrap.servers': server_list,
}

CSV_FILE = 'predictions.csv'
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

            # Write results to CSV file
            file_exists = os.path.isfile(CSV_FILE)

            with open(CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["start_time", "end_time", "req_delay", "req_acc", "prediction", "probability", "qoe", "acc_qoe", "delay_qoe"])
                writer.writerow([
                    start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    req_delay,
                    req_acc,
                    prediction,
                    probability,
                    qoe,
                    acc_qoe,
                    delay_qoe
                ])

            return jsonify({"prediction": prediction, "probability": probability,
                            "req_delay": req_delay, "req_acc": req_acc,
                            "qoe": qoe, "acc_qoe": acc_qoe, "delay_qoe": delay_qoe}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
