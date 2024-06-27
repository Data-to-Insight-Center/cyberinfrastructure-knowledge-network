import csv
import time
from datetime import datetime
import uuid
import random
import os
#
#This class is used as a stub to generate oracle data for CKN testing.
#
ORACLE_EVENTS_FILE = os.getenv('ORACLE_CSV_PATH', '/Users/swithana/git/d2i/icicle-ckn/oracle_ckn_daemon/output.csv')

header = ['image_count', 'UUID', 'image_name', 'image_receiving_timestamp', 'image_scoring_timestamp', 'score_label',
          'score_probability', 'image_store_delete_time', 'image_decision']
data_template = {
    "image_count": 1,
    "UUID": "",
    "image_name": "/example_images/labrador-pup.jpg",
    "image_receiving_timestamp": "",
    "image_scoring_timestamp": "",
    "score_label": "animal",
    "score_probability": 0.8429999947547913,
    "image_store_delete_time": "",
    "image_decision": "Save"
}

# Open the CSV file for writing
with open(ORACLE_EVENTS_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    # writer.writerow(header)  # Write the header

    i = 1
    while i < 10:
        # Update the dynamic parts of the data
        current_time = datetime.utcnow().isoformat() + "Z"
        unique_id = str(uuid.uuid4())
        score_probability = round(random.uniform(0.5, 1.0), 6)

        data_template["UUID"] = unique_id
        data_template["image_count"] = i
        data_template["image_receiving_timestamp"] = current_time
        data_template["image_scoring_timestamp"] = current_time
        data_template["score_probability"] = score_probability
        data_template["image_store_delete_time"] = current_time

        # increasing the image count by 1
        i += 1

        # Prepare the row data
        row = [
            data_template["image_count"],
            data_template["UUID"],
            data_template["image_name"],
            data_template["image_receiving_timestamp"],
            data_template["image_scoring_timestamp"],
            data_template["score_label"],
            data_template["score_probability"],
            data_template["image_store_delete_time"],
            data_template["image_decision"]
        ]

        # Write the row to the CSV file
        writer.writerow(row)
        print(f'Written row to CSV: {row}')

        # Flush the file to ensure data is written
        file.flush()

        # Wait for one second
        time.sleep(1)