import csv
import json
import os
import numpy as np
import requests
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv('.env')

SERVER_URL = os.getenv("SERVER_URL")
DEVICE_NAME = "raspi-3"
DATA_FILE = 'data/1_min_window_low_delay_high_rps.csv'
IMAGE_DIRECTORY = './data/images'


def get_images_in_order(dir_name, device_name):
    device_images_path = os.path.join(dir_name, device_name)
    all_images = np.sort(os.listdir(device_images_path))
    image_paths = [
        os.path.join(device_images_path, image) for image in all_images
        if not image.startswith('.')
        and os.path.isfile(os.path.join(device_images_path, image))
    ]
    final_images = [
        image for image in all_images if not image.startswith('.')
        and os.path.isfile(os.path.join(device_images_path, image))
    ]
    return np.asarray(final_images), np.asarray(image_paths)


def parse_data_file(file):
    with open(file, 'r') as f:
        data_file = list(csv.reader(f, delimiter=","))
    return np.array(data_file)


def get_device_data(data, device_name):
    return data


def get_json_requests(dataset):
    json_data = [{
        "accuracy": line[0],
        "delay": line[1],
        "server_id": line[2],
        "service_id": line[3],
        "client_id": line[4],
        "added_time": line[5]
    } for line in dataset]
    return np.asarray(json_data)


def split_data_by_timestamp(data):
    timestamp = data[0][-1]
    split_data = []
    single_split = []
    for row in data:
        if row[-1] == timestamp:
            single_split.append(row)
        else:
            split_data.append(single_split)
            single_split = [row]
            timestamp = row[-1]
    split_data.append(single_split)
    return split_data


if __name__ == "__main__":
    data_file = parse_data_file(DATA_FILE)
    device_data = get_device_data(data_file, DEVICE_NAME)
    split_data = split_data_by_timestamp(device_data)
    images_raspi_1, image_paths = get_images_in_order(IMAGE_DIRECTORY,
                                                      DEVICE_NAME)

    max_iterations = 1
    for i in range(max_iterations):
        total_splits = 0
        for split_idx in range(len(split_data)):
            json_requests = get_json_requests(np.asarray(
                split_data[split_idx]))
            for k in range(json_requests.shape[0]):
                file_path = image_paths[k]
                json_payload = json_requests[k]

                with open(file_path, 'rb') as f:
                    files = {'file': (file_path, f)}
                    # Convert JSON payload to a string and include it in form data=
                    response = requests.post(
                        SERVER_URL,
                        files=files,
                        data={'json': json.dumps(json_payload)})

                logging.info(response.status_code)

            logging.info("Signaling split end after {} requests!".format(len(split_data[split_idx])))

            total_splits += 1
            logging.info("{0} rounds sent!".format(i + 1))
            if total_splits == 1:
                break
