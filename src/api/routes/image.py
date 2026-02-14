from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Annotated, List, Optional, Any
import httpx
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from src.services.vision import vision_service
from src.services.clip import clip_service
from src.services.hashtag import caption_to_hashtags
from src.core.config import config
from src.schemas.response import TagResponse

router = APIRouter(prefix="/tag-image", tags=["image"])


def parse_num_tags(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


@router.post("", response_model=TagResponse)
async def tag_image(
    file: Annotated[UploadFile, File(description="Image to analyze")],
    num_tags: Any = Form(None),
    language: str = Form("vi"),
    model: str = Form(None),
    custom_vocabulary: str = Form(None, description="Comma-separated list of custom categories"),
    mode: str = Form("both", description="Mode: clip, vision, or both"),
):

    num_tags = parse_num_tags(num_tags, config.default_num_tags)
    custom_keywords = [k.strip() for k in custom_vocabulary.split(",")] if custom_vocabulary else None

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File is not an image")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty or unreadable image")

    caption = ""
    tags = []
    style = ""
    color = ""
    clip_hashtags = []

    loop = asyncio.get_event_loop()

    if mode in ("vision", "both"):
        caption = await loop.run_in_executor(
            None,
            partial(vision_service.generate_caption, image_bytes, model_key=model)
        )
        tags = caption_to_hashtags(caption, num_tags=num_tags, language=language, custom_keywords=custom_keywords)

    if mode in ("clip", "both"):
        style, color, clip_hashtags = await loop.run_in_executor(
            None,
            partial(clip_service.predict, image_bytes, num_tags=num_tags)
        )

    return TagResponse(tags=tags, caption=caption, style=style, color=color, clip_hashtags=clip_hashtags)


@router.post("/url", response_model=TagResponse)
async def tag_image_from_url(
    url: Annotated[str, Form(description="Image URL to analyze")],
    num_tags: Any = Form(None),
    language: str = Form("vi"),
    model: str = Form(None),
    custom_vocabulary: str = Form(None),
    mode: str = Form("both", description="Mode: clip, vision, or both"),
):

    num_tags = parse_num_tags(num_tags, config.default_num_tags)
    custom_keywords = [k.strip() for k in custom_vocabulary.split(",")] if custom_vocabulary else None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"URL does not point to an image (content-type: {content_type})")
            image_bytes = response.content
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {str(e)}")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty or unreadable image")

    caption = ""
    tags = []
    style = ""
    color = ""
    clip_hashtags = []

    loop = asyncio.get_event_loop()

    if mode in ("vision", "both"):
        caption = await loop.run_in_executor(
            None,
            partial(vision_service.generate_caption, image_bytes, model_key=model)
        )
        tags = caption_to_hashtags(caption, num_tags=num_tags, language=language, custom_keywords=custom_keywords)

    if mode in ("clip", "both"):
        style, color, clip_hashtags = await loop.run_in_executor(
            None,
            partial(clip_service.predict, image_bytes, num_tags=num_tags)
        )

    return TagResponse(tags=tags, caption=caption, style=style, color=color, clip_hashtags=clip_hashtags)


@router.post("/urls-batch")
async def tag_images_from_urls(
    urls: Annotated[List[str], Form(description="List of image URLs to analyze")],
    num_tags: Any = Form(None),
    language: str = Form("vi"),
    model: str = Form(None),
    threads: int = Form(4, ge=1, le=32, description="Number of concurrent threads"),
    custom_vocabulary: str = Form(None),
    mode: str = Form("both", description="Mode: clip, vision, or both"),
):

    num_tags = parse_num_tags(num_tags, config.default_num_tags)
    custom_keywords = [k.strip() for k in custom_vocabulary.split(",")] if custom_vocabulary else None

    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    if len(urls) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 URLs per batch")

    loop = asyncio.get_event_loop()

    async def process_url(url: str, executor: ThreadPoolExecutor):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("image/"):
                    return {"url": url, "status": "error", "error": f"URL does not point to an image (content-type: {content_type})"}
                image_bytes = response.content

            if not image_bytes:
                return {"url": url, "status": "error", "error": "Empty or unreadable image"}

            caption = ""
            tags = []
            style = ""
            color = ""
            clip_hashtags = []

            if mode in ("vision", "both"):
                caption = await loop.run_in_executor(
                    executor,
                    partial(vision_service.generate_caption, image_bytes, model_key=model)
                )
                tags = caption_to_hashtags(caption, num_tags=num_tags, language=language, custom_keywords=custom_keywords)

            if mode in ("clip", "both"):
                style, color, clip_hashtags = await loop.run_in_executor(
                    executor,
                    partial(clip_service.predict, image_bytes, num_tags=num_tags)
                )

            return {"url": url, "status": "success", "tags": tags, "caption": caption, "style": style, "color": color, "clip_hashtags": clip_hashtags}
        except httpx.HTTPStatusError as e:
            return {"url": url, "status": "error", "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"url": url, "status": "error", "error": str(e)}
        except Exception as e:
            return {"url": url, "status": "error", "error": f"Processing error: {str(e)}"}

    with ThreadPoolExecutor(max_workers=threads) as executor:
        tasks = [process_url(url, executor) for url in urls]
        results = await asyncio.gather(*tasks)

    return {"results": results}
