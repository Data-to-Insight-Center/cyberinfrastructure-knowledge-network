#!/usr/bin/env python

import csv
import json

from confluent_kafka import Consumer

if __name__ == '__main__':
    # Define the Kafka consumer configuration
    config = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'kafka-python-getting-started',
        'auto.offset.reset': 'earliest',
        'security.protocol': 'PLAINTEXT'
    }

    # Create the Consumer instance
    consumer = Consumer(config)

    # Subscribe to the Kafka topic
    topic = "ckn-qoe"
    consumer.subscribe([topic])

    csv_file = f"results/2024-10-07.csv"
    fieldnames = ['server_id', 'service_id', 'client_id', 'ground_truth', 'req_delay', 'req_acc', 'prediction', 'compute_time', 'probability', 'accuracy', 'total_qoe', 'accuracy_qoe', 'delay_qoe', 'cpu_power', 'model', 'start_time', 'end_time']

    # Open the CSV file and set up the CSV writer
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write the headers to the CSV file

        # Poll for new messages from Kafka and write them to the CSV
        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    print("Waiting for messages...")
                elif msg.error():
                    print(f"ERROR: {msg.error()}")
                else:
                    # Decode the message value and parse it as JSON
                    message_value = msg.value().decode('utf-8')
                    message_data = json.loads(message_value)

                    # Write the message data to the CSV file
                    writer.writerow(message_data)
                    print(f"Message written to CSV: {message_data}")

        except KeyboardInterrupt:
            print("Consumption interrupted.")

        finally:
            # Close the consumer connection
            consumer.close()
            print("Consumer closed.")
