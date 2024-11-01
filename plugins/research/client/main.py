import asyncio
import time
import aiohttp
from statistics import mean
import aiofiles
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

URL = "http://172.17.0.2:8000/process-image/"
IMAGE_PATH = "abacus.jpg"


async def send_request(session):
    """Send a single asynchronous request to the FastAPI endpoint with an image file."""
    start_time = time.time()  # Start time for RTT measurement
    try:
        async with aiofiles.open(IMAGE_PATH, 'rb') as file:
            file_data = await file.read()  # Read the file content
            form_data = aiohttp.FormData()  # Create FormData to send file
            form_data.add_field('file', file_data, content_type='application/octet-stream', filename='abacus.jpg')

            async with session.post(URL, data=form_data, timeout=10) as response:
                rtt = time.time() - start_time  # Calculate RTT
                if response.status == 200:
                    return rtt  # Only return RTT
                else:
                    logging.error(f"Error: Received status code {response.status}")
                    return None
    except Exception as e:
        logging.error(f"Request failed: {e}")
        return None


async def measure_throughput(session, requests_per_second):
    """Measure average RTT for a burst of requests."""
    tasks = []
    semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests

    async def sem_send_request():
        async with semaphore:
            return await send_request(session)

    for _ in range(requests_per_second):
        tasks.append(sem_send_request())

    # Wait for all tasks to complete
    times = await asyncio.gather(*tasks)

    # Filter out any failed requests (where the result is None)
    valid_times = [t for t in times if t is not None]

    if valid_times:
        avg_rtt = mean(valid_times)
        return avg_rtt
    else:
        return None


async def find_max_throughput(rps_values):
    """Test throughput limit by using specific RPS values."""
    async with aiohttp.ClientSession() as session:
        for rps in rps_values:
            avg_rtt = await measure_throughput(session, rps)
            if avg_rtt is not None:
                print(f"{rps}, {avg_rtt}")


# Run asyncio event loop to find throughput limit for specific RPS values
if __name__ == '__main__':
    asyncio.run(find_max_throughput(np.arange(1, 1001, 200)))
