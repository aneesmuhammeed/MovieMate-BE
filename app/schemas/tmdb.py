from pydantic import BaseModel, Field

from app.models.models import MediaType


class TMDBSearchItem(BaseModel):
    id: int
    title: str = Field(alias="name")
    media_type: MediaType
    overview: str | None = None
    poster_path: str | None = None
    release_date: str | None = None


class TMDBDetailsResponse(BaseModel):
    id: int
    media_type: MediaType
    title: str
    overview: str | None = None
    genres: list[str] = []
    runtime: int | None = None
    number_of_seasons: int | None = None
    number_of_episodes: int | None = None
    release_date: str | None = None
    poster_path: str | None = None
    vote_average: float | None = None