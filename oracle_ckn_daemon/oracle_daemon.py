import csv
import logging
import time
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from confluent_kafka import Producer, KafkaError

ORACLE_EVENTS_FILE = os.getenv('ORACLE_CSV_PATH', '/Users/swithana/git/d2i/icicle-ckn/oracle_ckn_daemon/output.csv')
CKN_LOG_FILE = os.getenv('CKN_LOG_FILE', './ckn_daemon.log')
KAFKA_BROKER = os.getenv('CKN_KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('CKN_KAFKA_TOPIC', 'oracle-events')
DEVICE_ID = os.getenv('CAMERA_TRAPS_DEVICE_ID', 'device_1')


header = ['image_count', 'UUID', 'image_name', 'image_receiving_timestamp', 'image_scoring_timestamp', 'score_label', 'score_probability', 'image_store_delete_time', 'image_decision']


class OracleEventHandler(FileSystemEventHandler):
    def __init__(self, file_path, producer, topic, device_id):
        self.file_path = file_path
        self.producer = producer
        self.topic = topic
        self.device_id = device_id
        self.processed_lines = set()

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        if event.src_path == self.file_path:
            logging.info(f"File {self.file_path} modified.")
            self.read_new_lines()

    def read_new_lines(self):
        logging.info(f"Reading new lines from {self.file_path}")
        with open(self.file_path, mode='r') as file:
            reader = csv.DictReader(file, fieldnames=header)
            for line_number, row in enumerate(reader, start=1):
                if line_number not in self.processed_lines:
                    self.processed_lines.add(line_number)
                    logging.info(f"New row: {row}")  # or process the row as needed
                    self.produce_event(row)

    def produce_event(self, event):
        try:
            event['device_id'] = self.device_id
            row_json = json.dumps(event)
            self.producer.produce(self.topic, key=DEVICE_ID, value=row_json)
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
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(CKN_LOG_FILE)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)


    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


if __name__ == "__main__":
    setup_logging()

    if not os.path.exists(ORACLE_EVENTS_FILE):
        logging.info(f"File {ORACLE_EVENTS_FILE} does not exist. Creating it.")
        open(ORACLE_EVENTS_FILE, 'w').close()

    logging.basicConfig(filename=CKN_LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

    conf = {'bootstrap.servers': KAFKA_BROKER}
    producer = Producer(**conf)

    event_handler = OracleEventHandler(file_path=ORACLE_EVENTS_FILE, producer=producer, topic=KAFKA_TOPIC, device_id=DEVICE_ID)
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
