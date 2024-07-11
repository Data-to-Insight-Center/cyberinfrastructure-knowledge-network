import csv
import logging
import time
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from confluent_kafka import Producer, KafkaError
from confluent_kafka.admin import AdminClient

ORACLE_EVENTS_FILE = os.getenv('ORACLE_CSV_PATH',
                               '/Users/swithana/git/icicle/camera-traps/releases/0.3.3/oracle_plugin_dir/image_mapping_final.json')
CKN_LOG_FILE = os.getenv('CKN_LOG_FILE', './ckn_daemon.log')
KAFKA_BROKER = os.getenv('CKN_KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('CKN_KAFKA_TOPIC', 'oracle-events')
DEVICE_ID = os.getenv('CAMERA_TRAPS_DEVICE_ID', 'device_1')

header = ["image_count", "UUID", "image_name", "ground_truth",
          "image_receiving_timestamp", "image_scoring_timestamp", "model_id",
          "label", "probability", "image_store_delete_time", "image_decision"]


class OracleEventHandler(FileSystemEventHandler):
    """
    Event handler class to handle events received from the Oracle plugin through the output.json.
    """

    def __init__(self, file_path, producer, topic, device_id):
        self.file_path = file_path
        self.producer = producer
        self.topic = topic
        self.device_id = device_id
        self.processed_images = set()

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        """
        When the file is modified, execute the event handler.
        """
        if event.src_path == self.file_path:
            logging.debug(f"File {self.file_path} modified.")
            self.read_json_events()

    def read_csv_lines(self):
        """
        CSV reader for csv files.
        :return:
        """
        logging.debug(f"Reading new image data from {self.file_path}")
        with open(self.file_path, mode='r') as file:
            reader = csv.DictReader(file, fieldnames=header)
            for line_number, row in enumerate(reader, start=1):
                if line_number not in self.processed_images:
                    self.processed_images.add(line_number)
                    logging.debug(f"New row: {row}")  # or process the row as needed
                    self.produce_event(row)

    def read_json_events(self):
        """
        Reads the JSON events from the file.
        Only sends events if the image_decision component is present in the JSON entry.
        This is to make sure only the processed images are extracted.
        :return:
        """
        logging.debug(f"Reading new image data from {self.file_path}")
        # Load the JSON data from the file. If the file is not yet written fully, wait for it to be written.
        while True:
            try:
                with open(self.file_path, 'r') as file:
                    data = json.load(file)
                    break
            except json.JSONDecodeError:
                logging.debug("File not complete. Waiting for the file to be completely written")
                time.sleep(1)

        # Process each entry in the JSON data
        for key, value in data.items():
            # if the full image processing workflow is not yet completed, don't read the json
            if "image_decision" not in value:
                continue

            uuid = value.get("UUID")
            # if the uuid has been processed earlier, skip it
            if uuid in self.processed_images:
                continue

            # Extract the rest of the fields
            image_count = value.get("image_count")
            image_name = value.get("image_name")
            ground_truth = value.get("ground_truth")
            image_receiving_timestamp = value.get("image_receiving_timestamp")
            image_scoring_timestamp = value.get("image_scoring_timestamp")
            image_store_delete_time = value.get("image_store_delete_time", value.get("image_delete_time"))
            image_decision = value.get("image_decision")
            model_id = value.get("model_id")

            # Extract the label with max probability for event processing.
            scores = value.get("score", [])
            if scores:
                highest_score = max(scores, key=lambda x: x["probability"])
                label = highest_score["label"]
                probability = highest_score["probability"]

                # Flatten the scores component as a JSON string for storing.
                flattened_scores = json.dumps(scores)
            else:
                label = None
                probability = 0
                flattened_scores = None

            # Generate the event
            event = {
                "image_count": image_count,
                "UUID": uuid,
                "image_name": image_name,
                "ground_truth": ground_truth,
                "image_receiving_timestamp": image_receiving_timestamp,
                "image_scoring_timestamp": image_scoring_timestamp,
                "model_id": model_id,
                "label": label,
                "probability": probability,
                "image_store_delete_time": image_store_delete_time,
                "image_decision": image_decision,
                "flattened_scores": flattened_scores
            }
            self.produce_event(event)

    def produce_event(self, event):
        """
        Adds the device_id to the event and sends it to the CKN broker.
        :param event:
        :return:
        """
        try:
            # add the device id
            event['device_id'] = self.device_id
            logging.info(f"New oracle event: {event}")
            row_json = json.dumps(event)

            # send the event
            self.producer.produce(self.topic, key=DEVICE_ID, value=row_json)

            # add line to the processed set only if the produce succeeds
            self.processed_images.add(event['UUID'])
            self.producer.flush()

        except BufferError as e:
            logging.error(f"Buffer error: {e}")
        except KafkaError as e:
            logging.error(f"Kafka error: {e}")


def setup_logging():
    """
    Logs to both console and file.
    :return:
    """
    log_formatter = logging.Formatter('%(asctime)s - %(message)s')

    # Create the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Logs all INFO, DEBUG and ERROR to the CKN_LOG_FILE
    file_handler = logging.FileHandler(CKN_LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # Logs INFO and ERROR to stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


def test_ckn_broker_connection(configuration, timeout=10):
    """
    Checks if the CKN broker is up and running.
    :param bootstrap_servers: CKN broker hosts
    :param timeout: seconds to wait for the admin client to connect
    :return:
    """
    while True:
        try:
            admin_client = AdminClient(configuration)
            # Access the topics, if not successful wait
            topics = admin_client.list_topics(timeout=timeout)
            return True
        except Exception as e:
            logging.info(f"CKN broker not available yet: {e}. Retrying in 5 seconds...")
            time.sleep(5)




if __name__ == "__main__":
    setup_logging()
    logging.basicConfig(filename=CKN_LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

    # Wait until the file exists
    while not os.path.exists(ORACLE_EVENTS_FILE):
        logging.info(f"Waiting for {ORACLE_EVENTS_FILE} to exist...")
        time.sleep(1)

    # Configure Kafka producer.
    kafka_conf = {'bootstrap.servers': KAFKA_BROKER, 'log_level': 0}

    logging.info("Connecting to the CKN broker at %s", KAFKA_BROKER)
    # Wait for CKN broker to be available
    test_ckn_broker_connection(kafka_conf)
    logging.info("Successfully connected to the CKN broker at %s", KAFKA_BROKER)

    # Initialize the Kafka producer
    producer = Producer(**kafka_conf)

    # Start the event handler for listening to the file modifications.
    event_handler = OracleEventHandler(file_path=ORACLE_EVENTS_FILE, producer=producer, topic=KAFKA_TOPIC,
                                       device_id=DEVICE_ID)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(ORACLE_EVENTS_FILE), recursive=False)

    logging.info(f"Watching file: {ORACLE_EVENTS_FILE}")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
