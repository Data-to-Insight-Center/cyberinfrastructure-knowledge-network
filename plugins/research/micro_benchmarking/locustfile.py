from locust import HttpUser, task, between
import numpy as np
import os
import time

# Define file and payload details for the POST request
filename = np.str_("abacus.jpg")
file_location = "/plugins/research/micro_benchmarking/abacus.jpg"
payload = {
    "accuracy": np.str_("0.849"),
    "delay": np.str_("0.051"),
    "server_id": np.str_("EDGE-1"),
    "service_id": np.str_("imagenet_image_classification"),
    "client_id": np.str_("raspi-1"),
    "added_time": np.str_("03-04-2023 15:13:05"),
    "ground_truth": "abacus"  # Adding ground_truth if required
}

class QoEPredictUser(HttpUser):
    host = "http://149.165.174.52:8080"

    @task
    def send_qoe_predict_request(self):
        # Open the image file in binary mode
        with open(file_location, 'rb') as file:
            files = {
                'file': (filename, file, 'image/jpeg')
            }

            # Use the with block to catch the response and check its status
            with self.client.post("/predict", data=payload, files=files, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()  # Mark the request as successful
                else:
                    response.failure(f"Failed with status code: {response.status_code}")
