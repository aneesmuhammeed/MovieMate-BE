from pydantic import BaseModel, Field

from app.models.models import MediaType


class RecommendedMovie(BaseModel):
    title: str
    media_type: MediaType | None = None
    reason: str


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendedMovie]