import os
import requests
import torch
from huggingface_hub import hf_hub_download
from urllib.parse import urlparse
import json

class ModelStore:
    def __init__(self):
        # Read configuration for model loading
        self.model_info_endpoint = os.getenv("MODEL_URL", "http://149.165.172.217:5002/download_mc?id=e8a5ce7ef628be00617e36b32e45c84bc961f32f502b4d71c391bc686bfc6cb0")
        self.loader_type = os.getenv("MODEL_LOAD_TYPE", "pt")  # Either "pt" or "transformers"

        # get the model details
        self.repo, self.filename = self.get_model(self.model_info_endpoint)

        # Load the model based on the specified loader type
        self.model = self.load_model(self.repo, self.filename)
        self.model.eval()

    def get_model(self, model_url):
        # Retrieve the model location from the Patra HTTP endpoint
        response = requests.get(model_url)
        if response.status_code != 200:
            raise Exception("Failed to get model info")
        model_info = response.json()
        location = self.get_model_location(model_info)
        if not location:
            raise Exception("Model location not provided in response")
        return self.get_huggingface_repo_and_filename(location)

    def load_model(self, repo, filename):
        if self.loader_type == "pt":
            # Download a PyTorch model file from the Hugging Face Hub and load it with torch.load
            model_file = hf_hub_download(repo_id=repo, filename=filename)
            model = torch.load(model_file, weights_only=False)
            return model
        else:
            # todo: support transformers
            # Use transformers to load the model along with its feature extractor
            # self.feature_extractor = AutoFeatureExtractor.from_pretrained(location)
            # model = AutoModelForImageClassification.from_pretrained(location)
            return None

    def change_model(self, model_url):
        # change to a new model given a Patra server model URL
        self.repo, self.filename = self.get_model(model_url)
        self.model = self.load_model(self.repo, self.filename)
        self.model.eval()

    def get_huggingface_repo_and_filename(self, url: str) -> (str, str):
        """
        Get repo and the filename from the huggingface repo given a URL
        Example:
          Input:  "https://huggingface.co/xxx/yyy/blob/main/googlenet.pt"
          Output: ("xxx/yyy", "googlenet.pt")
        """
        parsed = urlparse(url)
        parts = [part for part in parsed.path.split('/') if part]

        if len(parts) < 3:
            raise ValueError("URL format is not recognized. Expected at least a username, repo, and filename.")

        repo = "/".join(parts[:2])
        filename = parts[-1]
        return repo, filename

    def get_model_location(self, json_str: str) -> str:
        """
        Parses a JSON string to extract the 'location' field from the 'ai_model' section.
        """
        try:
            data = json.loads(json_str)
            location = data.get("ai_model", {}).get("location")
            if not location:
                raise ValueError("Location not found in the provided JSON.")
            return location
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON provided.") from e