import torch
from PIL import Image
from io import BytesIO
from transformers import CLIPModel, CLIPProcessor

STYLES = [
    "2D", "3D", "Cute", "Animeart", "Realism",
    "Aesthetic", "Cool", "Fantasy", "Comic", "Horror",
    "Cyberpunk", "Lofi", "Minimalism", "Digitalart", "Cinematic",
    "Pixelart", "Scifi", "Vangoghart"
]

COLORS = [
    "Black", "White", "Blackandwhite", "Red", "Yellow",
    "Blue", "Green", "Pink", "Orange", "Pastel",
    "Hologram", "Vintage", "Colorful", "Neutral", "Light",
    "Dark", "Warm", "Cold", "Neon", "Gradient",
    "Purple", "Brown", "Grey"
]

HASHTAGS = [
    "photography", "photo", "portrait", "landscape", "camera",
    "lifestyle", "daily", "vibes", "mood", "instagood",
    "fashion", "style", "ootd", "model", "beauty",
    "art", "digitalart", "illustration", "drawing", "creative",
    "travel", "adventure", "explore", "nature", "outdoor",
    "food", "foodie", "yummy", "delicious", "instafood",
    "instadaily", "picoftheday", "instagram", "love", "happy",
    "cute", "beautiful", "summer", "winter", "spring", "autumn",
    "street", "urban", "city", "night", "sunset", "sunrise",
    "minimal", "retro", "vintage", "modern"
]

STYLE_PROMPTS = {
    "Cool": "cool, stylish, badass attitude, swagger",
    "Cute": "cute, adorable, chibi, kawaii",
    "3D": "3D CGI render, blender, unreal engine",
    "Realism": "photorealistic, 4k photograph, detailed texture",
    "Animeart": "anime style, japanese manga"
}

COLOR_PROMPTS = {
    "Colorful": "colorful, many different colors, chaotic rainbow",
    "Hologram": "holographic, iridescent, cd reflection",
    "Neon": "glowing neon lights, cyber colors",
    "Pastel": "pastel colors, soft macaron colors"
}


class ClipService:
    def __init__(self):
        self.device = "cpu"
        self.model = None
        self.processor = None
        self.s_feat = None
        self.c_feat = None
        self.h_feat = None
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        
        print("Loading CLIP model via transformers...")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        s_prompts = []
        for s in STYLES:
            if s in STYLE_PROMPTS:
                txt = STYLE_PROMPTS[s]
            else:
                txt = f"a {s} style artwork"
            s_prompts.append(txt)

        c_prompts = []
        for c in COLORS:
            if c in COLOR_PROMPTS:
                txt = COLOR_PROMPTS[c]
            else:
                txt = f"dominant color is {c}"
            c_prompts.append(txt)
        
        h_prompts = [f"#{tag}" for tag in HASHTAGS]
        
        with torch.no_grad():
            s_inputs = self.processor(text=s_prompts, return_tensors="pt", padding=True).to(self.device)
            c_inputs = self.processor(text=c_prompts, return_tensors="pt", padding=True).to(self.device)
            h_inputs = self.processor(text=h_prompts, return_tensors="pt", padding=True).to(self.device)
            self.s_feat = self.model.get_text_features(**s_inputs)
            self.c_feat = self.model.get_text_features(**c_inputs)
            self.h_feat = self.model.get_text_features(**h_inputs)
            self.s_feat /= self.s_feat.norm(dim=-1, keepdim=True)
            self.c_feat /= self.c_feat.norm(dim=-1, keepdim=True)
            self.h_feat /= self.h_feat.norm(dim=-1, keepdim=True)
        
        self._loaded = True
        print("CLIP model loaded successfully")

    def predict(self, image_bytes: bytes, num_tags: int = 5) -> tuple[str, str, list[str]]:
        self.load()
        
        image = Image.open(BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        with torch.no_grad():
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            img_feat = self.model.get_image_features(**inputs)
            img_feat /= img_feat.norm(dim=-1, keepdim=True)
            
        s_probs = (100.0 * img_feat @ self.s_feat.T).softmax(dim=-1)
        c_probs = (100.0 * img_feat @ self.c_feat.T).softmax(dim=-1)
        h_probs = (100.0 * img_feat @ self.h_feat.T).softmax(dim=-1)
        
        s_idx = s_probs.argmax().item()
        c_idx = c_probs.argmax().item()
        
        top_h_indices = h_probs.topk(num_tags).indices.tolist()
        hashtags = [f"#{HASHTAGS[i]}" for i in top_h_indices]
        
        image.close()
        
        return STYLES[s_idx], COLORS[c_idx], hashtags


clip_service = ClipService()
