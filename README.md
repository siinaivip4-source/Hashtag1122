## Image Hashtag API với Qwen3 Local

Project này cung cấp một API đơn giản (FastAPI) để nhận ảnh và sinh ra danh sách hashtag phục vụ đăng bài content, sử dụng mô hình Qwen3 (hoặc Qwen-VL) chạy local trên máy tính.

### 1. Yêu cầu môi trường

- Python 3.10+ (khuyến nghị)
- Windows 10/11
- Một server Qwen3 / Qwen-VL chạy local và **phơi bày API tương thích OpenAI** (ví dụ qua vLLM, Ollama, ModelScope…).

> Lưu ý: Code này giả định server có endpoint `/v1/chat/completions` giống OpenAI và hỗ trợ input hình ảnh.

### 2. Cài đặt dependency

Trong thư mục project:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Cấu hình Qwen3 local

Tạo file `.env` cùng cấp với `main.py` (có thể copy từ ví dụ dưới và chỉnh lại):

```bash
QWEN_API_BASE=http://localhost:11434/v1
QWEN_API_KEY=EMPTY
QWEN_MODEL_NAME=qwen3-vl
```

- **QWEN_API_BASE**: base URL của server Qwen3 local.
- **QWEN_API_KEY**: nếu server không yêu cầu key, có thể để `EMPTY`.
- **QWEN_MODEL_NAME**: tên model trên server (ví dụ: `qwen3-vl`, `qwen-vl`, tùy cấu hình).

### 4. Chạy API

```bash
.venv\Scripts\activate
python main.py
```

Mặc định API sẽ chạy tại `http://localhost:8000`.

- Kiểm tra health:
  - `GET http://localhost:8000/health`

### 5. Endpoint đánh hashtag ảnh

- **Method**: `POST`
- **URL**: `http://localhost:8000/tag-image`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: file ảnh (bắt buộc)
  - `num_tags`: số lượng hashtag muốn sinh (mặc định 10)
  - `language`: ngôn ngữ hashtag, `vi` (mặc định) hoặc `en`

**Response mẫu**:

```json
{
  "tags": [
    "#coffee",
    "#morningvibes",
    "#coffeetime"
  ]
}
```

Bạn có thể test nhanh bằng Postman, Apidog hoặc frontend bất kỳ gửi form-data.

### 6. Tùy biến prompt

Logic tạo prompt hiện nằm trong hàm `build_prompt` trong `main.py`.  
Bạn có thể chỉnh lại giọng văn, độ “content”, thêm yêu cầu về niche, brand, v.v. để phù hợp với use case của mình.

