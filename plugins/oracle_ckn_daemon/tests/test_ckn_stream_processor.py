import json
from confluent_kafka import Consumer, KafkaError
import pytest


def consume_messages(consumer, topic, timeout=10):
    messages = []
    consumer.subscribe([topic])

    # Poll messages for a specified time
    for _ in range(timeout):
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                raise KafkaError(msg.error())
        messages.append(json.loads(msg.value().decode('utf-8')))

    return messages


def test_oracle_consumers():
    # Expected output for 'oracle-aggregated' topic
    expected_oracle_aggregated_messages = [
        {
            "device_id": "sachith-macbook",
            "experiment_id": "tapis-docker-power-test1",
            "image_decision": "Deleted",
            "window_start": "2024-10-30T00:16:00Z",
            "window_end": "2024-10-30T00:17:00Z",
            "average_probability": 0.031098332721740007,
            "event_count": 6
        },
        {
            "device_id": "sachith-macbook",
            "experiment_id": "tapis-docker-power-test1",
            "image_decision": "Save",
            "window_start": "2024-10-30T00:16:00Z",
            "window_end": "2024-10-30T00:17:00Z",
            "average_probability": 0.8448333243529002,
            "event_count": 6
        }
    ]

    # Expected output for 'oracle-alerts' topic
    expected_oracle_alerts_messages = [
        {
            "alert_name":"CKN Accuracy Alert","priority":"HIGH","description":"Accuracy below threshold: 0.5","source_topic":"oracle-events","experiment_id":"tapis-docker-power-test1","timestamp":1730249419204,"event_data":{"image_count":1,"image_name":"/example_images/APL_Keyset_800x290.jpg","ground_truth":"unknown","image_receiving_timestamp":"2024-08-06T20:46:13.839515798+00:00","image_scoring_timestamp":"2024-08-06T20:34:28.903813","model_id":"0","label":"vehicle","probability":0.005289999768137932,"image_store_delete_time":"2024-08-06T20:34:28.910339666+00:00","image_decision":"Deleted","device_id":"sachith-macbook","experiment_id":"tapis-docker-power-test1","user_id":"swithana","flattened_scores":"[{\"label\": \"vehicle\", \"probability\": 0.005289999768137932}]","UUID":"91ff130e-feb8-5e86-b939-78e789561ae6"}
        },
        {
            "alert_name":"CKN Accuracy Alert","priority":"HIGH","description":"Accuracy below threshold: 0.5","source_topic":"oracle-events","experiment_id":"tapis-docker-power-test1","timestamp":1730249419226,"event_data":{"image_count":3,"image_name":"/example_images/blank01.jpeg","ground_truth":"empty","image_receiving_timestamp":"2024-08-06T20:46:14.171939424+00:00","image_scoring_timestamp":"2024-08-06T20:35:05.355686","model_id":"0","label":"vehicle","probability":0.08139999955892563,"image_store_delete_time":"2024-08-06T20:35:05.364311669+00:00","image_decision":"Deleted","device_id":"sachith-macbook","experiment_id":"tapis-docker-power-test1","user_id":"swithana","flattened_scores":"[{\"label\": \"vehicle\", \"probability\": 0.005119999870657921}, {\"label\": \"vehicle\", \"probability\": 0.005950000137090683}, {\"label\": \"vehicle\", \"probability\": 0.008919999934732914}, {\"label\": \"vehicle\", \"probability\": 0.01209999993443489}, {\"label\": \"vehicle\", \"probability\": 0.015300000086426735}, {\"label\": \"vehicle\", \"probability\": 0.08139999955892563}]","UUID":"1afc70d2-0205-562c-845b-55db8d4cd12d"}
        },
        {
            "alert_name":"CKN Accuracy Alert","priority":"HIGH","description":"Accuracy below threshold: 0.5","source_topic":"oracle-events","experiment_id":"tapis-docker-power-test1","timestamp":1730249419227,"event_data":{"image_count":4,"image_name":"/example_images/blank02.jpeg","ground_truth":"empty","image_receiving_timestamp":"2024-08-06T20:46:14.217310257+00:00","image_scoring_timestamp":"2024-08-06T20:35:24.050806","model_id":"0","label":"animal","probability":0.008100000210106373,"image_store_delete_time":"2024-08-06T20:35:24.076661137+00:00","image_decision":"Deleted","device_id":"sachith-macbook","experiment_id":"tapis-docker-power-test1","user_id":"swithana","flattened_scores":"[{\"label\": \"animal\", \"probability\": 0.005950000137090683}, {\"label\": \"animal\", \"probability\": 0.008100000210106373}]","UUID":"15c5104f-20be-54c6-9624-66adcb91268b"}
        },
        {
            "alert_name":"CKN Accuracy Alert","priority":"HIGH","description":"Accuracy below threshold: 0.5","source_topic":"oracle-events","experiment_id":"tapis-docker-power-test1","timestamp":1730249419230,"event_data":{"image_count":5,"image_name":"/example_images/blank03.jpg","ground_truth":"empty","image_receiving_timestamp":"2024-08-06T20:46:14.899806091+00:00","image_scoring_timestamp":"2024-08-06T20:35:42.994304","model_id":"0","label":"animal","probability":0.09179999679327011,"image_store_delete_time":"2024-08-06T20:35:43.001081923+00:00","image_decision":"Deleted","device_id":"sachith-macbook","experiment_id":"tapis-docker-power-test1","user_id":"swithana","flattened_scores":"[{\"label\": \"animal\", \"probability\": 0.007000000216066837}, {\"label\": \"animal\", \"probability\": 0.010300000198185444}, {\"label\": \"animal\", \"probability\": 0.015599999576807022}, {\"label\": \"animal\", \"probability\": 0.09179999679327011}]","UUID":"6341c70f-9151-56d7-b16f-95f28bb93b9f"}
        },
        {
            "alert_name":"CKN Accuracy Alert","priority":"HIGH","description":"Accuracy below threshold: 0.5","source_topic":"oracle-events","experiment_id":"tapis-docker-power-test1","timestamp":1730249419234,"event_data":{"image_count":6,"image_name":"/example_images/blank04.jpeg","ground_truth":"empty","image_receiving_timestamp":"2024-08-06T20:46:14.969231216+00:00","image_scoring_timestamp":"2024-08-06T20:36:01.478263","model_id":"0","label":"empty","probability":0.0,"image_store_delete_time":"2024-08-06T20:36:01.485590626+00:00","image_decision":"Deleted","device_id":"sachith-macbook","experiment_id":"tapis-docker-power-test1","user_id":"swithana","flattened_scores":"[{\"label\": \"empty\", \"probability\": 0.0}]","UUID":"cb52dad5-372d-59de-8257-b3a316cd729c"}
        },
        {
            "alert_name":"CKN Accuracy Alert","priority":"HIGH","description":"Accuracy below threshold: 0.5","source_topic":"oracle-events","experiment_id":"tapis-docker-power-test1","timestamp":1730249419235,"event_data":{"image_count":7,"image_name":"/example_images/blank05.jpeg","ground_truth":"empty","image_receiving_timestamp":"2024-08-06T20:46:15.025145341+00:00","image_scoring_timestamp":"2024-08-06T20:36:19.558739","model_id":"0","label":"empty","probability":0.0,"image_store_delete_time":"2024-08-06T20:36:19.564788426+00:00","image_decision":"Deleted","device_id":"sachith-macbook","experiment_id":"tapis-docker-power-test1","user_id":"swithana","flattened_scores":"[{\"label\": \"empty\", \"probability\": 0.0}]","UUID":"313f2ee4-e271-5d3b-9ba6-5303e5ed0561"}
        }
    ]

    # Kafka consumer configuration
    consumer_config = {
        'bootstrap.servers': 'localhost:9092',  # Adjust based on your Kafka setup
        'group.id': 'test-group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_config)

    try:
        # Consume and verify messages from 'oracle-aggregated' topic
        aggregated_messages = consume_messages(consumer, 'oracle-aggregated')
        assert len(aggregated_messages) == len(expected_oracle_aggregated_messages), "Mismatch in number of aggregated messages consumed"

        for expected, actual in zip(expected_oracle_aggregated_messages, aggregated_messages):
            assert expected == actual, f"Expected: {expected}, but got: {actual}"

        # Consume and verify messages from 'oracle-alerts' topic
        alerts_messages = consume_messages(consumer, 'oracle-alerts')
        assert len(alerts_messages) == len(expected_oracle_alerts_messages), "Mismatch in number of alert messages consumed"

        for expected, actual in zip(expected_oracle_alerts_messages, alerts_messages):
            assert expected == actual, f"Expected: {expected}, but got: {actual}"

    finally:
        consumer.close()
