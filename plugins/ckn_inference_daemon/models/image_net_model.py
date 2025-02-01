import os
from PIL import Image
from torchvision import transforms
import torch
from models.base_model import BaseModel

class ImageNetModel(BaseModel):
    def __init__(self, model, feature_extractor=None, labels_path=None):
        # Use the provided labels_path or default to the environment variable with fallback.
        self.labels_path = labels_path or os.getenv("IMAGENET_CLASSES_PATH", "imagenet_classes.txt")
        with open(self.labels_path, "r") as f:
            self.labels = [s.strip() for s in f.readlines()]

        self.model = model
        self.feature_extractor = feature_extractor

    def pre_process(self, filename):
        input_image = Image.open(filename)
        if self.feature_extractor is not None:
            inputs = self.feature_extractor(images=input_image, return_tensors="pt")
            return inputs["pixel_values"]
        else:
            preprocess = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            input_tensor = preprocess(input_image)
            input_batch = input_tensor.unsqueeze(0)
            return input_batch

    def predict(self, input):
        with torch.no_grad():
            output = self.model(input)
        # If the model was loaded via transformers, it will have a "logits" attribute.
        logits = output.logits[0] if hasattr(output, "logits") else output[0]
        prob = torch.nn.functional.softmax(logits, dim=0)
        high_prob, pred_label = torch.topk(prob, 1)
        return str(self.labels[pred_label[0]]), high_prob[0].item()
