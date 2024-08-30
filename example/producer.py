from confluent_kafka import Producer
import json

# Configuration
conf = {"bootstrap.servers": "localhost:9092"}

# Create Producer instance
producer = Producer(conf)

# Event data
event = {
    "device_id": "device_123",
    "experiment_id": "experiment_456",
    "user_id": "user_789",
    "model_id": "model_101112",
    "UUID": "uuid_131415",
    "image_name": "sample_image.png",
    "ground_truth": "cat",
    "image_count": 1,
    "image_receiving_timestamp": "2024-08-30T12:34:56.789Z",
    "image_scoring_timestamp": "2024-08-30T12:35:56.789Z",
    "image_store_delete_time": "2024-09-30T12:34:56.789Z",
    "image_decision": "Save",
    "flattened_scores": json.dumps([
        {"label": "cat", "probability": 0.95},
        {"label": "dog", "probability": 0.05}
    ])
}

# Callback for delivery reports
def delivery_report(err, msg):
    if err is not None:
        print("Delivery failed: {}".format(err))
    else:
        print("Message delivered to {}".format(msg.topic()))


# Produce event to Kafka topic
producer.produce("oracle-events", json.dumps(event), callback=delivery_report)

# Wait up to 1 second for events to be delivered
producer.flush(timeout=1)
