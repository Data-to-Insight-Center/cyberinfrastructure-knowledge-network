import os

from flask import Flask, flash, request, redirect

from utils import get_prediction_results, check_file_extension

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


@app.route("/")
def home():
    """
    Home page.
    :return:
    """
    return "Welcome to the CKN Edge Daemon!"


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
            return get_prediction_results(file)
    return ''


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
