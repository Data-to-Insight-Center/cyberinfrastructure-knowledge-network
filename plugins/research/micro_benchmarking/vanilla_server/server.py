import time
from flask import Flask, request, jsonify

from model import predict, pre_process
from server_utils import save_file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

@app.route('/predict', methods=['POST'])
def qoe_predict():
    """
    Prediction endpoint.
    """

    server_receive_at = time.time()
    file = request.files['file']
    filename = save_file(file)

    image_save_at = time.time()

    preprocessed_input = pre_process(filename)
    image_preprocessed_at = time.time()

    prediction, probability = predict(preprocessed_input)
    image_predicted_at = time.time()

    return jsonify({
        "server_receive_at": server_receive_at,
        "image_save_at": image_save_at,
        "image_preprocessed_at": image_preprocessed_at,
        "image_predicted_at": image_predicted_at
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)