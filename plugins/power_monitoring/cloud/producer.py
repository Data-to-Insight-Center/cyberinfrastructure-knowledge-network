import json
from confluent_kafka import Producer


# Callback function to handle delivery reports
def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Path to your cleaned CSV file
csv_file = 'results/archive/2024-10-07.csv'

# Configure producer with acks and delivery report callback
producer = Producer({
    'bootstrap.servers': '10.20.39.102:9092',
    'acks': 'all',  # Wait for all replicas to acknowledge
})

topic = "ckn_raw"

schema = {
    "type": "struct",
    "fields": [
        {"type": "string", "optional": True, "field": "prediction"},
        {"type": "float", "optional": True, "field": "compute_time"},
        {"type": "float", "optional": True, "field": "probability"},
        {"type": "int32", "optional": True, "field": "accuracy"},
        {"type": "float", "optional": True, "field": "total_qoe"},
        {"type": "float", "optional": True, "field": "accuracy_qoe"},
        {"type": "float", "optional": True, "field": "delay_qoe"},
        {"type": "float", "optional": True,  "field":  "cpu_power"},
        {"type":"string",  "optional": True, "field": "model"},
        {"type":"string", "optional": True, "field": "timestamp"}
    ],
    "optional": False,
    "name": "mydatabase"
}

# Read the CSV file and send the data to Kafka
with open(csv_file, 'r') as file:
    for line in file:
        # Skip the header
        if line.startswith('prediction'):
            continue

        # Split the line into columns
        columns = line.split(',')

        # Define the payload with type
        payload = {
            "prediction": columns[0],
            "compute_time": float(columns[1]),
            "probability": float(columns[2]),
            "accuracy": int(columns[3]),
            "total_qoe": float(columns[4]),
            "accuracy_qoe": float(columns[5]),
            "delay_qoe": float(columns[6]),
            "cpu_power": float(columns[7]),
            "model": columns[8],
            "timestamp": columns[9]
        }

        # Combine schema and payload
        message = {
            'schema': schema,
            'payload': payload
        }

        # Produce the message and pass the callback function
        producer.produce(topic, value=json.dumps(message), callback=delivery_report)
        producer.flush(timeout=1)