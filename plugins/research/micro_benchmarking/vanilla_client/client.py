import time
import numpy as np
import requests
import csv
import os

if __name__ == '__main__':

    host = "http://149.165.174.52:8080"

    filename = np.str_("abacus.jpg")
    file_location = "abacus.jpg"
    payload = {
        "accuracy": np.str_("0.849"),
        "delay": np.str_("0.051"),
        "server_id": np.str_("EDGE-1"),
        "service_id": np.str_("imagenet_image_classification"),
        "client_id": np.str_("raspi-1"),
        "added_time": np.str_("03-04-2023 15:13:05"),
        "ground_truth": "abacus"
    }

    # Ensure the results directory exists
    os.makedirs("results", exist_ok=True)

    # CSV file setup
    csv_filename = "results/image_classification_times.csv"
    file_exists = os.path.isfile(csv_filename)

    fieldnames = ["client_send_at", "server_receive_at",
                  "image_preprocessed_at", "image_predicted_at",
                  "image_save_at", "client_receive_at"]

    # Initialize lists to store timing data for averaging later
    client_send_times = []
    server_receive_times = []
    image_preprocessed_times = []
    image_predicted_times = []
    image_save_times = []
    client_receive_times = []

    # Open CSV file for appending data
    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header only if file is new
        if not file_exists:
            writer.writeheader()

        # Loop through 100 requests
        for i in range(100):
            # Open the image file in binary mode
            with open(file_location, 'rb') as file:
                files = {
                    'file': (filename, file, 'image/jpeg')
                }

                client_send_at = time.time()
                response = requests.post(f"{host}/predict", data=payload, files=files)
                response = response.json()

                # Extracting timestamps from the server's response
                image_predicted_at = float(response["image_predicted_at"])
                image_preprocessed_at = float(response["image_preprocessed_at"])
                image_save_at = float(response["image_save_at"])
                server_receive_at = float(response["server_receive_at"])
                client_receive_at = time.time()

                # Append individual times to lists for averaging later
                client_send_times.append(client_send_at)
                server_receive_times.append(server_receive_at)
                image_preprocessed_times.append(image_preprocessed_at)
                image_predicted_times.append(image_predicted_at)
                image_save_times.append(image_save_at)
                client_receive_times.append(client_receive_at)

                # Prepare data for CSV row
                data = {
                    "client_send_at": client_send_at,
                    "server_receive_at": server_receive_at,
                    "image_preprocessed_at": image_preprocessed_at,
                    "image_predicted_at": image_predicted_at,
                    "image_save_at": image_save_at,
                    "client_receive_at": client_receive_at
                }

                # Write individual request data to CSV
                writer.writerow(data)

            print(f"Request {i+1} completed.")

    # Calculate averages after all requests are done
    avg_client_send_time = sum(client_send_times) / len(client_send_times)
    avg_server_receive_time = sum(server_receive_times) / len(server_receive_times)
    avg_image_preprocessed_time = sum(image_preprocessed_times) / len(image_preprocessed_times)
    avg_image_predicted_time = sum(image_predicted_times) / len(image_predicted_times)
    avg_image_save_time = sum(image_save_times) / len(image_save_times)
    avg_client_receive_time = sum(client_receive_times) / len(client_receive_times)

    # Print average times to console
    print("\nAverage Times for 100 Requests:")
    print(f"Average client_send_time: {avg_client_send_time}")
    print(f"Average server_receive_time: {avg_server_receive_time}")
    print(f"Average image_preprocessed_time: {avg_image_preprocessed_time}")
    print(f"Average image_predicted_time: {avg_image_predicted_time}")
    print(f"Average image_save_time: {avg_image_save_time}")
    print(f"Average client_receive_time: {avg_client_receive_time}")

    # Optionally, write averages to a separate CSV or append them to the same file.