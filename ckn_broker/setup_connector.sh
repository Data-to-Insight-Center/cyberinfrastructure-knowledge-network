#!/bin/bash

# Load the configuration from .env file
config_file="../.env"
NEO4J_URI=$(grep 'NEO4J_URI' $config_file | awk '{print $2}')
NEO4J_USER=$(grep 'NEO4J_USER' $config_file | awk '{print $2}')
NEO4J_PWD=$(grep 'NEO4J_PWD' $config_file | awk '{print $2}')

echo "Installing connector plugins"
confluent-hub install --no-prompt neo4j/kafka-connect-neo4j:latest

echo "Launching Kafka Connect worker"
/etc/confluent/docker/run &

echo "Waiting for Kafka Connect to start listening on localhost"
while : ; do
  curl_status=$(curl -s -o /dev/null -w %{http_code} http://localhost:8083/connectors)
  echo -e $(date) " Kafka Connect listener HTTP state: " $curl_status " (waiting for 200)"
  if [ $curl_status -eq 200 ] ; then
    break
  fi
  sleep 5
done

echo "Kafka Connect is ready!"

# Function to create Neo4j Sink Connector
create_connector() {
  local connector_file=$1
  curl -X POST -H "Content-Type: application/json" \
    --data @<(cat $connector_file | jq --arg uri "$NEO4J_URI" --arg user "$NEO4J_USER" --arg pwd "$NEO4J_PWD" \
      '.config += {"neo4j.server.uri": $uri, "neo4j.authentication.basic.username": $user, "neo4j.authentication.basic.password": $pwd}') \
    http://localhost:8083/connectors
}

# Create connectors using the function
create_connector "/app/neo4jsink-oracle-events-connector.json"
create_connector "/app/neo4jsink-oracle-alerts-connector.json"
create_connector "/app/neo4jsink-compiler-data-connector.json"
create_connector "/app/neo4jsink-cameratraps-power-summary-connector.json"

echo "Connector setup completed"

# Keep the container running
tail -f /dev/null
