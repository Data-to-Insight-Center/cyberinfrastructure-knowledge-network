import time
import uuid
import json
import random
from datetime import datetime
from kafka import KafkaProducer

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:56310'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Template data
data_template = {
    "image_count": 1,
    "UUID": "",
    "image_name": "/example_images/labrador-pup.jpg",
    "image_receiving_timestamp": "",
    "image_scoring_timestamp": "",
    "score_label": "animal",
    "score_probability": 0.8429999947547913,
    "image_store_delete_time": "",
    "image_decision": "Save"
}


def generate_event():
    event = data_template.copy()
    event["UUID"] = str(uuid.uuid4())
    now = datetime.now().isoformat()
    event["image_receiving_timestamp"] = now
    event["image_scoring_timestamp"] = now
    event["score_probability"] = round(random.uniform(0, 1), 2)
    event["image_store_delete_time"] = now
    return event


# Send events every second
try:
    while True:
        event = generate_event()
        producer.send('accuracy', event)
        print(f"Sent event: {event}")
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping producer.")
finally:
    producer.close()
