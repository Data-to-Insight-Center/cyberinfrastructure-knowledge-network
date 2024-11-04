import json
import uuid
from confluent_kafka import Consumer


def consume_messages(consumer, topic, timeout=10):
    messages = []
    consumer.subscribe([topic])

    # Poll messages for a specified time
    for _ in range(timeout):
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            raise Exception(f"Kafka error: {msg.error()}")

        message = json.loads(msg.value().decode('utf-8'))
        messages.append(message)

    return messages


def test_oracle_consumers():
    expected_oracle_aggregated_events_count = 2
    expected_oracle_alerts_events_count = 6

    # Kafka consumer configuration
    consumer_config = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': f'test-group-{uuid.uuid4()}',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_config)

    try:
        # Consume and verify messages from 'oracle-aggregated' topic
        aggregated_messages = consume_messages(consumer, 'oracle-aggregated')
        assert len(aggregated_messages) == expected_oracle_aggregated_events_count, "Mismatch in number of aggregated messages consumed"

        # Consume and verify messages from 'oracle-alerts' topic
        alerts_messages = consume_messages(consumer, 'oracle-alerts')
        assert len(alerts_messages) == expected_oracle_alerts_events_count, "Mismatch in number of alert messages consumed"

    finally:
        consumer.close()
