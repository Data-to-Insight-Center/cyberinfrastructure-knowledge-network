#!/bin/bash

echo "Installing connector plugins"
confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:latest

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

echo "Creating Postgres Sink Connector"
curl -X POST -H "Content-Type: application/json" --data @/app/postgres-sink-ckn-raw-connector.json http://localhost:8083/connectors

echo "Connector setup completed"

# Keep the container running
tail -f /dev/null