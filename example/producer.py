from confluent_kafka import Producer
import json

# Configuration
conf = {"bootstrap.servers": "localhost:9092"}

# Create Producer instance
producer = Producer(conf)

# Event data
event = {
    "user_id": "example_user",
    "experiment_id": "example_experiment",
    "experiment_data": {
        "user_id": "example_user",
        "experiment_id": "example_experiment",
        "device_id": "example_device",
        "image_count": "image_count",
        "UUID": "uuid",
        "image_name": "image_name",
        "ground_truth": "ground_truth",
        "image_receiving_timestamp": "image_receiving_timestamp",
        "image_scoring_timestamp": "image_scoring_timestamp",
        "model_id": "model_id",
        "label": "label",
        "probability": "probability",
        "image_store_delete_time": "image_store_delete_time",
        "image_decision": "image_decision",
        "flattened_scores": "flattened_scores",
    },
}


# Callback for delivery reports
def delivery_report(err, msg):
    if err is not None:
        print("Delivery failed: {}".format(err))
    else:
        print("Message delivered to {} [{}]".format(msg.topic(), msg.partition()))


# Produce event to Kafka topic
producer.produce("oracle-events", json.dumps(event), callback=delivery_report)

# Wait up to 1 second for events to be delivered
producer.flush(timeout=1)
