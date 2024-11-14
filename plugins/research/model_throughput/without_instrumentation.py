import asyncio
import time
from statistics import mean

import torch
from PIL import Image
from torchvision import transforms

def pre_process(filename):
    """
    Pre-processes the image to allow the image to be fed into the PyTorch model.
    :param filename: Path to the image file.
    :return: Pre-processed image tensor.
    """
    input_image = Image.open(filename).convert("RGB")  # Ensure the image is in RGB format
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0)
    return input_batch

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
    avg_queue_time = round(mean([t[0] for t in times]), 3)
    avg_compute_time = round(mean([t[1] for t in times]), 3)
    return avg_queue_time, avg_compute_time

async def find_max_throughput(rps_values):
    """Test throughput limit by using specific RPS values."""
    for rps in rps_values:
        # Show Start time for this rps
        print(f"Start time for RPS {rps}: {time.strftime('%X')}")
        avg_queue_time, avg_compute_time = await measure_throughput(rps)
        print(rps, avg_queue_time, avg_compute_time)
        # Show End time for this rps
        print(f"End time for RPS {rps}: {time.strftime('%X')}")

# Run asyncio event loop to find throughput limit for specific RPS values
if __name__ == '__main__':
    IMAGE_PATH = '../client/abacus.jpg'
    MODEL = torch.hub.load('pytorch/vision:v0.10.0', 'mobilenet_v3_small', pretrained=True)
    MODEL.eval()

    # Use GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    MODEL = MODEL.to(device)

    # Load labels
    with open("imagenet_classes.txt", "r") as f:
        labels = [s.strip() for s in f.readlines()]

    rps_values = [10, 50, 100, 500, 1000, 2000]  # Specific RPS values
    asyncio.run(find_max_throughput(rps_values))