from pydantic import BaseModel, Field, model_validator

from app.models.models import WatchStatus


class ProgressUpdateRequest(BaseModel):
    total_episodes: int | None = Field(default=None, ge=0)
    watched_episodes: int | None = Field(default=None, ge=0)
    status: WatchStatus

    @model_validator(mode="after")
    def validate_episode_counts(self) -> "ProgressUpdateRequest":
        if self.total_episodes is not None and self.watched_episodes is not None:
            if self.watched_episodes > self.total_episodes:
                raise ValueError("watched_episodes cannot be greater than total_episodes")
        return self


class ProgressResponse(BaseModel):
    id: int
    item_id: int
    total_episodes: int | None
    watched_episodes: int | None
    status: WatchStatus

    model_config = {"from_attributes": True}