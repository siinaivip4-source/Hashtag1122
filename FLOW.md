# Flow Xử Lý Hashtag

## Tổng Quan

Khi người dùng bấm nút "Chạy Hashtag" trên giao diện web, hệ thống sẽ thực hiện một chuỗi các bước xử lý từ backend để phân tích hình ảnh và trả về kết quả bao gồm: caption, hashtags, style, color, và clip_hashtags.

---

## Chi Tiết Từng Bước

### Bước 1: Gửi Request từ Client

Người dùng tải lên file hình ảnh thông qua giao diện web. Request được gửi đến API endpoint `/tag-image` với các tham số:

- `file`: File hình ảnh (UploadFile)
- `num_tags`: Số lượng tags muốn nhận (mặc định: 10)
- `model`: Model vision sử dụng (vit-gpt2, blip-base, git-base)
- `custom_vocabulary`: Danh sách từ khóa tùy chỉnh (comma-separated)
- `mode`: Chế độ xử lý (clip, vision, hoặc both)

### Bước 2: Validate Request tại API Endpoint

Tại `src/api/routes/image.py:55-90`, endpoint `tag_image`:

1. **Kiểm tra content type**: Đảm bảo file là hình ảnh (`image/*`)
   - Nếu không phải → Trả về HTTP 400 "File is not an image"

2. **Đọc image bytes**: Đọc nội dung file vào biến `image_bytes`
   - Nếu rỗng → Trả về HTTP 400 "Empty or unreadable image"

3. **Parse tham số**:
   - `num_tags`: Chuyển đổi sang số nguyên, mặc định lấy từ `config.default_num_tags`
   - `custom_keywords`: Tách chuỗi custom_vocabulary thành list, loại bỏ khoảng trắng thừa

### Bước 3: Chuyển Xử Lý Sang ThreadPoolExecutor

Vì xử lý hình ảnh với ML models là CPU-bound operations, API sử dụng `asyncio.get_event_loop().run_in_executor()` để chạy trong ThreadPoolExecutor, tránh blocking event loop:

```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    None,
    partial(_process_image_bytes, image_bytes, model, num_tags, custom_keywords, mode)
)
```

### Bước 4: Xử Lý Hình Ảnh (_process_image_bytes)

Hàm `src/api/routes/image.py:18-43` thực hiện:

#### 4.1. Xử Lý Vision Mode (nếu mode = "vision" hoặc "both")

- **Gọi** `vision_service.generate_caption(image_bytes, model_key)`
- **Tại** `src/services/vision.py:111-122`:
  1. Lấy model instance theo model_key (vit-gpt2, blip-base, hoặc git-base)
  2. Load model nếu chưa load (lazy loading)
  3. Mở image bằng PIL, convert sang RGB
  4. Gọi `instance.generate(image)`:
     - **VitGPT2Model**: Sử dụng VisionEncoderDecoderModel
     - **BlipModel**: Sử dụng BlipForConditionalGeneration
     - **GitModel**: Sử dụng AutoModelForCausalLM
  5. Trả về caption (mô tả văn bản về hình ảnh)

- **Chuyển Caption thành Hashtags**: Gọi `caption_to_hashtags(caption, num_tags, custom_keywords)`
- **Tại** `src/services/hashtag.py:10-43`:
  1. Nếu có `custom_keywords`: Match từ khóa trong caption, format thành hashtags
  2. Nếu không: Trích xuất từ khóa từ caption (loại stopwords, lọc từ > 2 ký tự, loại bỏ trùng lặp)
  3. Format thành hashtags `#word`, giới hạn `num_tags` tags

#### 4.2. Xử Lý CLIP Mode (nếu mode = "clip" hoặc "both")

- **Gọi** `clip_service.predict(image_bytes, num_tags)`
- **Tại** `src/services/clip.py:149-183`:
  1. Load CLIP model nếu chưa load (`openai/clip-vit-base-patch32`)
  2. Mở image bằng PIL, convert sang RGB
  3. Trích xuất image features bằng CLIP
  4. Tính similarity với:
     - **Style prompts** (18 styles: 2D, 3D, Anime, Realism,...)
     - **Color prompts** (23 colors: Black, White, Red,...)
     - **Object tags** (hàng trăm tags: sport, animal, anime,...)
     - **Mood tags** (Happy, Sad, Lonely,...)
     - **Gender tags** (Boy, Girl, Man,...)
  5. Trả về: `(style, color, clip_hashtags)`
     - `style`: Style có độ tương đồng cao nhất
     - `color`: Color có độ tương đồng cao nhất
     - `clip_hashtags`: List 3 tags [object, mood, gender]

