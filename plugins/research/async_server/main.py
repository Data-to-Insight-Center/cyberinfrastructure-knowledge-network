import torch
import numpy as np

from PIL import Image
from fastapi import FastAPI, HTTPException, File, UploadFile
from torchvision import transforms
import logging
import traceback

# Initialize FastAPI app
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load the pre-trained model
MODEL = torch.hub.load('pytorch/vision:v0.10.0', 'resnet152', pretrained=True)
MODEL.eval()

# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL = MODEL.to(device)

# Load labels
with open("imagenet_classes.txt", "r") as f:
    labels = [s.strip() for s in f.readlines()]

def pre_process(image: Image):
    """Pre-processes the image to allow it to be fed into the PyTorch model."""
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0)
    return input_batch

async def async_pre_process(image: Image):
    """Async wrapper for pre_process to enable concurrent execution."""
    return pre_process(image).to(device)

async def async_predict(input_tensor):
    """Async wrapper for predict function to enable concurrent execution."""
    with torch.no_grad():
        output = MODEL(input_tensor)
    prob = torch.nn.functional.softmax(output[0], dim=0)
    high_prob, pred_label = torch.topk(prob, 1)
    return labels[pred_label[0]], high_prob[0].item()

async def process_image(image: Image):
    """Process a single image."""
    preprocessed_input = await async_pre_process(image)
    label, probability = await async_predict(preprocessed_input)
    return {"label": label, "probability": probability}

@app.post("/process-image/")
async def process_image_endpoint(file: UploadFile = File(...)):
    """Endpoint to process image."""
    logging.info("Received request to process image.")
    try:
        image = Image.open(file.file).convert("RGB")
        logging.info("Image loaded successfully.")
        result = await process_image(image)
        logging.info("Image processed successfully.")
        return {"status": "success", "result": result}
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logging.error(f"Error processing image: {error_message}\n{stack_trace}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
