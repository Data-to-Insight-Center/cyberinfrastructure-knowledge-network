import json
import csv
import time
import uuid
from datetime import datetime, timedelta
import random
import os
#
#This class is used as a stub to generate oracle data for CKN testing.
#
ORACLE_EVENTS_FILE = os.getenv('ORACLE_CSV_PATH', '/Users/swithana/git/d2i/icicle-ckn/oracle_ckn_daemon/oracle_plugin.csv')


def generate_entry(index):
    base_time = datetime.now()

    return {
        "image_count": index,
        "UUID": str(uuid.uuid4()),
        "image_name": f"/example_images/image_{index}.jpg",
        "ground_truth": random.choice(["animal", "person", "vehicle", "building"]),
        "image_receiving_timestamp": (base_time + timedelta(minutes=index)).isoformat(),
        "image_scoring_timestamp": (base_time + timedelta(minutes=index, seconds=30)).isoformat(),
        "model_id": f"resnet-v{random.randint(1, 3)}.{random.randint(0, 9)}-sss",
        "label": random.choice(["animal", "person", "vehicle", "building"]),
        "probability": round(random.uniform(0.7, 0.99), 4),
        "image_store_delete_time": (base_time + timedelta(minutes=index, seconds=45)).isoformat(),
        "image_decision": random.choice(["Save", "Delete"])
    }

def write_to_csv(filename, num_entries):
    fieldnames = ["image_count", "UUID", "image_name", "ground_truth",
                  "image_receiving_timestamp", "image_scoring_timestamp", "model_id",
                  "label", "probability", "image_store_delete_time", "image_decision"]

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        for i in range(num_entries):
            entry = generate_entry(i + 1)
            writer.writerow(entry)
            time.sleep(1)


if __name__ == "__main__":
    number_of_entries = 10  # Change this to generate more or fewer entries

    write_to_csv(ORACLE_EVENTS_FILE, number_of_entries)
    print(f"Generated {number_of_entries} entries in {ORACLE_EVENTS_FILE}")