import torch
from PIL import Image
from torchvision import transforms
from torchvision import models


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
    # MobileNet_V3_Small

    model.eval()

    def change_model(self, model_name):
        if model_name == 'regnet':
            self.model = models.regnet_y_128gf(weights="IMAGENET1K_SWAG_E2E_V1")
            print("Regnet requested...")
        else:
            self.model = torch.hub.load('pytorch/vision:v0.10.0', model_name, pretrained=True)
        self.model.eval()


model_store = ModelStore()

def load_model(model_name):
    model_store.change_model(model_name)


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


def predict(input):
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
