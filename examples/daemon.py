import os
import sys
import json
import time
import random
import logging
from datetime import datetime
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient

CKN_LOG_FILE = os.getenv('CKN_LOG_FILE', './ckn_example.log')
KAFKA_BROKER = os.getenv('CKN_KAFKA_BROKER', '127.0.0.1:9092')
KAFKA_TOPIC = os.getenv('CKN_KAFKA_TOPIC', 'oracle-events')

def setup_logging():
    """
    Logs to both console and file.
    :return:
    """
    log_formatter = logging.Formatter('%(asctime)s - %(message)s')

    # Create the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Logs all INFO, DEBUG and ERROR to the CKN_LOG_FILE
    file_handler = logging.FileHandler(CKN_LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # Logs INFO and ERROR to stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

def test_ckn_broker_connection(bootstrap_servers, timeout=10, num_tries=5):
    """
    Checks if the CKN broker is up and running.
    :param bootstrap_servers: CKN broker hosts
    :param timeout: seconds to wait for the admin client to connect
    :return: True if connection is successful, otherwise False
    """
    config = {'bootstrap.servers': bootstrap_servers}
    for i in range(num_tries):
        try:
            admin_client = AdminClient(config)
            admin_client.list_topics(timeout=timeout)  # Check if topics can be listed
            return True
        except Exception as e:
            logging.info(f"CKN broker not available yet: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    logging.error("Could not connect to the CKN broker...")
    return False

def delivery_report(err, msg):
    """
    Callback for delivery reports
    """
    if err is not None:
        logging.error("Delivery failed: %s", err)
    else:
        logging.info("Produced example event to '%s' topic", msg.topic())


if __name__ == "__main__":
    setup_logging()

    # Configure Kafka producer
    kafka_conf = {'bootstrap.servers': KAFKA_BROKER}
    logging.info("Connecting to the CKN broker at %s", KAFKA_BROKER)

    # Wait for CKN broker to be available
    if not test_ckn_broker_connection(KAFKA_BROKER):
        logging.error("Shutting down CKN Daemon due to broker not being available")
        sys.exit(1)
    logging.info("Successfully connected to the CKN broker at %s", KAFKA_BROKER)

    # Example event data
    current_timestamp = datetime.utcnow().isoformat()
    event = {
                "device_id": "example_device",
                "experiment_id": "example_experiment_{}".format(random.randint(0, 100)),
                "user_id": "example_user",
                "model_id": "example_model",
                "UUID": "example_uuid",
                "image_name": "sample_image.png",
                "ground_truth": "cat",
                "image_count": 1,
                "image_receiving_timestamp": "{}Z".format(current_timestamp),
                "image_scoring_timestamp": "{}Z".format(current_timestamp),
                "image_store_delete_time": "{}Z".format(current_timestamp),
                "image_decision": "Save",
                "flattened_scores": json.dumps(
                    [
                        {"label": "cat", "probability": 0.95},
                        {"label": "dog", "probability": 0.05},
                    ]
                ),
            }


    # Produce event to Kafka topic
    producer = Producer(**kafka_conf)
    producer.produce(KAFKA_TOPIC, json.dumps(event), callback=delivery_report)
    producer.flush(timeout=1)
