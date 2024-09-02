from confluent_kafka import Producer
import json
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
LOG = logging.getLogger(__name__)

CONF = {"bootstrap.servers": "localhost:9092"}


def delivery_report(err, msg):
    """
    Callback for delivery reports
    """
    if err is not None:
        LOG.error("Delivery failed: %s", err)
    else:
        LOG.info("Produced example event to '%s' topic", msg.topic())


if __name__ == "__main__":
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
    producer = Producer(CONF)
    producer.produce("oracle-events", json.dumps(event), callback=delivery_report)
    producer.flush(timeout=1)
