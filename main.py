import os
from io import BytesIO
from typing import List

import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image
from transformers import (
    VisionEncoderDecoderModel,
    ViTImageProcessor,
    AutoTokenizer,
)


class TagRequest(BaseModel):
    tags: List[str]


app = FastAPI(title="Image Hashtag API (Qwen3 Local)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve giao diện web tĩnh
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# === Model local: image caption + chuyển caption thành hashtag ===

MODEL_NAME = os.getenv(
    "LOCAL_VISION_MODEL", "nlpconnect/vit-gpt2-image-captioning"
)

device = torch.device("cpu")  # chỉ dùng CPU theo yêu cầu

try:
    vision_model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME).to(device)
    vision_feature_extractor = ViTImageProcessor.from_pretrained(MODEL_NAME)
    vision_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
except Exception as e:
    # Nếu model load lỗi, raise rõ ràng để biết phải cài thêm / tải model
    raise RuntimeError(
        f"Không load được model vision local '{MODEL_NAME}'. "
        f"Chi tiết: {e}"
    )


def generate_caption_from_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Không đọc được ảnh để phân tích.")

    pixel_values = vision_feature_extractor(
        images=[image], return_tensors="pt"
    ).pixel_values.to(device)

    output_ids = vision_model.generate(
        pixel_values,
        max_length=32,
        num_beams=4,
        num_return_sequences=1,
    )
    caption = vision_tokenizer.decode(
        output_ids[0], skip_special_tokens=True
    ).strip()
    return caption


def caption_to_hashtags(caption: str, num_tags: int, language: str) -> List[str]:
    """
    Chuyển caption tiếng Anh đơn giản thành hashtag.
    (Model caption là tiếng Anh; nếu chọn 'vi' vẫn dùng hashtag dạng tiếng Anh.)
    """
    # Tách từ cơ bản
    import re

    words = re.findall(r"[A-Za-z0-9]+", caption.lower())
    # Loại bỏ stopword đơn giản
    stopwords = {
        "a",
        "an",
        "the",
        "of",
        "on",
        "in",
        "and",
        "with",
        "for",
        "to",
        "at",
        "is",
        "are",
        "this",
        "that",
        "it",
        "by",
        "from",
    }
    filtered = [w for w in words if len(w) > 2 and w not in stopwords]

    # Loại trùng, giữ thứ tự
    seen = set()
    unique_words = []
    for w in filtered:
        if w not in seen:
            seen.add(w)
            unique_words.append(w)

    tags = [f"#{w}" for w in unique_words]
    if num_tags > 0:
        tags = tags[:num_tags]
    return tags or ["#content", "#image"]


@app.post("/tag-image", response_model=TagRequest)
async def tag_image(
    file: UploadFile = File(..., description="Ảnh cần đánh hashtag"),
    num_tags: int = Form(10),
    language: str = Form("vi"),
):
    """
    Nhận ảnh (multipart/form-data) và trả về danh sách hashtag sinh bởi Qwen3 local.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File tải lên không phải là ảnh.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=400, detail="Ảnh rỗng hoặc không đọc được."
        )

    caption = generate_caption_from_image(image_bytes)
    tags = caption_to_hashtags(caption, num_tags=num_tags, language=language)

    return TagRequest(tags=tags)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "model_backend": "local_hf_image_caption",
        "vision_model_name": MODEL_NAME,
    }


@app.get("/")
async def index():
    """
    Trả về giao diện web đơn giản để upload nhiều ảnh và đánh hashtag.
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Giao diện web chưa được tạo.")
    return FileResponse(index_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

