#!/usr/bin/env python
import os
import json
from confluent_kafka import Producer
import socket

from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import NewTopic


def delivery_callback(err, msg):
    if err:
        print('ERROR: Message failed delivery: {}'.format(err))
    else:
        print("Produced event to topic {topic}: key = {key} value = {value}".format(
            topic=msg.topic(), key=msg.key(), value=msg.value()))


def create_topic(topic_name, conf, num_partitions=1, replication_factor=1):
    admin_client = AdminClient(conf)
    new_topic = NewTopic(topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
    fs = admin_client.create_topics([new_topic])

    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print(f"Topic {topic} created")
        except Exception as e:
            print(f"Failed to create topic {topic}: {e}")


if __name__ == '__main__':
    conf = {'bootstrap.servers': 'broker:29092'}
    producer = Producer(conf)
    topics = ["cpu", "gpu"]
    volume_mount_path = '/app/logs'

    for topic in topics:
        # create_topic(topic, conf, num_partitions=3, replication_factor=1)
        for root, dirs, files in os.walk(volume_mount_path):
            for filename in files:
                if filename == f"{topic}.json":
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r') as file:
                        try:
                            content = json.load(file)
                            for data in content:
                                data_to_send = json.dumps(data).encode('utf-8')
                                producer.produce(topic, value=data_to_send, callback=delivery_callback)
                                producer.poll(0)

                        except json.JSONDecodeError:
                            print(f"Error decoding JSON from file {file_path}")

    # Block until the messages are sent.
    producer.poll(10000)
    producer.flush()
