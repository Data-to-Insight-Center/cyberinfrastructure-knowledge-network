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

SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")
URL = f"{SERVER_ADDRESS}/predict"
SIGNAL_URL = f"{SERVER_ADDRESS}/changetimestep"
DEVICE_NAME = "raspi-3"
DATA_FILE = 'data/1_min_window_low_delay_high_rps.csv'
IMAGE_DIRECTORY = './data/images'
IMAGES = []


def get_images_in_order(dir_name, device_name):
    """
    Returns the images for the device in order
    Returns:

    """
    device_images_path = os.path.join(dir_name, device_name)
    # sort to maintain the order
    all_images = np.sort(os.listdir(device_images_path))
    # get the absolute path for each image
    image_paths = []
    final_images = []
    for image in all_images:
        image_path = os.path.join(device_images_path, image)
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


def get_device_data(data, device_name):
    """
    Filters the given dataset by device name and returns the corresponding data
    Args:
        data:
        device_name:

    Returns:

    """
    return data
    # return data[np.where(data[:, 4] == device_name)]


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


def send_request(filename, file_location, payload):
    start_time = datetime.datetime.now().microsecond/1000
    files = [
        ('file',
         (filename, open(file_location, 'rb'), 'image/jpeg'))
    ]
    headers = {}

    # if 'cat' in filename, ground_truth = 'cat', if dog in filename, ground_truth = 'dog'
    ground_truth = 'cat' if 'cat' in filename else 'dog'

    # add ground truth to the payload
    payload['ground_truth'] = ground_truth

    response = requests.request("POST", URL, headers=headers, data=payload, files=files)
    total_time = datetime.datetime.now().microsecond/1000 - start_time

    return response, total_time


def signal_split_end():
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


def main():
    """
    Run the generator for a given device
    Returns:

    """
    # get the device input data
    data_file = parse_data_file(DATA_FILE)
    device_data = get_device_data(data_file, DEVICE_NAME)
    # split data by timestamp
    split_data = split_data_by_timestamp(device_data)

    # convert to json requests
    # json_requests = get_json_requests(device_data)


    # get the input images
    images_raspi_1, image_paths = get_images_in_order(IMAGE_DIRECTORY, DEVICE_NAME)
    max_iterations = 1

    for i in range(max_iterations):
        total_splits = 0
        # each split contains single time frame data
        for split_idx in range(len(split_data)):
            # convert each split to json requests
            json_requests = get_json_requests(np.asarray(split_data[split_idx]))

            # send each request along wih an image from the IMAGENET data
            for k in range(json_requests.shape[0]):
                response, r_time = send_request(images_raspi_1[k], image_paths[k], json_requests[k])
                break

            print("Signaling split end after {} requests!".format(len(split_data[split_idx])))
            signal_split_end()
            time.sleep(5)
            total_splits += 1

            if total_splits == 20:
                print("{0} rounds sent!".format(i + 1))
                break

if __name__ == "__main__":
    main()