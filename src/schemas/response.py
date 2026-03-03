from typing import List

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    model_backend: str
    device: str


class TagResponse(BaseModel):
    style: str = ""
    color: str = ""
    clip_hashtags: List[str] = []
