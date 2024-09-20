import requests
import datetime
import csv
import numpy as np
import os
import time
"""
This generates the REST requests along with the images to be sent to the EDGE REST interfaces. 
"""

URL = "http://10.20.72.45:8080/predict"
SIGNAL_URL = "http:/10.20.72.45:8080/changetimestep"
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
    """
    Generates the POST request for the given set of parameters and sends it
    Args:
        filename:
        file_location:

    Returns:

    """
    start_time = datetime.datetime.now().microsecond/1000
    files = [
        ('file',
         (filename, open(file_location, 'rb'), 'image/jpeg'))
    ]
    headers = {}

    response = requests.request("POST", URL, headers=headers, data=payload, files=files)
    total_time = datetime.datetime.now().microsecond/1000 - start_time

    return response, total_time


def signal_split_end():
    """
    Generates the POST request for the given set of parameters and sends it
    Args:
        filename:
        file_location:

    Returns:

    """
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

    TOTAL_REQUESTS = 250000
    DISTINCT_IMAGES = 2000
    # max_iterations = int(TOTAL_REQUESTS/DISTINCT_IMAGES)
    max_iterations = 1

    # for i in range(max_iterations):
    #     for img_index in range(DISTINCT_IMAGES):
    #         request_index = DISTINCT_IMAGES*i + img_index
    #         response, time = send_request(images_raspi_1[img_index], image_paths[img_index], json_requests[request_index])
    #     print("{0} requests sent!".format(request_index + 1))
    #     print(response.text)
    #     # print("Total time: {}ms".format(round(time, 2)))

    for i in range(max_iterations):
        total_splits = 0
        # each split contains single time frame data
        for split_idx in range(len(split_data)):
            # convert each split to json requests
            json_requests = get_json_requests(np.asarray(split_data[split_idx]))

            # send each request along wih an image from the IMAGENET data
            for k in range(json_requests.shape[0]):
                response, r_time = send_request(images_raspi_1[k], image_paths[k], json_requests[k])

            print("Signaling split end after {} requests!".format(len(split_data[split_idx])))
            # signal_split_end()
            time.sleep(5)
            total_splits += 1

            if total_splits == 1:
                print("{0} rounds sent!".format(i + 1))
                break
        # print(response.text)
        # print("Total time: {}ms".format(round(time, 2)))


if __name__ == "__main__":
    main()
