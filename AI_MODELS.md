# Tài liệu về các Model AI trong Project

Project này sử dụng các model Deep Learning (Học sâu) tiên tiến để thực hiện nhiệm vụ **Image Captioning** (Tạo chú thích cho ảnh). Các model này được tích hợp thông qua thư viện `transformers` của Hugging Face.

## 1. Danh sách các Model được sử dụng

Cấu hình hiện tại trong `config.yaml` hỗ trợ 3 model chính:

### 1.1. ViT-GPT2 (`vit-gpt2`)
- **Tên đầy đủ**: `nlpconnect/vit-gpt2-image-captioning`
- **Kiến trúc**: Kết hợp giữa **Vision Transformer (ViT)** để xử lý hình ảnh và **GPT-2** để sinh văn bản.
- **Đặc điểm**:
    - **Encoder**: Sử dụng ViT để trích xuất đặc trưng từ ảnh.
    - **Decoder**: Sử dụng GPT-2 để giải mã các đặc trưng ảnh thành chuỗi văn bản mô tả.
- **Ưu điểm**: Tốc độ xử lý nhanh, mô hình nhẹ, phù hợp cho các tác vụ image captioning cơ bản.
- **Class cài đặt**: `VitGPT2Model` trong `src/services/vision.py`.

### 1.2. BLIP Base (`blip-base`)
- **Tên đầy đủ**: `Salesforce/blip-image-captioning-base`
- **Kiến trúc**: **BLIP (Bootstrapping Language-Image Pre-training)**.
- **Đặc điểm**:
    - Được huấn luyện trên tập dữ liệu quy mô lớn (image-text pairs).
    - Có khả năng hiểu ngữ nghĩa hình ảnh tốt hơn và sinh ra mô tả tự nhiên hơn so với các model cũ.
    - Sử dụng `BlipProcessor` và `BlipForConditionalGeneration`.
- **Ưu điểm**: Hiệu suất tốt trên nhiều loại ảnh khác nhau, cân bằng giữa tốc độ và độ chính xác.
- **Class cài đặt**: `BlipModel` trong `src/services/vision.py`.

### 1.3. GIT Base (`git-base`)
- **Tên đầy đủ**: `microsoft/git-base`
- **Kiến trúc**: **GIT (Generative Image-to-text Transformer)**.
- **Đặc điểm**:
    - Là một kiến trúc đơn giản nhưng mạnh mẽ, coi việc mô tả ảnh như một bài toán mô hình hóa ngôn ngữ thuần túy, với đầu vào là ảnh.
    - Sử dụng `AutoProcessor` và `AutoModelForCausalLM`.
- **Ưu điểm**: Thường cho kết quả rất tốt trên các benchmark image captioning hiện đại.
- **Class cài đặt**: `GitModel` trong `src/services/vision.py`.

## 2. Cấu trúc và Cách thức hoạt động

### 2.1. Cấu hình (`config.yaml`)
Việc lựa chọn model được định nghĩa trong file `config.yaml`:

```yaml
model:
  default: "vit-gpt2"  # Model mặc định khi khởi chạy
  available:
    vit-gpt2: "nlpconnect/vit-gpt2-image-captioning"
    blip-base: "Salesforce/blip-image-captioning-base"
    git-base: "microsoft/git-base"
```

Các tham số xử lý chung cho các model:
- `max_length`: Độ dài tối đa của câu mô tả (mặc định: 32 token).
- `num_beams`: Số lượng beams trong thuật toán beam search (mặc định: 4) để tìm ra câu mô tả tốt nhất.

### 2.2. Kiến trúc Code (`src/services/vision.py`)

Hệ thống sử dụng **Factory Pattern** và kế thừa để quản lý các model:

1.  **BaseModel (Lớp cha)**:
    - Định nghĩa interface chung cho tất cả các model.
    - Các phương thức chính: `load()` (tải model) và `generate(image)` (sinh mô tả).

2.  **Các lớp Model cụ thể**:
    - `VitGPT2Model`: Cài đặt logic riêng cho ViT-GPT2.
    - `BlipModel`: Cài đặt logic riêng cho BLIP.
    - `GitModel`: Cài đặt logic riêng cho GIT.
    - Mỗi lớp sẽ tự quản lý việc tải `processor`, `tokenizer` và `model` weights tương ứng từ Hugging Face Hub (hoặc cache local).

3.  **VisionService (Lớp quản lý)**:
    - Quản lý việc khởi tạo và lưu trữ các instance của model (`loaded_models`).
    - Phương thức `get_model_instance(model_key)`:
        - Kiểm tra xem model đã được tải chưa.
        - Nếu chưa, khởi tạo instance mới tương ứng với `model_key` (vit-gpt2, blip-base, hoặc git-base).
        - Trả về instance để sử dụng.
    - Phương thức `generate_caption(image_bytes, model_key)`:
        - Nhận ảnh đầu vào dưới dạng bytes.
        - Gọi `get_model_instance` để lấy đúng model người dùng yêu cầu.
        - Thực hiện `generate()` để lấy kết quả mô tả.

## 3. Cách thêm Model mới

Để thêm một model mới vào project, cần thực hiện các bước sau:

1.  **Cập nhật `config.yaml`**:
    - Thêm `key: "huggingface/path"` vào phần `model.available`.

2.  **Tạo Class Model mới trong `src/services/vision.py`**:
    - Tạo class mới kế thừa từ `BaseModel`.
    - Implement phương thức `load()` để tải model.
    - Implement phương thức `generate()` để xử lý ảnh và sinh text.

3.  **Cập nhật `VisionService`**:
    - Thêm logic `elif` trong phương thức `get_model_instance` để nhận diện model mới và khởi tạo class tương ứng.
