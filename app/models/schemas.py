from typing import Any, Optional
from pydantic import BaseModel, Field


class NCERTMetadata(BaseModel):
    chapter_name: str = Field(description="The main chapter name")
    topic: str = Field(description="The primary topic being discussed")
    subtopic: str = Field(description="The specific subtopic or concept")
    image_referenced: bool = Field(default=False, description="Whether an image is referenced")
    image_url: Optional[str] = Field(default=None, description="Direct URL path to the image")
    image_caption: Optional[str] = Field(default=None, description="Caption or description of the image")


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Question asked by the user")
    top_k: Optional[int] = Field(default=None, ge=1, le=10, description="Number of source chunks to retrieve")


class SourceItem(BaseModel):
    text: str
    metadata: dict[str, Any]
    score: Optional[float] = None
    image_url: Optional[str] = None
    image_caption: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem]
    images: list[str] = []


class HealthResponse(BaseModel):
    status: str
    app_name: str
    database_connected: bool
    model_name: str
    environment: str

