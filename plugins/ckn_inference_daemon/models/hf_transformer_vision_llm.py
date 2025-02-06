from PIL import Image
from torchvision import transforms
import torch
from models.base_model import BaseModel
from transformers import AutoProcessor, AutoModelForVision2Seq
from transformers.image_utils import load_image

class HFTransformerVisionLLM(BaseModel):
    def __init__(self, hf_model_name):
        self.model_name = hf_model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Initialize processor and model
        self.processor = AutoProcessor.from_pretrained(self.model_name)
        self.model = AutoModelForVision2Seq.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            _attn_implementation="flash_attention_2" if self.device == "cuda" else "eager",
        ).to(self.device)

    def pre_process(self, filename):
        input_image = load_image(filename)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": "Can you describe this image?"}
                ]
            },
        ]

        prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(text=prompt, images=[input_image], return_tensors="pt")
        inputs = inputs.to(self.device)
        return inputs

    def predict(self, preprocessed_input, max_new_tokens=500):
        generated_ids = self.model.generate(**preprocessed_input, max_new_tokens=max_new_tokens)
        generated_texts = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )
        return generated_texts[0], 0.0
