#!/usr/bin/env python
import time
import random
import uuid
import json
from datetime import datetime, timedelta
from confluent_kafka import Producer

def delivery_callback(err, msg):
    if err:
        print('ERROR: Message failed delivery: {}'.format(err))
    else:
        key = msg.key().decode('utf-8') if msg.key() is not None else None
        value = msg.value().decode('utf-8') if msg.value() is not None else None
        print(f"Produced event to topic {msg.topic()}: key = {key} value = {value}")

def generate_entry(index):
    base_time = datetime.now()

    return {
        "image_count": index,
        "UUID": str(uuid.uuid4()),
        "image_name": f"/example_images/image_{index}.jpg",
        "ground_truth": random.choice(["animal", "person", "vehicle", "building"]),
        "image_receiving_timestamp": (base_time + timedelta(minutes=index)).isoformat(),
        "image_scoring_timestamp": (base_time + timedelta(minutes=index, seconds=30)).isoformat(),
        "model_id": f"resnet-v{random.randint(1, 3)}.{random.randint(0, 9)}-sss",
        "label": random.choice(["animal", "person", "vehicle", "building"]),
        "probability": round(random.uniform(0.7, 0.99), 4),
        "image_store_delete_time": (base_time + timedelta(minutes=index, seconds=45)).isoformat(),
        "image_decision": random.choice(["Save", "Delete"])
    }

if __name__ == '__main__':

    config = {
        # User-specific properties that you must set
        'bootstrap.servers': 'localhost:57581',

        # Fixed properties
        'acks': 'all'
    }

    # Create Producer instance
    producer = Producer(config)

    topic = "accuracy"
    number_of_entries = 10000

    for i in range(number_of_entries):
        event = generate_entry(i + 1)
        print(f"Produced event: {event}")
        event_bytes = json.dumps(event).encode('utf-8')  # Serialize the event to JSON and encode as bytes
        producer.produce(topic, value=event_bytes, callback=delivery_callback)
        time.sleep(1)

    # Block until the messages are sent.
    producer.poll(10000)
    producer.flush()