### Bước 5: Trả Kết Quả Về Client

Tổng hợp kết quả và trả về `TagResponse`:

```python
return TagResponse(
    tags=result["tags"],           # Hashtags từ caption (Vision)
    caption=result["caption"],     # Mô tả hình ảnh (Vision)
    style=result["style"],         # Style dự đoán (CLIP)
    color=result["color"],         # Color dự đoán (CLIP)
    clip_hashtags=result["clip_hashtags"]  # [object, mood, gender] từ CLIP
)
```

Định nghĩa tại `src/schemas/response.py:16-21`:

```python
class TagResponse(BaseModel):
    tags: List[str] = []       # Vision hashtags
    caption: str = ""          # Vision caption
    style: str = ""            # CLIP style
    color: str = ""            # CLIP color
    clip_hashtags: List[str] = []  # CLIP [object, mood, gender]
```

---

## Sơ Đồ Flow

```
┌─────────────────┐
│  User clicks    │
│  "Run Hashtag"  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  POST /tag-image (or /url)      │
│  - file / url                   │
│  - num_tags                     │
│  - model                        │
│  - custom_vocabulary            │
│  - mode                         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Validate Request               │
│  - Check image/* content type  │
│  - Read image bytes             │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  run_in_executor                │
│  (ThreadPoolExecutor)           │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────────┐ ┌──────────┐
│  VISION  │ │   CLIP   │
│   MODE   │ │   MODE   │
└────┬─────┘ └────┬─────┘
     │            │
     ▼            ▼
┌────────────┐ ┌────────────┐
│  Generate  │ │   CLIP     │
│  Caption   │ │  Predict   │
│ (ViT-GPT2/ │ │  - Style   │
│  BLIP/     │ │  - Color   │
│  GIT)      │ │  - Tags    │
└────┬───────┘ └─────┬──────┘
     │               │
     ▼               ▼
┌────────────┐ ┌────────────┐
│  Caption   │ │  (style,   │
│    to      │ │  color,   │
│  Hashtags  │ │  hashtags) │
└────┬───────┘ └────────────┘
     │               │
     └───────┬───────┘
             │
             ▼
┌─────────────────────────────────┐
│  TagResponse                    │
│  - tags                         │
│  - caption                      │
│  - style                        │
│  - color                        │
│  - clip_hashtags               │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Return JSON to Client          │
└─────────────────────────────────┘
```

---

## Các Model Được Sử Dụng

### Vision Models (Caption Generation)

| Model | HuggingFace ID | Mô Tả |
|-------|----------------|-------|
| vit-gpt2 | nlpconnect/vit-gpt2-image-captioning | Vision Encoder Decoder với ViT + GPT2 |
| blip-base | Salesforce/blip-image-captioning-base | BLIP (Bootstrapped Language-Image Pre-training) |
| git-base | microsoft/git-base | GIT (Generative Image-to-text) |

### CLIP Model

| Model | HuggingFace ID | Mục Đích |
|-------|----------------|----------|
| clip-vit-base-patch32 | openai/clip-vit-base-patch32 | Phân loại style, color, object, mood, gender |

---

# Tài Liệu Chi Tiết CLIP Model (openai/clip-vit-base-patch32)

## 1. Tổng Quan CLIP

**CLIP (Contrastive Language-Image Pre-Training)** là model multimodal của OpenAI, được phát triển vào **tháng 1/2021**, kết nối giữa hình ảnh và văn bản trong một không gian embedding chung. CLIP nổi bật với khả năng **zero-shot image classification** - phân loại hình ảnh vào bất kỳ danh mục nào mà không cần fine-tuning.

### Đặc điểm nổi bật:
- **Dual Encoders**: Vision Transformer + Text Transformer
- **Training data**: 400 triệu cặp (image, text)
- **Zero-shot transfer**: Không cần training thêm cho downstream tasks
- **Multimodal**: Hiểu cả hình ảnh và văn bản

