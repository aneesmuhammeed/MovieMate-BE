from datetime import datetime

from pydantic import BaseModel, Field

from app.models.models import MediaType


class ReviewCreateRequest(BaseModel):
    tmdb_id: int = Field(gt=0, description="TMDB id from the library item")
    type: MediaType | None = Field(default=None, description="Optional media type to disambiguate ids")
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=2000)


class ReviewResponse(BaseModel):
    id: int
    item_id: int
    rating: int
    comment: str
    created_at: datetime

    model_config = {"from_attributes": True}