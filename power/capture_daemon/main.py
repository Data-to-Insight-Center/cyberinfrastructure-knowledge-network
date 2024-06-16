import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.file_path = file_path
        self.last_data_length = 0

    def on_modified(self, event):
        if event.src_path == self.file_path:
            print(f"Detected modification in {self.file_path}")
            self.read_and_print_new_data()

    def read_and_print_new_data(self):
        with open(self.file_path, 'r') as file:
            try:
                data = json.load(file)
                print(f"Current data length: {len(data)}, Last known length: {self.last_data_length}")
                # Check if there is new data
                if len(data) > self.last_data_length:
                    new_entries = data[self.last_data_length:]
                    for entry in new_entries:
                        print("New entry detected:")
                        print(json.dumps(entry, indent=4))
                    self.last_data_length = len(data)
                else:
                    print("No new data found.")
            except json.JSONDecodeError:
                print("JSON decode error - file might be incomplete.")
                pass  # File might be incomplete, so ignore this error


def monitor_file(file_path):
    event_handler = FileChangeHandler(file_path)
    observer = Observer()
    observer.schedule(event_handler, path=file_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    file_path = '/app/cpu_generated.json'
    print(f"Monitoring changes in {file_path}")
    monitor_file(file_path)
