from fastapi import APIRouter

from src.core.config import config
from src.schemas.response import HealthResponse

from src.services.clip import clip_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    return {
        "status": "ok",
        "model_backend": "local_hf_clip",
        "device": clip_service.device
    }
