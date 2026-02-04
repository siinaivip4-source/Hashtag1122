import torch
from PIL import Image
from io import BytesIO
from transformers import (
    VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer,
    BlipProcessor, BlipForConditionalGeneration,
    AutoProcessor, AutoModelForCausalLM
)

from src.core.config import config


class BaseModel:
    def __init__(self, model_path, device):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.processor = None
        self.tokenizer = None 

    def load(self):
        raise NotImplementedError

    def generate(self, image: Image.Image) -> str:
        raise NotImplementedError


class VitGPT2Model(BaseModel):
    def load(self):
        if not self.model:
            print(f"Loading VitGPT2Model from {self.model_path}...")
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_path).to(self.device)
            self.processor = ViTImageProcessor.from_pretrained(self.model_path)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

    def generate(self, image: Image.Image) -> str:
        self.load()
        pixel_values = self.processor(images=[image], return_tensors="pt").pixel_values.to(self.device)
        with torch.no_grad():
            output_ids = self.model.generate(
                pixel_values,
                max_length=config.max_length,
                num_beams=config.num_beams,
            )
        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()


class BlipModel(BaseModel):
    def load(self):
        if not self.model:
            print(f"Loading BlipModel from {self.model_path}...")
            self.processor = BlipProcessor.from_pretrained(self.model_path)
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_path).to(self.device)

    def generate(self, image: Image.Image) -> str:
        self.load()
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=50) 
        return self.processor.decode(output[0], skip_special_tokens=True).strip()


class GitModel(BaseModel):
    def load(self):
        if not self.model:
            print(f"Loading GitModel from {self.model_path}...")
            self.processor = AutoProcessor.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path).to(self.device)

    def generate(self, image: Image.Image) -> str:
        self.load()
        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values.to(self.device)
        with torch.no_grad():
            generated_ids = self.model.generate(pixel_values=pixel_values, max_length=config.max_length)
        return self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]


class VisionService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.loaded_models = {}

    def get_model_instance(self, model_key: str):
        if model_key not in config.available_models:
             # Fallback to default if invalid key or None
            model_key = config.default_model_name
        
        if model_key in self.loaded_models:
            return self.loaded_models[model_key]

        model_path = config.get_model_path(model_key)
        
        if model_key == "vit-gpt2":
            instance = VitGPT2Model(model_path, self.device)
        elif model_key == "blip-base":
            instance = BlipModel(model_path, self.device)
        elif model_key == "git-base":
            instance = GitModel(model_path, self.device)
        else:
             # Fallback for unconfigured models if they match a known pattern? No, just error or revert
             print(f"Warning: Unknown model type for {model_key}, falling back to default")
             return self.get_model_instance(config.default_model_name)
        
        self.loaded_models[model_key] = instance
        return instance

    def load(self):
        # Preload default model
        self.get_model_instance(config.default_model_name).load()

    def generate_caption(self, image_bytes: bytes, model_key: str = None) -> str:
        if not model_key:
            model_key = config.default_model_name
            
        instance = self.get_model_instance(model_key)

        image = Image.open(BytesIO(image_bytes))
        try:
            image = image.convert("RGB")
            return instance.generate(image)
        finally:
            image.close()


vision_service = VisionService()
