import json
import os
import socket

from confluent_kafka import Producer

def delivery_callback(err, msg):
    if err:
        print('ERROR: Message failed delivery: {}'.format(err))
    else:
        print("Produced event to topic {topic}: key = {key} value = {value}".format(
            topic=msg.topic(), key=msg.key(), value=msg.value()))

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def main():
    conf = {'bootstrap.servers': 'kafka:29092',
            'client.id': socket.gethostname()}

    producer = Producer(conf)

    topic = "cpu"

    cpu_file = json.loads(read_file(os.path.join("/data", f"{topic}.json")))
    metadata_file = json.loads(read_file(os.path.join("/data", "metadata.json")))

    pid_map = {}
    for pair in metadata_file['plugins']:
        for pid in pair['pids']:
            pid_map[str(pid)] = pair['name']

    for entry in cpu_file:
        for timestamp, values in entry.items():
            for value in values:
                watt = value[0]
                pid = value[1]
                event = {"server_id": 1,
                         "plugin_name": pid_map.get(pid, "Unknown Plugin"),
                         "type": topic,
                         "value": watt,
                         "process_id": pid,
                         "timestamp": timestamp}

                data_to_send = json.dumps(event)

                producer.produce(topic, value=data_to_send, callback=delivery_callback)
                producer.poll(0)

    # Block until all messages are sent
    producer.poll(10000)
    producer.flush()

if __name__ == "__main__":
    main()