---

## 2. Kiến Trúc Model

### 2.1. Image Encoder (ViT-B/32)

```
Input Image (224x224)
       │
       ▼
┌──────────────────┐
│  Patch Division  │  Chia ảnh thành 16x16 patches
│  (32x32 pixels)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Linear Projection│  Flatten + Position Embedding
│  + CLS Token     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Transformer     │  12 layers, 768 hidden, 12 heads
│  Encoder         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Output          │  512-dim image embedding
│  (pooled)        │
└──────────────────┘
```

**Thông số kỹ thuật:**
| Thông số | Giá trị |
|----------|---------|
| Image Size | 224 x 224 |
| Patch Size | 32 x 32 |
| Hidden Size | 768 |
| Layers | 12 |
| Attention Heads | 12 |
| Output Dimension | 512 |

### 2.2. Text Encoder (Transformer)

```
Input Text (77 tokens max)
       │
       ▼
┌──────────────────┐
│  Byte-level BPE  │  Tokenizer (vocab: 49408)
│  Tokenization    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Positional      │  Position Embeddings
│  Embeddings      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Transformer     │  12 layers, 512 hidden, 8 heads
│  Encoder         │  (masked self-attention)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  [EOS] Token     │  Lấy output tại vị trí [EOS]
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Linear Project  │  Project to 512-dim
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Output          │  512-dim text embedding
│  (normalized)    │
└──────────────────┘
```

**Thông số kỹ thuật:**
| Thông số | Giá trị |
|----------|---------|
| Vocab Size | 49408 |
| Max Position | 77 |
| Hidden Size | 512 |
| Layers | 12 |
| Attention Heads | 8 |
| Output Dimension | 512 |

### 2.3. Contrastive Learning

```
Batch N pairs: {(image₁, text₁), (image₂, text₂), ..., (imageₙ, textₙ)}

Image Encoder     Text Encoder
     │                  │
     ▼                  ▼
 I₁, I₂, ..., Iₙ   T₁, T₂, ..., Tₙ
     │                  │
     └────────┬─────────┘
              │
              ▼
    ┌─────────────────┐
    │ Linear Project  │  Project to same dim
    │ (both to 512)   │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Temperature τ   │  Trainable scalar
    │ compute:        │
    │ s = I · T^T     │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Contrastive    │  Symmetric cross-entropy
    │ Loss           │  Nx2 classification
    └─────────────────┘
```

---

## 3. Cách CLIP Hoạt Động Trong Dự Án

### 3.1. Quá Trình Load Model

Tại `src/services/clip.py:112-147`:

```python
def load(self):
    # Load CLIP model và processor
    self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    # Tạo text prompts cho từng category
    s_prompts = [STYLE_PROMPT_MAP.get(s, f"a {s} style artwork") for s in STYLES]
    c_prompts = [COLOR_PROMPT_MAP.get(c, f"dominant color is {c}") for c in COLORS]
    obj_prompts = [f"#{tag}" for tag in TAGS_OBJECT]
    mood_prompts = [f"feeling {tag.lower()}" for tag in TAGS_MOOD]
    gender_prompts = [f"a photo of a {tag.lower()}" for tag in TAGS_GENDER]
    
    # Encode tất cả prompts một lần (cache)
    with torch.no_grad():
        s_inputs = self.processor(text=s_prompts, return_tensors="pt", padding=True)
        s_feat = self.model.get_text_features(**s_inputs)
        s_feat /= s_feat.norm(dim=-1, keepdim=True)
        self.s_feat = s_feat
        # ... tương tự cho các category khác
```

### 3.2. Quá Trình Dự Đoán

Tại `src/services/clip.py:149-183`:

