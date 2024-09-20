import os
import time
import requests
from jtop import jtop
from dotenv import load_dotenv

load_dotenv()
# Log file where data will be written
log_file = "power_log.txt"

# Duration to run the script (in seconds)
duration = 5

# Record the start time
start_time = time.time()

# Open the log file in append mode
with open(log_file, 'a') as f:
    with jtop() as jetson:
        while jetson.ok():
            # Check if the duration has passed
            elapsed_time = time.time() - start_time
            if elapsed_time > duration:
                print("Time limit reached. Exiting.")
                break

            # Get the current timestamp
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

            # Create log entry
            log_entry = "{} - {}\n".format(timestamp, jetson.power)

            # Write to log file
            f.write(log_entry)
            f.flush()  # Ensure data is written immediately

            # Sleep for a short period to avoid excessive logging
            time.sleep(1)

# After logging, send the file via POST request
url = os.getenv('UPLOAD_URL')
files = {'file': open(log_file, 'rb')}
print(files)
response = requests.post(url, files=files)

# Check the response from the server
if response.status_code == 200:
    print("File uploaded successfully.")
else:
    print("Failed to upload file. Status code: {}".format(response.status_code))
