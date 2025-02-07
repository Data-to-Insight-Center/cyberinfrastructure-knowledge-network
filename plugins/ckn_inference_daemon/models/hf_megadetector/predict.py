import torch
import cv2
import numpy as np

# Import YOLOv5 utilities (make sure yolov5 is on your path)
from utils.general import non_max_suppression
from utils.augmentations import letterbox
try:
    from utils.general import scale_coords  # YOLOv5 < v7
except ImportError:
    from utils.general import scale_boxes as scale_coords  # YOLOv5 v7+

from huggingface_hub import hf_hub_download

def simple_md_inference(image_path, device='cpu', conf_thres=0.25):
    """
    Loads the MegaDetector V5 checkpoint, preprocesses the image,
    runs inference, and returns a list of {label, probability} dicts.
    """
    # 1. Download checkpoint from Hugging Face
    model_path = hf_hub_download(repo_id="nkarthikeyan/MegaDetectorV5",
                                 filename="md_v5a.0.0.pt")

    # 2. Load YOLO model from checkpoint
    checkpoint = torch.load(model_path, map_location=device)
    # The actual YOLO model is stored under 'model'
    yolov5_model = checkpoint['model'].float().fuse().eval()

    # 3. Read and preprocess image
    orig_img = cv2.imread(image_path)            # BGR (OpenCV)
    orig_img = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)  # Convert to RGB
    # Letterbox to a fixed size (e.g., 640)
    resized_img = letterbox(orig_img, new_shape=640, stride=64, auto=True)[0]

    # Convert HWC -> CHW, float [0,1]
    resized_img = resized_img.transpose(2, 0, 1)
    resized_img = np.ascontiguousarray(resized_img, dtype=np.float32) / 255.0

    # Create a batch of size 1
    tensor_img = torch.from_numpy(resized_img).unsqueeze(0).to(device)

    # 4. Inference
    with torch.no_grad():
        prediction = yolov5_model(tensor_img)[0]

    # 5. Non-max suppression
    detections = non_max_suppression(prediction, conf_thres=conf_thres, iou_thres=0.45)

    # 6. Map detections to label/conf
    results = []
    if len(detections) > 0 and detections[0] is not None:
        # Rescale boxes back to original image size
        det = detections[0]
        det[:, :4] = scale_coords(resized_img.shape[1:], det[:, :4], orig_img.shape).round()

        # YOLO detection format: x1, y1, x2, y2, conf, class
        for *xyxy, conf, cls in det.tolist():
            results.append({
                "label": int(cls),          # YOLO class index
                "probability": float(conf)  # confidence score
            })

    return results

# --- Example usage ---
if __name__ == "__main__":
    image_path = "/Users/neeleshkarthikeyan/d2i/cyberinfrastructure-knowledge-network/plugins/ckn_inference_daemon/models/hf_megadetector/yolov5/megadetector_test_img.JPG"
    detections = simple_md_inference(image_path, device='cpu', conf_thres=0.25)
    print("Detections:", detections)
