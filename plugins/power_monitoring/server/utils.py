import os
import time
from datetime import timedelta

import torch
from PIL import Image
from torchvision import transforms
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
ACCEPTED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

class ModelStore:
    # loading the model
    # model = models.squeezenet1_1(weights="SqueezeNet1_1_Weights.IMAGENET1K_V1")
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'googlenet', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'alexnet', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'mobilenet_v2', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'convnext_small', pretrained=True)
    # model = models.resnet50(weights="IMAGENET1K_V2")
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'convnext', pretrained=True)

    model = torch.hub.load('pytorch/vision:v0.10.0', 'squeezenet1_1', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet152', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'shufflenet_v2_x0_5', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'densenet201', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'mobilenet_v3_small', pretrained=True)
    # model = torch.hub.load('pytorch/vision:v0.10.0', 'resnext50_32x4d', pretrained=True)

    # model = torch.hub.load('pytorch/vision:v0.10.0', 'googlenet', pretrained=True)
    # model = models.regnet_y_128gf(weights="IMAGENET1K_SWAG_E2E_V1")

    model.eval()


model_store = ModelStore()


# retrieving the class label
with open("imagenet_classes.txt", "r") as f:
    labels = [s.strip() for s in f.readlines()]


def pre_process(filename):
    """
    Pre-processes the image to allow the image to be fed into the pytorch model.
    :param filename:
    :return: pre-processed image
    """
    input_image = Image.open(filename)
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0)
    return input_batch


def get_prediction_probability(input):
    """
    Predicting the class for a given pre-processed input
    :param input:
    :return: prediction class
    """
    with torch.no_grad():
        output = model_store.model(input)
    prob = torch.nn.functional.softmax(output[0], dim=0)

    # retrieve top probability for the input
    high_prob, pred_label = torch.topk(prob, 1)

    return str((labels[pred_label[0]])), high_prob[0].item()

def save_file(file):
    """
    Saves a given file and waits for it to be saved before returning.
    :param file:
    :return: relative file path of the image saved.
    """
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    while not os.path.exists(file_path):
        time.sleep(0.1)
    return file_path


def check_file_extension(filename):
    """
    Validates the file uploaded is an image.
    :param filename:
    :return: if the file extension is of an image or not.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ACCEPTED_EXTENSIONS

def process_qoe(probability, compute_time, req_delay, req_accuracy):
    """
    Processes the QoE value for a given inference.
    """
    acc_qoe = calculate_acc_qoe(req_accuracy, probability)
    delay_qoe = calculate_delay_qoe(req_delay, compute_time)
    return 0.5*acc_qoe + 0.5*delay_qoe, acc_qoe, delay_qoe

def calculate_acc_qoe(req_acc, provided_acc):
    """
    Measures the accuracy QoE between two values.
    """
    # dxy = np.abs(req_acc-provided_acc)/np.max((req_acc, provided_acc))
    return min(1.0, provided_acc/req_acc)


def calculate_delay_qoe(req_delay, provided_delay):
    """
    Measures the delay QoE between two values.
    """
    req_delay_seconds = req_delay.total_seconds() if isinstance(req_delay, timedelta) else req_delay
    provided_delay_seconds = provided_delay.total_seconds() if isinstance(provided_delay, timedelta) else provided_delay
    return min(1.0, req_delay_seconds / provided_delay_seconds)