```python
def predict(self, image_bytes: bytes, num_tags: int = 5):
    # B1: Load và preprocess image
    image = Image.open(BytesIO(image_bytes))
    image = image.convert("RGB")
    
    # B2: Extract image features
    inputs = self.processor(images=image, return_tensors="pt")
    img_feat = self.model.get_image_features(**inputs)
    img_feat /= img_feat.norm(dim=-1, keepdim=True)
    
    # B3: Compute similarity với từng category
    # Style: Image · Style^T → softmax → argmax
    s_probs = (100.0 * img_feat @ self.s_feat.T).softmax(dim=-1)
    s_idx = s_probs.argmax().item()
    
    # Color: Image · Color^T → softmax → argmax
    c_probs = (100.0 * img_feat @ self.c_feat.T).softmax(dim=-1)
    c_idx = c_probs.argmax().item()
    
    # Object, Mood, Gender: tương tự
    obj_probs = (100.0 * img_feat @ self.obj_feat.T).softmax(dim=-1)
    mood_probs = (100.0 * img_feat @ self.mood_feat.T).softmax(dim=-1)
    gender_probs = (100.0 * img_feat @ self.gender_feat.T).softmax(dim=-1)
    
    # B4: Trả kết quả
    return STYLES[s_idx], COLORS[c_idx], [TAGS_OBJECT[obj_idx], TAGS_MOOD[mood_idx], TAGS_GENDER[gender_idx]]
```

### 3.3. Prompt Engineering

CLIP sử dụng **prompt engineering** để tăng độ chính xác:

| Category | Template Example |
|----------|------------------|
| Style | "a photo of a cat", "flat 2d vector art" |
| Color | "dominant color is red", "black clothing" |
| Object | "#cat", "#dog", "#football" |
| Mood | "feeling happy", "feeling sad" |
| Gender | "a photo of a man", "a photo of a woman" |

---

## 4. Categories Được Sử Dụng Trong Dự Án

### 4.1. Styles (18 categories)

```python
STYLES = [
    "2D", "3D", "Cute", "Animeart", "Realism",
    "Aesthetic", "Cool", "Fantasy", "Comic", "Horror",
    "Cyberpunk", "Lofi", "Minimalism", "Digitalart", "Cinematic",
    "Pixelart", "Scifi", "Vangoghart"
]
```

### 4.2. Colors (23 categories)

```python
COLORS = [
    "Black", "White", "Blackandwhite", "Red", "Yellow",
    "Blue", "Green", "Pink", "Orange", "Pastel",
    "Hologram", "Vintage", "Colorful", "Neutral", "Light",
    "Dark", "Warm", "Cold", "Neon", "Gradient",
    "Purple", "Brown", "Grey"
]
```

### 4.3. Objects (400+ tags)

Được phân theo nhóm:
- **Sports**: sport, football, messi, ronaldo, barcelona, ...
- **Animals**: lion, wolf, dog, cat, panda, dragon, ...
- **Anime**: goku, luffy, naruto, pokemon, ...
- **Movies**: batman, spiderman, ironman, ...
- **Nature**: mountain, beach, sunset, ocean, ...
- **Vehicles**: car, porsche, lamborghini, ferrari, ...
- **Food**: food, fruit, drink, coffee, ...
- Và nhiều nhóm khác...

### 4.4. Mood & Gender

```python
TAGS_MOOD = ["Happy", "Sad", "Lonely", "Chill", "Funny", "None"]
TAGS_GENDER = ["Boy", "Girl", "Man", "Woman", "Couple", "None"]
```

---

## 5. Prompt Mapping Chi Tiết

### 5.1. Style Prompts

| Style | Prompt Description |
|-------|-------------------|
| 2D | flat 2d vector art, simple lines, cartoon illustration |
| 3D | 3d computer graphics, blender render, c4d, volumetric lighting |
| Animeart | anime style, japanese manga, cel shading, waifu |
| Realism | real life photography, 4k photo, hyperrealistic |
| Cyberpunk | cyberpunk city, neon lights, high tech low life |
| ... | ... |

### 5.2. Color Prompts

| Color | Prompt Description |
|-------|-------------------|
| Black | black clothing, black outfit, matte black material |
| White | white clothing, bright white surface, ivory elegance |
| Red | bright red clothing, crimson object, ruby radiance |
| Neon | glowing neon signs, cyberpunk lights, laser beam |
| Warm | warm lighting, golden hour, cozy atmosphere |
| ... | ... |

---

## 6. Performance & Benchmarks

### 6.1. Zero-Shot Performance (từ paper)

