# Image Hashtag API

FastAPI-based image tagging service that generates hashtags, captions, style, and color predictions for images using local vision AI models.

## Features

- **CLIP Classification**: Predict image style, color, object, mood, and gender
- **Hashtag Generation**: Auto-generate relevant hashtags from CLIP predictions
- **Batch Processing**: Process multiple images from URLs with concurrent threads
- **Web Interface**: Built-in UI for testing and uploads

## Requirements

- Python 3.10+
- 8GB+ RAM recommended
- GPU recommended for faster processing (CUDA) - currently runs on CPU

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` to customize settings:

```yaml
app:
  host: "0.0.0.0"
  port: 8000
  reload: true

processing:
  max_length: 32
  num_beams: 4
  default_num_tags: 10
  max_num_tags: 50
```

## Running the API (local)

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API runs at `http://localhost:8000`

- Web UI: `http://localhost:8000/`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Running with Docker

### CPU image (recommended, runs anywhere)

```bash
docker build -t image-hashtag-api:cpu .

docker run --rm \
  -p 6868:6868 \
  -e PORT=6868 \
  -v "$(pwd)/data:/data" \
  --name image-hashtag-api \
  image-hashtag-api:cpu
```

Then open:

- Web UI: `http://localhost:6868/`
- Health check: `http://localhost:6868/health`
- API docs: `http://localhost:6868/docs`

### GPU image (optional, if host has NVIDIA GPU)

```bash
docker build -t image-hashtag-api:latest .

docker run --rm \
  -p 6868:6868 \
  -e PORT=6868 \
  --gpus all \
  -v "$(pwd)/data:/data" \
  --name image-hashtag-api-gpu \
  image-hashtag-api:latest
```

Inside `clip.py`, the service will automatically pick:

- GPU when `torch.cuda.is_available() == True`
- CPU otherwise

## Running on port 6868 without Docker

### Option 1: via `config.yaml`

```yaml
app:
  host: "0.0.0.0"
  port: 6868
  reload: true
```

```bash
python main.py
```

### Option 2: via uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 6868
```

## API Endpoints

### POST /tag-image

Generate hashtags from an uploaded image.

| Parameter | Type | Description |
|-----------|------|-------------|
| file | File | Image file (required) |

**Example using curl:**

```bash
curl -X POST http://localhost:8000/tag-image \
  -F "file=@image.jpg"
```

**Response:**

```json
{
  "style": "Realism",
  "color": "Blue",
  "clip_hashtags": ["anime", "Happy", "Boy"]
}
```

### POST /tag-image/url

Generate hashtags from an image URL.

```bash
curl -X POST http://localhost:8000/tag-image/url \
  -F "url=https://example.com/image.jpg"
```

### POST /tag-image/urls-batch

Batch process multiple image URLs (max 50).

```bash
curl -X POST http://localhost:8000/tag-image/urls-batch \
  -F "urls=https://example.com/1.jpg" \
  -F "urls=https://example.com/2.jpg" \
  -F "threads=4"
```

### POST /tag-image/load-model

Pre-load the CLIP model.

```bash
curl -X POST http://localhost:8000/tag-image/load-model
```

## Processing Flow

### CLIP Mode Flow

```
┌─────────────────┐
│  Upload Image  │
│ (file/URL/batch)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validate Image │
│  (content-type)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Load CLIP     │
│    Model       │──── First request only
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Preprocess     │
│   Image        │
│ (PIL, RGB)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Image   │
│  Features       │
│ (CLIP ViT-B/32) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Compute        │
│ Similarity     │
│ (Image vs Text)│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ Style │ │ Color │
│ Top 1 │ │ Top 1 │
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│  Predict       │
│ Object/Mood/   │
│   Gender       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Return        │
│  Hashtags     │
│ [obj,mood,gen] │
└─────────────────┘
```

### Detailed Processing Steps

1. **Image Input**: Accept image via file upload, URL, or batch URLs
2. **Validation**: Check content-type is image/*, verify non-empty
3. **Model Loading**: Load `openai/clip-vit-base-patch32` on first request (lazy loading)
4. **Preprocessing**: Convert image to PIL Image, ensure RGB mode
5. **Feature Extraction**: 
   - Extract image features using CLIP vision encoder
   - Extract text features from predefined prompts
6. **Similarity Calculation**: 
   - Compute cosine similarity between image and text embeddings
   - Apply softmax with temperature=0.01 (multiply by 100)
7. **Prediction**:
   - **Style**: 18 categories (2D, 3D, Animeart, Realism, etc.)
   - **Color**: 23 categories (Black, White, Blue, Green, etc.)
   - **Object**: ~400+ tags (sports, anime, nature, vehicles, etc.)
   - **Mood**: 6 categories (Happy, Sad, Lonely, Chill, Funny, None)
   - **Gender**: 6 categories (Boy, Girl, Man, Woman, Couple, None)
8. **Response**: Return style, color, and hashtags (object, mood, gender)

### Supported Categories

#### Styles (18)

2D, 3D, Cute, Animeart, Realism, Aesthetic, Cool, Fantasy, Comic, Horror, Cyberpunk, Lofi, Minimalism, Digitalart, Cinematic, Pixelart, Scifi, Vangoghart

#### Colors (23)

Black, White, Blackandwhite, Red, Yellow, Blue, Green, Pink, Orange, Pastel, Hologram, Vintage, Colorful, Neutral, Light, Dark, Warm, Cold, Neon, Gradient, Purple, Brown, Grey

#### Object Tags (400+)

Categories include: Sports, Animals, Universe, Games, Films, Cartoons, Anime, Humans, Nature, Vehicles, Abstract, Love, Food, Religion, Holiday, Quotes, Scenery, Seasons, Memes, and more.

#### Mood (6)

Happy, Sad, Lonely, Chill, Funny, None

#### Gender (6)

Boy, Girl, Man, Woman, Couple, None

## Architecture

```
main.py
├── FastAPI app
├── CORS middleware
└── Static files mount
    │
    ├── src/api/routes/
    │   ├── image.py      # Main image processing endpoints
    │   └── health.py     # Health check
    │
    ├── src/services/
    │   └── clip.py       # CLIP model service
    │
    ├── src/core/
    │   └── config.py     # Configuration loader
    │
    └── src/schemas/
        └── response.py   # Pydantic response models
```

## Development

```bash
# Run tests
pytest

# Run linting
flake8 .

# Format code
black .
isort .
```

## License

MIT
