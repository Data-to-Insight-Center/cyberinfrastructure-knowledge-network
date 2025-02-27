import os
import time
import json
import base64
import logging
import paho.mqtt.client as mqtt
import message_schema

CAMERA_TRAP_ID = os.environ.get("CAMERA_TRAP_ID", "MLEDGE_1")
IMAGES_TOPIC = os.environ.get("IMAGES_TOPIC", "cameratrap/images")

def create_image_payload(event: dict, encoded_image: str, image_id: int) -> dict:
    """
    Create the image payload using the shared message schema.
    """
    image_id = f"{CAMERA_TRAP_ID}_{image_id}"

    payload = message_schema.create_event_data(CAMERA_TRAP_ID, event, timestamp=time.time())
    payload.update({
        "image_id": image_id,
        "image_data": encoded_image,
    })
    return payload

def process_image_event(event: dict, mqtt_client: mqtt.Client) -> None:
    """
    Processes a single image event by reading the image file from the provided file location,
    publishing the image payload IMAGES_TOPIC.
    """
    try:
        file_path = event.get("file_location")
        file_name = event.get("file_name")
        if not file_path or not file_name:
            logging.error("Invalid event data for image processing: %s", event)
            return

        unique_image_id = int(time.time() * 1000)

        # read the image
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        # create the image payload
        image_payload = create_image_payload(event, encoded_image, unique_image_id)
        payload = json.dumps(image_payload)

        # publish the image payload
        result = mqtt_client.publish(IMAGES_TOPIC, payload=payload, qos=1)
        result.wait_for_publish()
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logging.error("Failed to publish image: %s", payload)
        else:
            logging.info("Published image with ID: %s", image_payload.get("image_id"))
    except Exception as e:
        logging.exception("Failed to process image event: %s", event)

def image_worker(queue, mqtt_client: mqtt.Client) -> None:
    """
    Continuously processes image events from the given queue.
    """
    while True:
        event = queue.get()  # Blocks until an event is available
        if event is None:
            break
        process_image_event(event, mqtt_client)
        queue.task_done()
