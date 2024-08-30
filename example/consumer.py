from confluent_kafka import Consumer, KafkaError
from neo4j import GraphDatabase
import json

# Kafka Consumer Configuration
consumer_conf = {
    "bootstrap.servers": "172.22.0.4:9092",
    "group.id": "neo4j-consumer-group",
    "auto.offset.reset": "earliest",
}

# Neo4j Configuration
neo4j_conf = {"uri": "bolt://localhost:7687", "user": "neo4j", "password": "PWD_HERE"}

# Create Kafka Consumer instance
consumer = Consumer(consumer_conf)
consumer.subscribe(["oracle-events"])

# Create Neo4j Driver instance
neo4j_driver = GraphDatabase.driver(
    neo4j_conf["uri"], auth=(neo4j_conf["user"], neo4j_conf["password"])
)


def process_message(message):
    event = json.loads(message.value().decode("utf-8"))

    with neo4j_driver.session() as session:
        query = """
        MERGE (e:Experiment {experiment_id: $experiment_id})
        MERGE (d:Deployment {deployment_id: $experiment_id})
        SET d.image_generating_plugin_cpu_power_consumption = $image_generating_plugin_cpu_power_consumption,
            d.image_generating_plugin_gpu_power_consumption = $image_generating_plugin_gpu_power_consumption,
            d.power_monitor_plugin_cpu_power_consumption = $power_monitor_plugin_cpu_power_consumption,
            d.power_monitor_plugin_gpu_power_consumption = $power_monitor_plugin_gpu_power_consumption,
            d.image_scoring_plugin_cpu_power_consumption = $image_scoring_plugin_cpu_power_consumption,
            d.image_scoring_plugin_gpu_power_consumption = $image_scoring_plugin_gpu_power_consumption,
            d.total_cpu_power_consumption = $total_cpu_power_consumption,
            d.total_gpu_power_consumption = $total_gpu_power_consumption,
            d.end_time = timestamp()
        MERGE (e)-[:DEPLOYMENT_INFO]->(d)
        """
        params = {
            "experiment_id": event["experiment_id"],
            "image_generating_plugin_cpu_power_consumption": event[
                "experiment_data"
            ].get("image_generating_plugin_cpu_power_consumption"),
            "image_generating_plugin_gpu_power_consumption": event[
                "experiment_data"
            ].get("image_generating_plugin_gpu_power_consumption"),
            "power_monitor_plugin_cpu_power_consumption": event["experiment_data"].get(
                "power_monitor_plugin_cpu_power_consumption"
            ),
            "power_monitor_plugin_gpu_power_consumption": event["experiment_data"].get(
                "power_monitor_plugin_gpu_power_consumption"
            ),
            "image_scoring_plugin_cpu_power_consumption": event["experiment_data"].get(
                "image_scoring_plugin_cpu_power_consumption"
            ),
            "image_scoring_plugin_gpu_power_consumption": event["experiment_data"].get(
                "image_scoring_plugin_gpu_power_consumption"
            ),
            "total_cpu_power_consumption": event["experiment_data"].get(
                "total_cpu_power_consumption"
            ),
            "total_gpu_power_consumption": event["experiment_data"].get(
                "total_gpu_power_consumption"
            ),
        }
        session.run(query, params)


def main():
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break

            process_message(msg)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        neo4j_driver.close()


if __name__ == "__main__":
    main()
