#!/usr/bin/env python
import json
import time as tm
from datetime import datetime
from random import uniform, randint
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from matplotlib import pyplot as plt


def delivery_callback(err, msg):
    if err:
        print('ERROR: Message failed delivery: {}'.format(err))
    else:
        print('{}: {}'.format(msg.topic(), data))


if __name__ == '__main__':

    config = {"bootstrap.servers": "localhost:9092"}
    topic_list = [NewTopic("request-raw"),
                  NewTopic("request-agg"),
                  NewTopic("alert-raw"),
                  NewTopic("alert-agg")]

    producer = Producer(config)
    admin_client = AdminClient(config)
    admin_client.create_topics(topic_list)

    data_entries = []
    mean_accuracies = [0.7, 0.4, 0.5, 0.8, 0.2]

    start_time = tm.time()
    while tm.time() - start_time < 100:
        current_time = tm.time() - start_time
        cycle_index = int(current_time // 10) % len(mean_accuracies)
        mean_acc = mean_accuracies[cycle_index]

        pred_accuracy = uniform(mean_acc - 0.1, mean_acc + 0.1)
        added_time = datetime.now()

        data = {
            'server_id': 'server-1',
            'service_id': "animal_classification",
            'client_id': "raspi-1",
            'prediction': randint(0, 1),
            'compute_time': tm.time() - current_time,
            'pred_accuracy': pred_accuracy,
            'total_qoe': uniform(0.7, 0.9),
            'accuracy_qoe': uniform(0.3, 0.5),
            'delay_qoe': uniform(0.3, 0.5),
            'req_acc': uniform(0.7, 0.9),
            'req_delay': uniform(0.2, 0.4),
            'model': 'GoogleNet',
            'added_time': added_time.strftime("%d-%m-%Y %H:%M:%S.%f")[:-3]
        }

        producer.produce("request-raw", json.dumps(data), data['server_id'], callback=delivery_callback)
        producer.poll(0)
        tm.sleep(0.1)

    # Block until all messages are sent
    producer.poll(10000)
    producer.flush()

    times = [entry[1] for entry in data_entries]
    accuracies = [entry[0] for entry in data_entries]

    plt.figure(figsize=(12, 6))
    plt.plot(times, accuracies, linestyle='-', color='b')
    plt.axhline(y=0.4, color='r', linestyle='--', label='Raw Alert Threshold')
    plt.axhline(y=0.6, color='g', linestyle='--', label='Agg Alert Threshold')
    plt.title('Prediction Accuracy Over Time')
    plt.xlabel('Time')
    plt.ylabel('Prediction Accuracy')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(True)
    plt.legend()
    # plt.savefig('workload.png')
