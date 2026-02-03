from typing import List

from pydantic import BaseModel


class TagRequest(BaseModel):
    tags: List[str]


class HealthResponse(BaseModel):
    status: str
    model_backend: str
    vision_model_name: str


class TagResponse(BaseModel):
    tags: List[str]
