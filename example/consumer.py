from confluent_kafka import Consumer, KafkaError, KafkaException
import json

# Configuration
conf = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "python-consumer-group",
    "auto.offset.reset": "earliest",  # Start reading at the earliest message
}

# Create Consumer instance
consumer = Consumer(conf)

# Subscribe to topic
consumer.subscribe(["oracle-events"])

# Poll for new messages
try:
    while True:
        msg = consumer.poll(timeout=1.0)  # Wait for up to 1 second for a message

        if msg is None:
            continue  # No message available

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition, continue polling
                continue
            else:
                raise KafkaException(msg.error())

        # Process the message
        event_data = json.loads(msg.value().decode("utf-8"))
        print(f"Received event: {event_data}")

except KeyboardInterrupt:
    # Exit on Ctrl+C
    pass

finally:
    # Close down the consumer
    consumer.close()
