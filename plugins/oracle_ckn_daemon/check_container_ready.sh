#!/bin/bash

# Define the endpoint and port
ENDPOINT="http://localhost:8080/health"

# Number of attempts and delay between them
MAX_ATTEMPTS=10
SLEEP_INTERVAL=10

echo "Waiting for oracle_ckn_daemon to be ready..."

for i in $(seq 1 $MAX_ATTEMPTS); do
  if curl -s --head  --request GET $ENDPOINT | grep "200 OK" > /dev/null; then 
    echo "oracle_ckn_daemon is ready"
    exit 0
  else
    echo "Attempt $i: oracle_ckn_daemon not ready yet..."
    sleep $SLEEP_INTERVAL
  fi
done

echo "oracle_ckn_daemon did not become ready after $MAX_ATTEMPTS attempts."
exit 1
