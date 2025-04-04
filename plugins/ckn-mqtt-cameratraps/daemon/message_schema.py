import time
from typing import Dict, Any

# Parameters expected from the csv file
schema_fields = ["file_name", "file_location", "classification"]

def create_event_data(camera_trap_id: str, row_data: Dict[str, Any], timestamp: float = None) -> Dict[str, Any]:
    """
    Create the event data dictionary using the given parameters.
    """
    if timestamp is None:
        timestamp = int(time.time() * 1000)
    image_id = f'{camera_trap_id}_image_{timestamp}'
    event_data = {"camera_trap_id": camera_trap_id, "timestamp": timestamp, "image_id": image_id}
    event_data.update(row_data)
    return event_data
