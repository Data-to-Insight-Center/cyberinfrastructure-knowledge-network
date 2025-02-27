import os
import json
import logging
import paho.mqtt.client as mqtt

# This script connects to an MQTT broker and listens for messages on the EVENTS_TOPIC.
# It then logs the received event data to the console, providing a way to monitor events published by the camera traps.

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
EVENTS_TOPIC = os.environ.get("EVENTS_TOPIC", "cameratrap/events")
CLIENT_ID = os.environ.get("CLIENT_ID", "ckn_event_subscriber")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info("Connected to MQTT broker. Subscribing to %s", EVENTS_TOPIC)
        client.subscribe(EVENTS_TOPIC)
    else:
        logging.error("Failed to connect with result code %d", rc)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        logging.info(f"Event message received on topic {msg.topic}:\n {json.dumps(data, indent=2)}")
    except Exception as e:
        logging.exception("Error processing message: %s", e)

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        logging.exception("Could not connect to MQTT broker: %s", e)
        return

    client.loop_forever()

if __name__ == "__main__":
    main()
