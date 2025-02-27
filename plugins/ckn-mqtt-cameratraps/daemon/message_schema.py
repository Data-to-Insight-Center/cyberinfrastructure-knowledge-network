import time
from typing import Dict, Any

# Parameters expected from the csv file
schema_fields = ["file_name", "file_location", "classification"]

def create_event_data(camera_trap_id: str, row_data: Dict[str, Any], timestamp: float = None) -> Dict[str, Any]:
    """
    Create the event data dictionary using the given parameters.
    This schema can be updated or extended as needed.
    """
    if timestamp is None:
        timestamp = time.time()
    event_data = {"camera_trap_id": camera_trap_id, "timestamp": timestamp}
    event_data.update(row_data)
    return event_data
