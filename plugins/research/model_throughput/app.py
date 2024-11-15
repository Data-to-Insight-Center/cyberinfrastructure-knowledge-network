import time
from statistics import mean

import torch
from torchvision import models, transforms
from PIL import Image

# Load the model
def load_model(model_name):
    if model_name == "googlenet":
        model = models.googlenet(pretrained=True)
    elif model_name == "resnet152":
        model = models.resnet152(pretrained=True)
    elif model_name == "shufflenet_v2_x0_5":
        model = models.shufflenet_v2_x0_5(pretrained=True)
    elif model_name == "densenet201":
        model = models.densenet201(pretrained=True)
    elif model_name == "mobilenet_v3_small":
        model = models.mobilenet_v3_small(pretrained=True)
    elif model_name == "resnext50_32x4d":
        model = models.resnext50_32x4d(pretrained=True)
    else:
        raise ValueError(f"Model {model_name} not supported!")

    model.eval()  # Set the model to evaluation mode
    return model

# Preprocess the image
def preprocess_image(image_path):
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    image = Image.open(image_path)
    image_tensor = preprocess(image).unsqueeze(0)  # Add batch dimension
    return image_tensor

# Measure latency for one forward pass
def measure_latency(model, image_tensor):
    start_time = time.perf_counter()  # Use perf_counter for high precision timing
    with torch.no_grad():
        output = model(image_tensor)
    end_time = time.perf_counter()
    return end_time - start_time

# Measure mean latency over multiple trials
def measure_mean_latency(model, image_tensor, num_trials=100):
    latencies = []
    for _ in range(num_trials):
        latency = measure_latency(model, image_tensor)
        latencies.append(latency)
    return round(mean(latencies), 3)

if __name__ == "__main__":
    image_path = "abacus.jpg"
    image_tensor = preprocess_image(image_path)

    model_names = [
        'shufflenet_v2_x0_5',
        'densenet201',
        'googlenet',
        'mobilenet_v3_small',
        'resnet152',
        'resnext50_32x4d',
        'squeezenet1_1'
    ]

    # Warm-up and measure latency for each model
    for model_name in model_names:
        model = load_model(model_name)
        min_latency = measure_mean_latency(model, image_tensor)

        # Write to a file
        with open("latency_results.txt", "a") as f:
            f.write(f"{model_name}, {min_latency}\n")

