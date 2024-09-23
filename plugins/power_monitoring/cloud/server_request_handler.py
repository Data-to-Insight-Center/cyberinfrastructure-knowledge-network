from flask import Flask, request, jsonify
import os
import csv
from dotenv import load_dotenv

load_dotenv('.env')
app = Flask(__name__)

# Directory to save uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL = os.getenv("MODEL")
PREDICTIONS_CSV=f'{MODEL}_predictions.csv'

@app.route('/upload_predictions', methods=['POST'])
def upload_predictions():
    # Extract JSON data
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    # Extract values from JSON
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    req_delay = data.get('req_delay')
    req_acc = data.get('req_acc')
    prediction = data.get('prediction')
    probability = data.get('probability')
    qoe = data.get('qoe')
    acc_qoe = data.get('acc_qoe')
    delay_qoe = data.get('delay_qoe')

    # Open the CSV file and write the data
    with open(PREDICTIONS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        # Write header if file is empty
        if os.stat(PREDICTIONS_CSV).st_size == 0:
            writer.writerow([
                "start_time", "end_time", "req_delay", "req_acc",
                "prediction", "probability", "qoe", "acc_qoe",
                "delay_qoe"
            ])
        writer.writerow([start_time, end_time, req_delay, req_acc, prediction, probability, qoe, acc_qoe, delay_qoe])

    return 'Data written to CSV', 200

@app.route('/upload_power', methods=['POST'])
def upload_power():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']

    if file.filename == '':
        return 'No selected file', 400

    # Save the file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    return 'File uploaded successfully', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)