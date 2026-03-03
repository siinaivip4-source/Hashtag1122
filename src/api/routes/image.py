from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Annotated, List, Optional, Any
import httpx
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from src.services.clip import clip_service
from src.core.config import config
from src.schemas.response import TagResponse

router = APIRouter(prefix="/tag-image", tags=["image"])

# Global executor for AI tasks to control thread count
# We use a bit more threads to handle I/O (file reading) + Lock queueing
inference_executor = ThreadPoolExecutor(max_workers=20)


def _process_image_bytes(image_bytes: bytes, model_key: str = "clip-openai") -> dict:
    start_time = time.time()
    
    # Chỉ dùng CLIP cho việc phân loại style, color, object, mood, gender
    style, color, clip_hashtags = clip_service.predict(image_bytes, model_key=model_key)

    duration = time.time() - start_time
    print(f"Image processed in {duration:.3f}s [model={model_key}]")

    return {
        "style": style,
        "color": color,
        "clip_hashtags": clip_hashtags
    }




@router.post("/load-model")
async def load_model(
    model: Annotated[Optional[str], Form(description="Model key to load")] = "clip-openai",
) -> dict:
    req_start = time.time()

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(inference_executor, partial(clip_service.load, model_key=model))
    except Exception as e:
        duration = time.time() - req_start
        print(f"-> [Endpoint /tag-image/load-model] Failed after {duration:.3f}s: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    duration = time.time() - req_start
    print(f"-> [Endpoint /tag-image/load-model] Model ready in {duration:.3f}s")

    return {
        "status": "ok",
        "model": model,
        "duration": duration,
    }


@router.post("", response_model=TagResponse)
async def tag_image(
    file: Annotated[UploadFile, File(description="Image to analyze")],
    model: Annotated[Optional[str], Form(description="Model key to use")] = "clip-openai",
):
    req_start = time.time()
    print(f"-> [Endpoint /tag-image] Incoming request. Filename: {file.filename}, Type: {file.content_type}", flush=True)

    if not file.content_type.startswith("image/"):
        print(f"!! [Endpoint /tag-image] Invalid type: {file.content_type}", flush=True)
        raise HTTPException(status_code=400, detail="File is not an image")

    try:
        print(f"-> [Endpoint /tag-image] Reading bytes for {file.filename}...", flush=True)
        image_bytes = await file.read()
        print(f"-> [Endpoint /tag-image] Bytes read: {len(image_bytes)} bytes", flush=True)
        
        if not image_bytes:
            print("!! [Endpoint /tag-image] Buffer empty", flush=True)
            raise HTTPException(status_code=400, detail="Empty or unreadable image")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            inference_executor,
            partial(_process_image_bytes, image_bytes, model_key=model)
        )
    except Exception as e:
        print(f"!! [Endpoint /tag-image] Error in processing: {str(e)}", flush=True)
        raise e
    finally:
        await file.close()

    duration = time.time() - req_start
    print(f"-> [Endpoint /tag-image] Request completed in {duration:.3f}s for {file.filename}", flush=True)

    return TagResponse(
        style=result["style"],
        color=result["color"],
        clip_hashtags=result["clip_hashtags"]
    )


@router.post("/url", response_model=TagResponse)
async def tag_image_from_url(
    url: Annotated[str, Form(description="Image URL to analyze")],
    model: Annotated[Optional[str], Form(description="Model key to use")] = "clip-openai",
):
    req_start = time.time()

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            # check the response
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

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        inference_executor,
        partial(_process_image_bytes, image_bytes, model_key=model)
    )

    duration = time.time() - req_start
    print(f"-> [Endpoint /tag-image/url] Total request time: {duration:.3f}s")

    return TagResponse(
        style=result["style"],
        color=result["color"],
        clip_hashtags=result["clip_hashtags"]
    )


@router.post("/urls-batch")
async def tag_images_from_urls(
    urls: Annotated[List[str], Form(description="List of image URLs to analyze")],
    model: Annotated[Optional[str], Form(description="Model key to use")] = "clip-openai",
    threads: int = Form(4, ge=1, le=32, description="Number of concurrent threads"),
):
    req_start = time.time()

    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    if len(urls) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 URLs per batch")

    loop = asyncio.get_event_loop()

    async def process_url(url: str):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            # Use a shorter timeout for batch items to prevent one hang from blocking the whole request
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("image/"):
                    return {"url": url, "status": "error", "error": f"URL does not point to an image (content-type: {content_type})"}
                image_bytes = response.content

            if not image_bytes:
                return {"url": url, "status": "error", "error": "Empty or unreadable image"}

            result = await loop.run_in_executor(
                inference_executor,
                partial(_process_image_bytes, image_bytes, model_key=model)
            )

            return {
                "url": url,
                "status": "success",
                "style": result["style"],
                "color": result["color"],
                "clip_hashtags": result["clip_hashtags"]
            }
        except httpx.HTTPStatusError as e:
            return {"url": url, "status": "error", "error": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"url": url, "status": "error", "error": str(e)}
        except Exception as e:
            return {"url": url, "status": "error", "error": f"Processing error: {str(e)}"}

    tasks = [process_url(url) for url in urls]
    results = await asyncio.gather(*tasks)

    duration = time.time() - req_start
    print(f"-> [Endpoint /tag-image/urls-batch] Total request time for {len(urls)} items: {duration:.3f}s")
    
    return {"results": results}
