# Flow Xử Lý Hashtag

## Tổ Quan

Khi người dùng bấm nút "Chạy Hashtag" trên giao diện web, hệ thống sẽ phân tích hình ảnh và trả về: style, color, và clip_hashtags (object, mood, gender).

**Lưu ý**: Hiện tại chỉ có **CLIP mode** đang hoạt động. Vision mode (caption generation) chưa được kích hoạt.

---

## Chi Tiết Từng Bước

### Bước 1: Gửi Request từ Client

Người dùng tải lên file hình ảnh thông qua giao diện web. Request được gửi đến API endpoint `/tag-image` với các tham số:

- `file`: File hình ảnh (UploadFile)
- `num_tags`: Số lượng tags muốn nhận (mặc định: 5) - **Chưa hoạt động**
- `model`: Model vision sử dụng - **Chưa hoạt động**
- `custom_vocabulary`: Danh sách từ khóa tùy chỉnh - **Chưa hoạt động**
- `mode`: Chế độ xử lý (clip) - **Hiện tại chỉ hỗ trợ clip**

### Bước 2: Validate Request tại API Endpoint

Tại `src/api/routes/image.py:69-104`, endpoint `tag_image`:

1. **Kiểm tra content type**: Đảm bảo file là hình ảnh (`image/*`)
   - Nếu không phải → HTTP 400 "File is not an image"

2. **Đọc image bytes**: Đọc nội dung file vào biến `image_bytes`
   - Nếu rỗng → HTTP 400 "Empty or unreadable image"

3. **Parse tham số**:
   - `num_tags`: Chuyển đổi sang số nguyên, mặc định từ `config.default_num_tags`
   - `custom_keywords`: Tách chuỗi custom_vocabulary thành list

### Bước 3: Chuyển Xử Lý Sang ThreadPoolExecutor

Vì xử lý hình ảnh với ML models là CPU-bound, API sử dụng `asyncio.get_event_loop().run_in_executor()` để chạy trong ThreadPoolExecutor:

```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    None,
    partial(_process_image_bytes, image_bytes, model, num_tags, custom_keywords, mode)
)
```

### Bước 4: Xử Lý Hình Ảnh (_process_image_bytes)

Tại `src/api/routes/image.py:16-35`:

#### 4.1. CLIP Mode (Đang hoạt động)

- **Gọi** `clip_service.predict(image_bytes, num_tags)`
- **Tại** `src/services/clip.py:149-183`:
  1. Load CLIP model nếu chưa load (`openai/clip-vit-base-patch32`)
  2. Mở image bằng PIL, convert sang RGB
  3. Trích xuất image features bằng CLIP vision encoder
  4. Tính similarity với:
     - **Style prompts** (18 styles)
     - **Color prompts** (23 colors)
     - **Object tags** (400+ tags)
     - **Mood tags** (6 tags)
     - **Gender tags** (6 tags)
  5. Trả về: `(style, color, clip_hashtags)`
     - `style`: Style có độ tương đồng cao nhất
     - `color`: Color có độ tương đồng cao nhất
     - `clip_hashtags`: List 3 tags [object, mood, gender]

#### 4.2. Vision Mode (Chưa hoạt động)

Hiện tại không hoạt động - `tags` và `caption` luôn trả về rỗng.

### Bước 5: Trả Kết Quả Về Client

Tại `src/api/routes/image.py:98-104`:

```python
return TagResponse(
    tags=result["tags"],           # [] (rỗng - vision chưa hoạt động)
    caption=result["caption"],     # "" (rỗng - vision chưa hoạt động)
    style=result["style"],         # Style từ CLIP
    color=result["color"],         # Color từ CLIP
    clip_hashtags=result["clip_hashtags"]  # [object, mood, gender]
)
```

Định nghĩa tại `src/schemas/response.py:16-21`:

```python
class TagResponse(BaseModel):
    tags: List[str] = []       # Vision hashtags (rỗng)
    caption: str = ""          # Vision caption (rỗng)
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
         ▼
┌─────────────────────────────────┐
│  CLIP Mode (Active)             │
│  - Load CLIP model              │
│  - Extract image features       │
│  - Compute similarity           │
│  - Return top predictions       │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  TagResponse                    │
│  - tags: [] (chưa hoạt động)   │
│  - caption: "" (chưa hoạt động)│
│  - style: "Realism"             │
│  - color: "Blue"                │
│  - clip_hashtags: [obj,mood,gen]│
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Return JSON to Client          │
└─────────────────────────────────┘
```

---

## Các Endpoint

| Endpoint | Method | Mô Tả |
|----------|--------|-------|
| `/tag-image` | POST | Xử lý single image (upload file) |
| `/tag-image/url` | POST | Xử lý single image từ URL |
| `/tag-image/urls-batch` | POST | Xử lý nhiều images (max 50) với threading |
| `/tag-image/load-model` | POST | Pre-load CLIP model |
| `/health` | GET | Health check API |

---

## CLIP Model (openai/clip-vit-base-patch32)

### Kiến Trúc

- **Image Encoder**: ViT-B/32 (Vision Transformer)
  - Input: 224x224 pixels
  - Patch size: 32x32
  - Output: 512-dim embedding
- **Text Encoder**: Transformer 12-layer
  - Vocab: 49408 tokens
  - Max length: 77
  - Output: 512-dim embedding

### Categories Được Sử Dụng

#### Styles (18)

```
2D, 3D, Cute, Animeart, Realism, Aesthetic, Cool, Fantasy, Comic, 
Horror, Cyberpunk, Lofi, Minimalism, Digitalart, Cinematic, Pixelart, Scifi, Vangoghart
```

#### Colors (23)

```
Black, White, Blackandwhite, Red, Yellow, Blue, Green, Pink, Orange, 
Pastel, Hologram, Vintage, Colorful, Neutral, Light, Dark, Warm, Cold, 
Neon, Gradient, Purple, Brown, Grey
```

#### Object Tags (400+)

Categories: Sports, Animals, Anime, Movies, Cartoons, Games, Nature, Vehicles, Food, Religion, Holiday, và nhiều nhóm khác.

#### Mood (6)

```
Happy, Sad, Lonely, Chill, Funny, None
```

#### Gender (6)

```
Boy, Girl, Man, Woman, Couple, None
```

---

## Response Ví Dụ

```json
{
    "tags": [],
    "caption": "",
    "style": "Animeart",
    "color": "Blue",
    "clip_hashtags": [
        "anime",
        "Happy",
        "Boy"
    ]
}
```

---

## Vấn Đề Cần Cải Tiến

| Issue | Mô Tả |
|-------|-------|
| Vision mode | Chưa hoạt động - cần kích hoạt caption generation |
| num_tags | Parameter được truyền nhưng không ảnh hưởng kết quả |
| Multi-object | Chỉ trả về top 1 object, không phải top N |
| GPU support | Luôn chạy trên CPU |
