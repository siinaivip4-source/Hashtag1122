from fastapi import APIRouter

from src.core.config import config
from src.schemas.response import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    return {
        "status": "ok",
        "model_backend": "local_hf_image_caption",
        "vision_model_name": config.vision_model_name,
    }
