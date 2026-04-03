import torch
import threading
import time
from PIL import Image
from io import BytesIO
from transformers import CLIPModel, CLIPProcessor
from typing import Dict, Any

from src.core.logger import get_logger
from src.core.config import config

logger = get_logger(__name__)

from .prompts import (
    STYLE_PROMPT_MAP, COLOR_PROMPT_MAP, SUBJECT_PROMPT_MAP,
    STYLES, COLORS, TAGS_OBJECT, TAGS_MOOD, TAGS_GENDER
)

# ==========================================
# 3. CLASS DỊCH VỤ CLIP
# ==========================================

class ClipService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.loaded_models: Dict[str, Dict[str, Any]] = {}
        self.model_map = {
            "clip-openai": "openai/clip-vit-base-patch32",
            "clip-openclip-laion": "laion/CLIP-ViT-B-32-laion2B-s34B-b79K",
            "clip-openclip-vit-h14": "laion/CLIP-ViT-H-14-laion2B-s32B-b79K",
        }
        self._load_lock = threading.Lock()
        self._inference_locks: Dict[str, threading.Lock] = {}
        self._request_count = 0

    def _get_inference_lock(self, model_key: str) -> threading.Lock:
        if model_key not in self._inference_locks:
            self._inference_locks[model_key] = threading.Lock()
        return self._inference_locks[model_key]

    def load(self, model_key: str = "clip-openai") -> None:
        if model_key in self.loaded_models:
            return
            
        logger.info(f"Thread {threading.get_ident()} waiting to load model '{model_key}'...")
        with self._load_lock:
            if model_key in self.loaded_models:
                return
                
            repo_id = self.model_map.get(model_key, "openai/clip-vit-base-patch32")
            logger.info(f"Loading CLIP model '{model_key}' ({repo_id}) to {self.device}...")
            
            model = CLIPModel.from_pretrained(repo_id).to(self.device)
            processor = CLIPProcessor.from_pretrained(repo_id)
            
            s_prompts = [STYLE_PROMPT_MAP.get(s, f"a {s} style artwork") for s in STYLES]
            c_prompts = [COLOR_PROMPT_MAP.get(c, f"dominant color is {c}") for c in COLORS]
            
            # Khử hashtag cứng, thay bằng ngữ cảnh tự nhiên cực kỳ chi tiết từ SUBJECT_PROMPT_MAP
            obj_prompts = []
            for tag in TAGS_OBJECT:
                if tag == "None":
                    obj_prompts.append("an empty background scene with no main subject, abstract, plain context")
                else:
                    obj_prompts.append(SUBJECT_PROMPT_MAP.get(tag, f"a clear photo of {tag}"))
            
            mood_prompts = []
            for tag in TAGS_MOOD:
                if tag == "None":
                    mood_prompts.append("inanimate object, landscape, neutral scene, abstract image without any emotion")
                else:
                    mood_prompts.append(f"a person, character, or scene strongly expressing a {tag.lower()} feeling or mood")
            
            gender_prompts = []
            for tag in TAGS_GENDER:
                if tag == "None":
                    gender_prompts.append("an object, landscape, or abstract concept without humans, no people, empty scene")
                else:
                    gender_prompts.append(f"a photo or portrait focusing on a {tag.lower()} character")
            
            with torch.no_grad():
                s_inputs = processor(text=s_prompts, return_tensors="pt", padding=True).to(self.device)
                c_inputs = processor(text=c_prompts, return_tensors="pt", padding=True).to(self.device)
                obj_inputs = processor(text=obj_prompts, return_tensors="pt", padding=True).to(self.device)
                mood_inputs = processor(text=mood_prompts, return_tensors="pt", padding=True).to(self.device)
                gender_inputs = processor(text=gender_prompts, return_tensors="pt", padding=True).to(self.device)

                s_feat = model.get_text_features(**s_inputs)
                c_feat = model.get_text_features(**c_inputs)
                obj_feat = model.get_text_features(**obj_inputs)
                mood_feat = model.get_text_features(**mood_inputs)
                gender_feat = model.get_text_features(**gender_inputs)

                s_feat /= s_feat.norm(dim=-1, keepdim=True)
                c_feat /= c_feat.norm(dim=-1, keepdim=True)
                obj_feat /= obj_feat.norm(dim=-1, keepdim=True)
                mood_feat /= mood_feat.norm(dim=-1, keepdim=True)
                gender_feat /= gender_feat.norm(dim=-1, keepdim=True)
            
            self.loaded_models[model_key] = {
                "model": model,
                "processor": processor,
                "s_feat": s_feat,
                "c_feat": c_feat,
                "obj_feat": obj_feat,
                "mood_feat": mood_feat,
                "gender_feat": gender_feat
            }
            logger.info(f"CLIP model '{model_key}' ready.")

    def predict(self, image_bytes: bytes, model_key: str = "clip-openai") -> tuple[str, str, list[str]]:
        self._request_count += 1
        rid = self._request_count
        start_time = time.time()
        
        logger.info(f"[REQ-{rid}] Pipeline start for {len(image_bytes)} bytes")
        self.load(model_key)
        
        m_data = self.loaded_models.get(model_key)
        if not m_data:
            raise Exception(f"Model {model_key} failed to load.")

        model = m_data["model"]
        processor = m_data["processor"]
        
        image = Image.open(BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        logger.info(f"[REQ-{rid}] Waiting for model lock...")
        lock_start = time.time()
        lock = self._get_inference_lock(model_key)
        acquired = lock.acquire(timeout=config.lock_timeout)
        if not acquired:
            logger.error(f"[REQ-{rid}] Lock timeout ({config.lock_timeout}s).")
            raise Exception(f"Server Busy: AI model lock timeout")
            
        try:
            wait_time = time.time() - lock_start
            logger.info(f"[REQ-{rid}] Lock acquired (waited {wait_time:.3f}s). Processing...")
            
            with torch.no_grad():
                inputs = processor(images=image, return_tensors="pt").to(self.device)
                img_feat = model.get_image_features(**inputs)
                img_feat /= img_feat.norm(dim=-1, keepdim=True)
                
            s_probs = (100.0 * img_feat @ m_data["s_feat"].T).softmax(dim=-1)
            c_probs = (100.0 * img_feat @ m_data["c_feat"].T).softmax(dim=-1)
            obj_probs = (100.0 * img_feat @ m_data["obj_feat"].T).softmax(dim=-1)
            mood_probs = (100.0 * img_feat @ m_data["mood_feat"].T).softmax(dim=-1)
            gender_probs = (100.0 * img_feat @ m_data["gender_feat"].T).softmax(dim=-1)
            
            s_idx = s_probs.argmax().item()
            mood_idx = mood_probs.argmax().item()
            gender_idx = gender_probs.argmax().item()

            # ── Object: lọc theo threshold
            # Có ~180 object => random chance là ~0.55%.
            # Threshold = 2.0% (mức tin tưởng cao hơn random gấp ~4 lần)
            OBJ_THRESHOLD = 0.02
            obj_scores = obj_probs[0]
            obj_top2_indices = obj_scores.topk(2).indices.tolist()
            
            obj1 = "None"
            obj2 = "None"
            
            if obj_scores[obj_top2_indices[0]].item() >= OBJ_THRESHOLD:
                obj1 = TAGS_OBJECT[obj_top2_indices[0]]
            if obj_scores[obj_top2_indices[1]].item() >= OBJ_THRESHOLD:
                obj2 = TAGS_OBJECT[obj_top2_indices[1]]

            hashtags = [
                obj1,
                obj2,
                TAGS_MOOD[mood_idx],
                TAGS_GENDER[gender_idx]
            ]

            # ── Color: chỉ nhận màu khi model đủ tự tin (vượt threshold)
            # Threshold 0.10 = cần ít nhất 2.3x tự tin hơn chọn ngẫu nhiên (1/23 ≈04.35%)
            COLOR_THRESHOLD = 0.10
            c_vals = c_probs[0]
            c_max_score = c_vals.max().item()
            c_idx = c_vals.argmax().item()
            final_color = COLORS[c_idx] if c_max_score >= COLOR_THRESHOLD else "None"
            logger.info(f"[REQ-{rid}] Color: {COLORS[c_idx]} score={c_max_score:.4f} "
                        f"({'accepted' if c_max_score >= COLOR_THRESHOLD else 'REJECTED -> None'})")

            image.close()
            return STYLES[s_idx], final_color, hashtags
        finally:
            lock.release()
            logger.info(f"[REQ-{rid}] Released lock. Total: {time.time() - start_time:.3f}s")

clip_service = ClipService()