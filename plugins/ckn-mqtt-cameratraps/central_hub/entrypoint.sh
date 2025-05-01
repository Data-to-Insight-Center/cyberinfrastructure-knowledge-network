#!/usr/bin/env bash
set -e

# Decide which subscriber to launch
case "$SUBSCRIBER_TYPE" in
  event)
    exec python /app/event_subscriber.py
    ;;
  image)
    exec python /app/image_subscriber.py
    ;;
  *)
    echo "ERROR: SUBSCRIBER_TYPE must be 'event' or 'image'" >&2
    exit 1
    ;;
esac
