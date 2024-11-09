import psycopg2
import json
from confluent_kafka import Producer
import pandas as pd

# PostgreSQL connection parameters
db_config = {
    "dbname": "d2i",
    "user": "d2i",
    "password": "d2i",
    "host": "149.165.170.250",
    "port": 5432
}

# Kafka Producer configuration
kafka_config = {
    'bootstrap.servers': '149.165.170.250:9092'
}
producer = Producer(kafka_config)
AGG_TOPIC = 'ckn_agg_deployment'

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def fetch_data_from_postgres():
    """Fetch data from PostgreSQL and return as a DataFrame."""
    conn = psycopg2.connect(**db_config)
    query = "SELECT * FROM ckn_raw"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def aggregate_data(df):
    """Group by deployment_id and compute aggregates."""
    agg_df = df.groupby('deployment_id').agg({
        'req_delay': 'mean',
        'req_acc': 'mean',
        'compute_time': 'mean',
        'probability': 'mean',
        'accuracy': 'mean',
        'total_qoe': 'mean',
        'accuracy_qoe': 'mean',
        'delay_qoe': 'mean',
        'cpu_power': 'mean',
        'gpu_power': 'mean',
        'total_power': 'mean',
        'deployment_id': 'size'  # count as total requests
    }).rename(columns={'deployment_id': 'total_requests'}).reset_index()

    # Rename columns to match the Neo4j sink connector config
    agg_df.columns = [
        'deployment_id', 'avg_req_delay', 'avg_req_acc', 'avg_compute_time',
        'avg_probability', 'avg_accuracy', 'avg_total_qoe', 'avg_accuracy_qoe',
        'avg_delay_qoe', 'avg_cpu_power', 'avg_gpu_power', 'avg_total_power',
        'total_requests'
    ]
    return agg_df

def produce_to_kafka(agg_df):
    """Produce aggregated data to Kafka."""
    for _, row in agg_df.iterrows():
        payload = row.to_dict()
        producer.produce(
            AGG_TOPIC,
            key=str(payload['deployment_id']),
            value=json.dumps(payload),
            callback=delivery_report
        )
    producer.flush()

def main():
    df = fetch_data_from_postgres()
    agg_df = aggregate_data(df)
    produce_to_kafka(agg_df)

if __name__ == "__main__":
    main()
