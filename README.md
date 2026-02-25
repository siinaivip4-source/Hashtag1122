# Image Hashtag API

FastAPI-based image tagging service that generates hashtags, captions, style, and color predictions for images using local vision AI models.

## Features

- **Image Captioning**: Generate captions using ViT-GPT2, BLIP, or GIT models
- **CLIP Classification**: Predict image style and dominant colors
- **Hashtag Generation**: Auto-generate relevant hashtags from captions or CLIP predictions
- **Batch Processing**: Process multiple images from URLs
- **Web Interface**: Built-in UI for testing and batch uploads

## Requirements

- Python 3.10+
- 8GB+ RAM recommended
- GPU recommended for faster processing (CUDA)

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

model:
  default: "vit-gpt2"
  available:
    vit-gpt2: "nlpconnect/vit-gpt2-image-captioning"
    blip-base: "Salesforce/blip-image-captioning-base"
    git-base: "microsoft/git-base"

processing:
  max_length: 32
  num_beams: 4
  default_num_tags: 10
  max_num_tags: 50
```

## Running the API

```bash
python main.py
```

API runs at `http://localhost:8000`

- Web UI: `http://localhost:8000/`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## API Endpoints

### POST /tag-image

Generate hashtags from an uploaded image.

| Parameter | Type | Description |
|-----------|------|-------------|
| file | File | Image file (required) |
| num_tags | int | Number of hashtags (default: 10) |
| model | string | Model: `vit-gpt2`, `blip-base`, `git-base` |
| custom_vocabulary | string | Comma-separated custom keywords |
| mode | string | `clip`, `vision`, or `both` (default: `both`) |

**Example using curl:**

```bash
curl -X POST http://localhost:8000/tag-image \
  -F "file=@image.jpg" \
  -F "num_tags=10" \
  -F "mode=both"
```

**Response:**

```json
{
  "tags": ["#photography", "#nature", "#travel"],
  "caption": "A beautiful landscape with mountains",
  "style": "Realism",
  "color": "Blue",
  "clip_hashtags": ["#photography", "#nature", "#landscape"]
}
```

### POST /tag-image/url

Generate hashtags from an image URL.

```bash
curl -X POST http://localhost:8000/tag-image/url \
  -F "url=https://example.com/image.jpg" \
  -F "num_tags=10"
```

### POST /tag-image/urls-batch

Batch process multiple image URLs (max 50).

```bash
curl -X POST http://localhost:8000/tag-image/urls-batch \
  -F "urls=https://example.com/1.jpg" \
  -F "urls=https://example.com/2.jpg" \
  -F "threads=4"
```

## Modes

- **vision**: Uses image captioning models to generate caption, then extracts hashtags from caption
- **clip**: Uses CLIP model to predict style, color, and generate hashtags
- **both**: Returns results from both modes

## Supported Styles (CLIP)

2D, 3D, Cute, Animeart, Realism, Aesthetic, Cool, Fantasy, Comic, Horror, Cyberpunk, Lofi, Minimalism, Digitalart, Cinematic, Pixelart, Scifi, Vangoghart

## Supported Colors

Black, White, Blackandwhite, Red, Yellow, Blue, Green, Pink, Orange, Pastel, Hologram, Vintage, Colorful, Neutral, Light, Dark, Warm, Cold, Neon, Gradient, Purple, Brown, Grey

## License

MIT
