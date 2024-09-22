import logging
import os

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv(".env")

CLOUD_URL = os.getenv("CLOUD_URL")
PREDICTIONS_CSV = os.getenv("PREDICTIONS_CSV")

# POST predictions.csv to the cloud
response = requests.post(CLOUD_URL,
                         files={'file': open(PREDICTIONS_CSV, 'rb')})

if response.status_code != 200:
    logging.error(f"Error: {response.status_code} - {response.text}")
else:
    logging.info(response.text)
