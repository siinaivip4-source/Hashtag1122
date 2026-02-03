from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Annotated

from src.services.vision import vision_service
from src.services.hashtag import caption_to_hashtags
from src.core.config import config
from src.schemas.response import TagResponse

router = APIRouter(prefix="/tag-image", tags=["image"])


@router.post("", response_model=TagResponse)
async def tag_image(
    file: Annotated[UploadFile, File(description="Image to analyze")],
    num_tags: Annotated[int, Form()] = None,
    language: Annotated[str, Form()] = "vi",
    model: Annotated[str, Form()] = None,
):
    if num_tags is None:
        num_tags = config.default_num_tags

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File is not an image")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty or unreadable image")

    caption = vision_service.generate_caption(image_bytes, model_key=model)
    tags = caption_to_hashtags(caption, num_tags=num_tags, language=language)

    return TagResponse(tags=tags)
