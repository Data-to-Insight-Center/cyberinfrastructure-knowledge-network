import imghdr
import os
import json
import base64
import logging
import time
import paho.mqtt.client as mqtt

# This script subscribes to the IMAGES_TOPIC on the MQTT broker and saves received images locally.
# It extracts image data from incoming messages, decodes it, determines the image type, and then stores the image in the SAVED_IMAGES_DIR.

SAVED_IMAGES_DIR = os.environ.get("SAVED_IMAGES_DIR", "./saved_images")
IMAGES_TOPIC = os.environ.get("IMAGES_TOPIC", "cameratrap/images")
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
CLIENT_ID = os.environ.get("CLIENT_ID", "ckn_image_subscriber")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

os.makedirs(SAVED_IMAGES_DIR, exist_ok=True)

def on_connect(client, userdata, flags, rc, properties=None):
    """
    Callback to handle connection events. Once connected,
    subscribe to the IMAGES_TOPIC.
    """
    if rc == 0:
        logging.info("Connected to MQTT broker. Subscribing to %s", IMAGES_TOPIC)
        client.subscribe(IMAGES_TOPIC)
    else:
        logging.error("Failed to connect with result code %d", rc)

def on_message(client, userdata, msg):
    """
    Callback to handle incoming base64-encoded images and saves it to SAVED_IMAGES_DIR.
    """
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        camera_trap = data.get("camera_trap_id", "unknown_camera_trap")

        # Get the image_id from the data or generate a unique id if not present
        unique_id = f'image_{int(time.time() * 1000)}'
        image_id = data.get("image_id", f'{camera_trap}_{unique_id}')
        file_name = data.get("filename", image_id)

        image_data_b64 = data.get("image_data", "")
        if not image_data_b64:
            logging.error("No image data found in the message")
            return

        # Decode the image data from base64
        image_bytes = base64.b64decode(image_data_b64)

        # Determine image extension if not specified, using imghdr
        detected_type = imghdr.what(None, image_bytes)
        if detected_type:
            ext = detected_type
        else:
            ext = os.path.splitext(file_name)[1].lstrip(".") or "png"

        # Construct a file name that includes the detected extension
        final_file_name = f"{image_id}.{ext}"
        # Construct a file name using image_id and save the file
        file_path = os.path.join(SAVED_IMAGES_DIR, final_file_name)

        with open(file_path, "wb") as f:
            f.write(image_bytes)
        logging.info("Saved image to %s", file_path)
    except Exception as e:
        logging.exception("Failed to process incoming image message: %s", e)

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
