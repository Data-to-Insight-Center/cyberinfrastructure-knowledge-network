import os
import sys
sys.path.append("yolov5")

from utils.general import non_max_suppression
from utils.augmentations import letterbox
try:
    from utils.general import scale_coords  # YOLOv5 < v7
except ImportError:
    from utils.general import scale_boxes as scale_coords  # YOLOv5 v7+

import cv2
import numpy as np
import torch
from huggingface_hub import hf_hub_download
from base_model import BaseModel

class MegaDetectorModel(BaseModel):
    """
    A model class that loads the MegaDetector V5 checkpoint from Hugging Face,
    preprocesses an input image, runs inference, and returns detections (label/conf).
    """

    def __init__(self, device='cpu', conf_thres=0.25, iou_thres=0.45, labels_path=None):
        """
        :param device: 'cpu' or 'cuda' (if GPU is available)
        :param conf_thres: Confidence threshold for non-max suppression
        :param iou_thres: IoU threshold for non-max suppression
        :param labels_path: Optional path to a labels file (if you want class names).
                            For MegaDetector, we often have 1=animal, 2=person, 3=vehicle, etc.
        """
        self.device = torch.device(device)
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

        # Optionally load a label file if you have one (otherwise default to None)
        self.labels = None
        if labels_path and os.path.exists(labels_path):
            with open(labels_path, "r") as f:
                self.labels = [line.strip() for line in f.readlines()]

        # Download the MegaDetector V5 checkpoint from Hugging Face
        model_path = hf_hub_download(repo_id="nkarthikeyan/MegaDetectorV5", filename="md_v5a.0.0.pt")

        # Load the YOLO model
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model = checkpoint['model'].float().fuse().eval()

        if self.device.type != 'cpu':
            self.model.to(self.device)

    def pre_process(self, filename):
        image_bgr = cv2.imread(filename)
        if image_bgr is None:
            raise ValueError(f"Could not load image from path: {filename}")

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # 1. Detect the model's stride
        model_stride = int(self.model.stride.max())  # e.g., 32 or 64

        # 2. Letterbox with auto=False, passing the model stride
        processed = letterbox(
            image_rgb, new_shape=640, stride=model_stride, auto=False
        )[0]

        processed = processed.transpose(2, 0, 1)
        processed = np.ascontiguousarray(processed, dtype=np.float32) / 255.0
        input_tensor = torch.from_numpy(processed).unsqueeze(0).to(self.device)

        return (input_tensor, image_rgb)

    def predict(self, input_data):
        """
        Run the model on the pre-processed input.
        Returns a list of (label, probability) or (label_str, probability) if labels are provided.
        """
        # input_data is a tuple of (processed_tensor, original_rgb)
        processed_tensor, original_rgb = input_data

        with torch.no_grad():
            prediction = self.model(processed_tensor)[0]

        # Apply Non-Max Suppression
        detections = non_max_suppression(prediction,
                                         conf_thres=self.conf_thres,
                                         iou_thres=self.iou_thres)

        results = []
        if len(detections) > 0 and detections[0] is not None:
            # Rescale detections from [640x640] back to original image size
            det = detections[0]
            det[:, :4] = scale_coords(processed_tensor.shape[2:], det[:, :4], original_rgb.shape).round()

            # Each detection: [x1, y1, x2, y2, conf, class]
            for *xyxy, conf, cls_idx in det.tolist():
                label_idx = int(cls_idx)
                confidence = float(conf)
                # If we have a label file, map the index to a label string
                if self.labels and 0 <= label_idx < len(self.labels):
                    results.append((self.labels[label_idx], confidence))
                else:
                    # Just return numeric class index
                    results.append((label_idx, confidence))

        return results