| Dataset | CLIP ViT-B/32 |
|---------|---------------|
| ImageNet | 59.5% |
| CIFAR-10 | 85.4% |
| CIFAR-100 | 60.8% |
| STL-10 | 81.8% |
| Food101 | 84.0% |
| Flowers102 | 93.5% |
| SVHN | 60.4% |
| DTD | 54.6% |

### 6.2. Inference Speed (ước tính)

| Hardware | Batch Size | FPS |
|----------|------------|-----|
| CPU (i7-10700) | 1 | ~3-5 |
| CPU (i7-10700) | 4 | ~8-12 |
| GPU (RTX 3080) | 1 | ~50-80 |
| GPU (RTX 3080) | 32 | ~200-300 |

---

## 7. Limitations & Considerations

### 7.1. Hạn chế của CLIP

- **Fine-grained classification**: Khó phân loại chi tiết (vd: giống chó cụ thể)
- **Counting**: Không đếm được số lượng objects
- **Spatial relationships**: Không hiểu quan hệ không gian ("trên", "dưới", "trong")
- **Complex reasoning**: Không推理 phức tạp
- **English only**: Chỉ hỗ trợ tiếng Anh

### 7.2. Best Practices

1. **Sử dụng prompts chi tiết**: "a photo of a cat" tốt hơn "cat"
2. **Ensemble multiple prompts**: Kết hợp nhiều variations
3. **Temperature scaling**: Dùng `softmax` với temperature phù hợp
4. **Cache text features**: Encode prompts một lần, tái sử dụng

---

## 8. Code Reference

### 8.1. Load Model

```python
from transformers import CLIPModel, CLIPProcessor

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
```

### 8.2. Zero-Shot Classification

```python
from PIL import Image
import torch

# Load image
image = Image.open("image.jpg")

# Define labels
labels = ["a photo of a cat", "a photo of a dog", "a photo of a car"]

# Encode
inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)
outputs = model(**inputs)

# Get probabilities
logits_per_image = outputs.logits_per_image
probs = logits_per_image.softmax(dim=1)

# Result
predicted_class = labels[probs.argmax()]
print(f"Predicted: {predicted_class} ({probs.max().item():.2f})")
```

### 8.3. Image-Text Similarity

```python
# Get embeddings
image_emb = model.get_image_features(**image_inputs)
text_emb = model.get_text_features(**text_inputs)

# Normalize
image_emb = image_emb / image_emb.norm(dim=-1, keepdim=True)
text_emb = text_emb / text_emb.norm(dim=-1, keepdim=True)

# Similarity (cosine = dot product vì đã normalize)
similarity = (image_emb @ text_emb.T) * 100  # scale up
```

---

## 9. Tài Liệu Tham Khảo

- **Paper**: [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020)
- **Blog**: [OpenAI CLIP Blog Post](https://openai.com/blog/clip)
- **HuggingFace**: [openai/clip-vit-base-patch32](https://huggingface.co/openai/clip-vit-base-patch32)
- **GitHub**: [openai/CLIP](https://github.com/openai/CLIP)

---

## 10. License

Apache 2.0 - Có thể sử dụng cho cả mục đích thương mại và phi thương mại.

---

## Các Endpoint Liên Quan

| Endpoint | Method | Mô Tả |
|----------|--------|-------|
| `/tag-image` | POST | Xử lý single image (upload file) |
| `/tag-image/url` | POST | Xử lý single image từ URL |
| `/tag-image/urls-batch` | POST | Xử lý nhiều images (max 50) với threading |
| `/health` | GET | Health check API |

---

## Tham Số Mode

| Mode | Vision | CLIP | Kết Quả Trả Về |
|------|--------|------|----------------|
| `vision` | ✅ | ❌ | tags, caption |
| `clip` | ❌ | ✅ | style, color, clip_hashtags |
| `both` | ✅ | ✅ | Tất cả |

---

##Ví Dụ Response

```json
{
    "tags": [
        "#sunset",
        "#beach",
        "#ocean",
        "#sky",
        "#summer"
    ],
    "caption": "A beautiful sunset over the ocean with golden sky",
    "style": "Aesthetic",
    "color": "Warm",
    "clip_hashtags": [
        "nature",
        "Chill",
        "None"
    ]
}
```
