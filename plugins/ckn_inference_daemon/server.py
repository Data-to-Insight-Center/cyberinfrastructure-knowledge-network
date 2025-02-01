import os
import time
import logging
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from model import predict, pre_process, load_model
from plugins.ckn_inference_daemon.message_broker.ingester import KafkaIngester
# from ckn.src.daemon.controller import predictive_placement
# from ckn.src.messagebroker.kafka_ingester import KafkaIngester

# Import utility functions and Window class
from util import (
    check_file_extension, save_file, send_model_change, process_qoe,
    send_summary_event, write_perf_file, Window
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read configuration from environment variables
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
ACCEPTED_EXTENSIONS = set(os.getenv("ACCEPTED_EXTENSIONS", "png,jpg,jpeg").split(","))
EDGE_ID = os.getenv("SERVER_ID", "EDGE-1")
SERVER_LIST = os.getenv("SERVER_LIST", "localhost:9092")
INFERENCE_TOPIC = os.getenv("INFERENCE_TOPIC", "edge-inference")
# PERF_FILENAME = os.getenv("PERF_FILENAME", "./timers.csv")
# INFERENCE_QOE_TOPIC = os.getenv("INFERENCE_QOE_TOPIC", "edge-inference-qoe")
# MODEL_DEPLOYMENT_TOPIC = os.getenv("MODEL_DEPLOYMENT_TOPIC", "model-deployments")

# Instantiate Kafka producers
# edge_pred_producer = KafkaIngester(SERVER_LIST, INFERENCE_TOPIC)
# producer = KafkaIngester(SERVER_LIST, INFERENCE_QOE_TOPIC)
# model_producer = KafkaIngester(SERVER_LIST, MODEL_DEPLOYMENT_TOPIC)

# Global window objects for tracking QoE metrics
# prev_window = Window()
# current_window = Window()

app = FastAPI()


@app.post("/predict")
async def predict_endpoint(
    file: UploadFile = File(...),
    label: str = Form(None)
):
    """
    Prediction endpoint.
    Accepts an image file and an optional label.
    Preprocesses the image, runs the prediction, and returns the result along with computation time.
    If a label is provided, calculates accuracy as 1.0 if the predicted label matches the input label, else 0.0.
    """
    if not check_file_extension(file.filename, ACCEPTED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Invalid file extension")

    file_path = await save_file(file, UPLOAD_FOLDER)
    start_time = time.time()

    # predict for the given image
    preprocessed_input = pre_process(file_path)
    prediction, probability = predict(preprocessed_input)

    compute_time = time.time() - start_time

    result = {
        "prediction": prediction,
        "compute_time": compute_time,
        "probability": probability
    }

    # If label is provided, compare it to the predicted label to calculate accuracy.
    if label is not None:
        result["accuracy"] = 1.0 if prediction.lower() == label.lower() else 0.0

    # send event to edge-predictions topic
    edge_prediction_event = {
        "server_id": EDGE_ID,
        "prediction": prediction,
        "probability": probability,
        "compute_time": compute_time
    }
    # edge_pred_producer.send_request(edge_prediction_event, key=EDGE_ID)

    return JSONResponse(content=result)


# @app.post("/process_w_qoe")
# async def process_w_qoe_endpoint(
#         file: UploadFile = File(...),
#         accuracy: float = Form(...),
#         delay: float = Form(...),
#         server_id: str = Form(...),
#         service_id: str = Form(...),
#         client_id: str = Form(...),
#         added_time: str = Form(...)
# ):
#     """
#     Endpoint that processes an image file along with QoE parameters.
#     This endpoint:
#       - Saves the file and preprocesses it.
#       - Runs the prediction.
#       - Measures compute time.
#       - Processes QoE values.
#       - Sends a QoE summary event via Kafka.
#       - Updates the current window metrics.
#       - Writes performance data to a CSV file.
#     """
#     if not check_file_extension(file.filename, ACCEPTED_EXTENSIONS):
#         raise HTTPException(status_code=400, detail="Invalid file extension")
#
#     file_path = await save_file(file, UPLOAD_FOLDER)
#     start_time = time.time()
#     preprocessed_input = pre_process(file_path)
#     prediction, probability = predict(preprocessed_input)
#     compute_time = time.time() - start_time
#
#     total_qoe, acc_qoe, delay_qoe = process_qoe(probability, compute_time, delay, accuracy)
#
#     result = {
#         "prediction": prediction,
#         "compute_time": compute_time,
#         "probability": probability,
#         "QoE": total_qoe,
#         "Acc_QoE": acc_qoe,
#         "Delay_QoE": delay_qoe,
#         "model": current_window.model_name
#     }
#
#     # Prepare data for the summary event
#     data = {
#         "accuracy": str(accuracy),
#         "delay": str(delay),
#         "server_id": server_id,
#         "service_id": service_id,
#         "client_id": client_id,
#         "added_time": added_time
#     }
#
#     pub_timer = time.time()
#     send_summary_event(
#         data, total_qoe, compute_time, probability, prediction,
#         acc_qoe, delay_qoe, current_window.model_name, producer
#     )
#     pub_time = time.time() - pub_timer
#
#     # Update current window metrics
#     current_window.total_acc += accuracy
#     current_window.total_delay += delay
#     current_window.num_requests += 1
#
#     predict_timer = time.time()
#     dnn_time = time.time() - predict_timer
#
#     write_perf_file([{
#         'compute_time': compute_time,
#         'pub_time': pub_time,
#         'dnn_time': dnn_time
#     }], PERF_FILENAME)
#
#     return JSONResponse(content=result)

#
# @app.get("/changemodel")
# def change_model():
#     """
#     Change model endpoint.
#     Calculates average QoE from the current window,
#     selects a new model using predictive placement,
#     loads the new model, sends a model change event via Kafka,
#     and resets the current window.
#     """
#     if current_window.num_requests == 0:
#         return JSONResponse(
#             content={"error": "No requests processed in the current window."},
#             status_code=400
#         )
#
#     avg_acc = current_window.total_acc / current_window.num_requests
#     avg_delay = current_window.total_delay / current_window.num_requests
#     current_window.avg_acc = avg_acc
#     current_window.avg_delay = avg_delay
#     logger.info(f"Avg Acc: {avg_acc}\tAvg Delay: {avg_delay}\tTotal requests: {current_window.num_requests}")
#
#     new_model = predictive_placement(prev_window, current_window)
#     load_model(new_model)
#     current_window.model_name = new_model
#     logger.info(f"Model Loaded: {new_model}")
#
#     send_model_change(new_model, model_producer, EDGE_ID)
#
#     prev_window.avg_acc = avg_acc
#     prev_window.avg_delay = avg_delay
#     current_window.total_acc = 0.0
#     current_window.total_delay = 0.0
#     current_window.num_requests = 0
#
#     return {"message": "Model changed", "new_model": new_model}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
