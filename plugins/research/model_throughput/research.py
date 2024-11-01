import asyncio
import time
from statistics import mean

import torch

from model import pre_process

IMAGE_PATH =  '/Users/neeleshkarthikeyan/d2i/cyberinfrastructure-knowledge-network/plugins/power_monitoring/device/data/images/abacus.jpg'
MODEL = torch.hub.load('pytorch/vision:v0.10.0', 'resnet152', pretrained=True)
MODEL.eval()

# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL = MODEL.to(device)

# Load labels
with open("imagenet_classes.txt", "r") as f:
    labels = [s.strip() for s in f.readlines()]

async def async_pre_process(filename):
    """Async wrapper for pre_process to enable concurrent execution."""
    return pre_process(filename).to(device)

async def async_predict(input_tensor):
    """Async wrapper for predict function to enable concurrent execution."""
    with torch.no_grad():
        output = MODEL(input_tensor)
    prob = torch.nn.functional.softmax(output[0], dim=0)
    high_prob, pred_label = torch.topk(prob, 1)
    return labels[pred_label[0]], high_prob[0].item()

async def process_image(filename, request_time):
    """Process a single image, measuring both queue and compute time."""
    start_time = time.time()
    queue_time = start_time - request_time

    preprocessed_input = await async_pre_process(filename)
    prediction, probability = await async_predict(preprocessed_input)

    end_time = time.time()
    compute_time = end_time - start_time
    return queue_time, compute_time

async def measure_throughput(requests_per_second):
    """Measure average queue time and compute time for a burst of requests."""
    tasks = []
    start_times = []

    # Simulate a burst of requests (all at once)
    for _ in range(requests_per_second):
        request_time = time.time()
        start_times.append(request_time)
        tasks.append(process_image(IMAGE_PATH, request_time))

    # Wait for all tasks to complete
    times = await asyncio.gather(*tasks)

    # Calculate averages for queue time and compute time
    avg_queue_time = mean([t[0] for t in times])
    avg_compute_time = mean([t[1] for t in times])
    return avg_queue_time, avg_compute_time

async def find_max_throughput(rps_values):
    """Test throughput limit by using specific RPS values."""
    for rps in rps_values:
        avg_queue_time, avg_compute_time = await measure_throughput(rps)
        print(f"RPS: {rps}, Mean Queue Time: {avg_queue_time:.4f}s, Mean Compute Time: {avg_compute_time:.4f}s")

# Run asyncio event loop to find throughput limit for specific RPS values
if __name__ == '__main__':
    rps_values = [10, 50, 100, 500, 1000]  # Specific RPS values
    asyncio.run(find_max_throughput(rps_values))