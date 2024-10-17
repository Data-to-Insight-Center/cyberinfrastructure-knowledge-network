#!/bin/bash

install_connector() {
  local plugin=$1
  echo "Installing connector plugin: $plugin"
  confluent-hub install --no-prompt $plugin
}

wait_for_kafka_connect() {
  echo "Waiting for Kafka Connect to start listening on localhost"
  while : ; do
    curl_status=$(curl -s -o /dev/null -w %{http_code} http://localhost:8083/connectors)
    echo -e "$(date) Kafka Connect listener HTTP state: $curl_status (waiting for 200)"
    if [ $curl_status -eq 200 ] ; then
      break
    fi
    sleep 5
  done
  echo "Kafka Connect is ready!"
}

create_connector() {
  local config_file=$1
  echo "Creating connector from config: $config_file"
  curl -X POST -H "Content-Type: application/json" --data @$config_file http://localhost:8083/connectors
}

# Install connector plugins
install_connector neo4j/kafka-connect-neo4j:5.0.5
install_connector confluentinc/kafka-connect-jdbc:latest

# Launch Kafka Connect worker
echo "Launching Kafka Connect worker"
/etc/confluent/docker/run &

# Wait for Kafka Connect to be ready
wait_for_kafka_connect

create_connector /app/postgres-sink-ckn-raw-connector.json
create_connector /app/neo4jsink-ckn-start-deployment-connector.json
create_connector /app/neo4jsink-ckn-end-deployment-connector.json
create_connector /app/neo4jsink-ckn-agg-deployment-connector.json
create_connector /app/neo4jsink-ckn-agg-device-connector.json

echo "Connector setup completed"

# Keep the container running
tail -f /dev/null