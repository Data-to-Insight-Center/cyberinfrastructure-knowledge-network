import os
import time
import csv
import json
import logging
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict
import paho.mqtt.client as mqtt
import ast
# from dotenv import load_dotenv

import image_worker
import message_schema


# load_dotenv()

CAMERA_TRAP_ID: str = os.environ.get("CAMERA_TRAP_ID", "MLEDGE_1")
MQTT_BROKER: str = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT: int = int(os.environ.get("MQTT_PORT", 1883))
EVENTS_TOPIC: str = os.environ.get("EVENTS_TOPIC", "cameratrap/events")
DETECTED_EVENTS_FILE: str = os.environ.get("DETECTED_EVENTS_FILE", "detected-events.csv")
IMAGE_WORKER_COUNT: int = int(os.environ.get("CONCURRENT_WORKERS", 2))
MQTT_QOS: int = int(os.environ.get("MQTT_QOS", 1))  # do not change this unless absolutely required.

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

image_event_queue: Queue = Queue()


def on_connect(client, userdata, flags, rc, properties=None):
    """
    Callback to handle check MQTT connection.
    """
    if rc == 0:
        logging.info("Connected to MQTT Broker")
    else:
        logging.error("MQTT connection failed with return code %d", rc)


def publish_event(mqtt_client: mqtt.Client, event_data: Dict[str, Any]) -> None:
    """
    Publishes an event to the designated EVENTS_TOPIC.
    The event data is serialized into JSON before sending.
    """
    try:
        payload = json.dumps(event_data)
        result = mqtt_client.publish(EVENTS_TOPIC, payload=payload, qos=MQTT_QOS)
        result.wait_for_publish()
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logging.error("Failed to publish event: %s", payload)
        else:
            logging.info("Published event: %s", payload)
    except Exception as e:
        logging.exception("Exception during event publish: %s", e)


def tail_and_process_events(mqtt_client: mqtt.Client) -> None:
    """
    Opens the DETECTED_EVENTS_FILE and tails it for new entries.
    For each new line, the CSV row is mapped into a dictionary using the schema
    defined in message_schema.py. The resulting event is published to the MQTT topic,
    and the event is enqueued for image file transfer to the central drone hub.
    """
    try:
        with open(DETECTED_EVENTS_FILE, 'r') as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(1)
                    continue
                line = line.strip()
                if not line:
                    continue

                try:
                    reader = csv.reader([line])
                    row = next(reader)

                    event_type = row[0]

                    if event_type == "DETECTION":
                        if len(row) < 3:
                            logging.warning("Incomplete DETECTION row: %s", row)
                            continue
                        uuid = row[1].strip()
                        parts = line.split(',', 2)
                        if len(parts) < 3:
                            logging.warning("Incomplete row: %s", line)
                            continue
                        event_type, event_id, classification_raw = parts
                        try:
                            classification = ast.literal_eval(classification_raw.strip())
                        except Exception as e:
                            logging.warning("Invalid classification format: %s", row[2])
                            continue
                        event_data = {
                            "event_type": "DETECTION",
                            "uuid": uuid,
                            "classification": classification,
                        }

                    elif event_type == "STORING":
                        if len(row) < 4:
                            logging.warning("Incomplete STORING row: %s", row)
                            continue
                        uuid = row[1].strip()
                        file_location = row[2].strip()
                        action = row[3].strip()
                        event_data = {
                            "event_type": "STORING",
                            "uuid": uuid,
                            "file_location": file_location,
                            "action": action,
                        }
                    else:
                        logging.warning("Unknown event type: %s", event_type)
                        continue
                    # create the event
                    message = message_schema.create_event_data(CAMERA_TRAP_ID, event_data)
                    if event_type == "DETECTION":
                        # publish the event
                        publish_event(mqtt_client, message)
                    elif event_type == "STORING":
                        # enqueue the event for image transfer
                        image_event_queue.put(message)
                except Exception as e:
                    logging.exception("Error processing CSV line: %s", line)
    except Exception as e:
        logging.exception("Failed to tail file %s", DETECTED_EVENTS_FILE)


def start_image_worker_pool(mqtt_client: mqtt.Client, num_workers: int = IMAGE_WORKER_COUNT) -> ThreadPoolExecutor:
    """
    Initiates a pool of image worker threads.
    These workers continuously process events from the shared queue,
    handling image encoding and publishing via MQTT.
    """
    executor = ThreadPoolExecutor(max_workers=num_workers)
    for _ in range(num_workers):
        executor.submit(image_worker.image_worker, image_event_queue, mqtt_client)
        pass
    return executor


def main() -> None:
    """
    Sets up the MQTT client, starts the network loop, initiates the image worker pool,
    and begins tailing the CSV event file.
    """
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{CAMERA_TRAP_ID}_combined_worker")
    mqtt_client.on_connect = on_connect

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        logging.exception("Could not connect to MQTT Broker: %s", e)
        return

    mqtt_client.loop_start()
    executor = start_image_worker_pool(mqtt_client, num_workers=IMAGE_WORKER_COUNT)
    tail_thread = threading.Thread(target=tail_and_process_events, args=(mqtt_client,), daemon=True)
    tail_thread.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Shutdown requested. Stopping workers...")

    for _ in range(IMAGE_WORKER_COUNT):
        image_event_queue.put(None)
    executor.shutdown(wait=True)
    mqtt_client.loop_stop()
    logging.info("Shutdown complete.")


if __name__ == "__main__":
    main()
