from datetime import datetime

from pydantic import BaseModel, Field

from app.models.models import MediaType, WatchStatus


class LibraryAddRequest(BaseModel):
    tmdb_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    type: MediaType
    genre: str = Field(min_length=1, max_length=120)
    platform: str = Field(min_length=1, max_length=120)


class LibraryItemResponse(BaseModel):
    id: int
    tmdb_id: int
    title: str
    media_type: MediaType
    genre: str
    platform: str
    date_added: datetime
    status: WatchStatus | None = None
    average_rating: float | None = None

    model_config = {"from_attributes": True}