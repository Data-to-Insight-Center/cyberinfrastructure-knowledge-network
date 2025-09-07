import requests
import datetime
import csv
import numpy as np
import os
import time
from dotenv import load_dotenv

load_dotenv(".env")
"""
This generates the REST requests along with the images to be sent to the EDGE REST interfaces. 
"""

SERVER_ADDRESS = os.getenv("SERVER_ADDRESS", "http://127.0.0.1:5003")
DEVICE_NAME = os.getenv("DEVICE_NAME")
DATA_FILE = 'data/1_min_window_low_delay_high_rps.csv'
IMAGE_DIRECTORY = './data/images'
IMAGES = []


def get_images_in_order(dir_name):
    """
    Returns the images for the device in order
    Returns:

    """
    all_images = np.sort(os.listdir(dir_name))
    # get the absolute path for each image
    image_paths = []
    final_images = []
    for image in all_images:
        image_path = os.path.join(dir_name, image)
        if not image.startswith('.') and os.path.isfile(image_path):
            image_paths.append(image_path)
            final_images.append(image)

    return np.asarray(final_images), np.asarray(image_paths)


def parse_data_file(file):
    """
    Given the input file, parses it and returns a numpy array.
    Args:
        file:

    Returns:

    """
    with open(file, 'r') as f:
        data_file = list(csv.reader(f, delimiter=","))

    data = np.array(data_file)
    return data


def get_json_requests(dataset):
  """
  Given a set of requests, converts them into json format and returns the dataset
  Args:
      dataset:

  Returns:
  """
  json_data = []
  for line in dataset:
    json_data.append({"accuracy": line[0], "delay": line[1], "server_id": line[2], "service_id": line[3], "client_id": line[4], "added_time": line[5]})
  return np.asarray(json_data)


def send_request(filename, file_location, payload, URL):
    start_time = datetime.datetime.now().microsecond / 1000
    files = [
        ('file',
         (filename, open(file_location, 'rb'), 'image/jpeg'))
    ]
    headers = {}

    response = requests.request("POST", URL, headers=headers, data=payload, files=files)
    total_time = datetime.datetime.now().microsecond / 1000 - start_time

    return response, total_time


def signal_split_end(SIGNAL_URL):
    headers = {}

    response = requests.request("GET", SIGNAL_URL, headers=headers)

    return response


def split_data_by_timestamp(data):
    timestamp = data[0][-1]
    split_data = []
    single_split = []
    for row in data:
        if row[-1] == timestamp:
            single_split.append(row)
        else:
            split_data.append(single_split)
            single_split = []
            single_split.append(row)
            timestamp = row[-1]
    split_data.append(single_split)
    return split_data


def main(SERVER_ADDRESS):
    URL = f"{SERVER_ADDRESS}/predict"
    SIGNAL_URL = f"{SERVER_ADDRESS}/changetimestep"
    DATA_FILE = 'data/1_min_window_low_delay_high_rps.csv'
    IMAGE_DIRECTORY = './data/images'

    device_data = parse_data_file(DATA_FILE)
    split_data = split_data_by_timestamp(device_data)

    # get the input images
    images_raspi_1, image_paths = get_images_in_order(IMAGE_DIRECTORY)
    max_iterations = 1

    for i in range(max_iterations):
        total_splits = 0
        # each split contains single time frame data
        for split_idx in range(len(split_data)):
            # convert each split to json requests
            json_requests = get_json_requests(np.asarray(split_data[split_idx]))
            requests_count = json_requests.shape[0]

            if requests_count < 10:
                continue
            requests_count = 10

            # send each request along wih an image from the IMAGENET data
            for k in range(requests_count):
                filename, file_location, payload = images_raspi_1[k], image_paths[k], json_requests[k]

                payload['ground_truth'] = filename.split('.')[0]
                response, r_time = send_request(filename, file_location, payload, URL)

            print("Signaling split end after {} requests!".format(requests_count))
            signal_split_end(SIGNAL_URL)
            time.sleep(5)
            total_splits += 1

            if total_splits == 10:
                print("{0} rounds sent!".format(i + 1))
                break


if __name__ == "__main__":
    main("http://127.0.0.1:5003")
