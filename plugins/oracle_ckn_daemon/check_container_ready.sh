#!/bin/bash

# Replace with the actual check command or HTTP endpoint
CONTAINER_NAME="oracle_ckn_daemon"
MAX_ATTEMPTS=10
ATTEMPT=1
SLEEP_INTERVAL=10

echo "Waiting for $CONTAINER_NAME to be ready..."

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
  if docker exec $CONTAINER_NAME curl -s http://localhost:your-endpoint 2>/dev/null | grep "expected-response"; then
    echo "$CONTAINER_NAME is ready!"
    exit 0
  else
    echo "Attempt $ATTEMPT: $CONTAINER_NAME not ready yet..."
    sleep $SLEEP_INTERVAL
    ATTEMPT=$((ATTEMPT+1))
  fi
done

echo "$CONTAINER_NAME did not become ready after $MAX_ATTEMPTS attempts."
exit 1
