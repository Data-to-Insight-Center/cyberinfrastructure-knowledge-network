import os
import time
import csv
import requests
from jtop import jtop
import logging

from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv(".env")

CLOUD_URL = os.getenv("CLOUD_URL")
POWER_CSV = os.getenv("POWER_CSV")

duration = 250  # seconds
start_time = time.time()

# Open the CSV file in append mode
with open(POWER_CSV, 'a', newline='') as f:
    csv_writer = csv.writer(f)

    # Write the header only if the file is empty
    if os.stat(POWER_CSV).st_size == 0:
        csv_writer.writerow(['timestamp',
        'cpu_volt', 'cpu_curr', 'cpu_power', 'cpu_avg_power',
        'gpu_volt', 'gpu_curr', 'gpu_power', 'gpu_avg_power',
        'total_volt', 'total_curr', 'total_power', 'total_avg_power'])

    with jtop() as jetson:
        while jetson.ok():
            # Check if the duration has passed
            elapsed_time = time.time() - start_time
            if elapsed_time > duration:
                print(f"written to {POWER_CSV}")
                break

            # Get the current timestamp
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

            # Extract power details for CPU and GPU from 'jetson.power'
            cpu_power = jetson.power['rail']['POM_5V_CPU']
            gpu_power = jetson.power['rail']['POM_5V_GPU']
            total_power = jetson.power['tot']

            # Create log entry for CSV
            log_entry = [
                timestamp,
                cpu_power['volt'], cpu_power['curr'], cpu_power['power'], cpu_power['avg'],
                gpu_power['volt'], gpu_power['curr'], gpu_power['power'], gpu_power['avg'],
                total_power['volt'], total_power['curr'], total_power['power'], total_power['avg']
            ]

            csv_writer.writerow(log_entry)
            f.flush()

            time.sleep(1)


    # POST predictions.csv to the cloud
    response = requests.post(f"{CLOUD_URL}/upload_power", files={'file': open(POWER_CSV, 'rb')})

    if response.status_code != 200:
        logging.error(f"Error: {response.status_code} - {response.text}")
    else:
        logging.info(response.text)
