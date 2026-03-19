from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.models import MediaType, MovieShow, Progress, WatchStatus
from app.schemas.progress import ProgressResponse, ProgressUpdateRequest

router = APIRouter(prefix="/progress", tags=["Progress"])
settings = get_settings()


@router.put("/{item_id}", response_model=ProgressResponse)
@limiter.limit(settings.default_rate_limit)
async def update_progress(
    request: Request,
    item_id: int,
    payload: ProgressUpdateRequest,
    db: Session = Depends(get_db),
) -> ProgressResponse:
    item = db.execute(select(MovieShow).where(MovieShow.id == item_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Library item not found")

    progress = db.execute(select(Progress).where(Progress.item_id == item_id)).scalar_one_or_none()
    if not progress:
        progress = Progress(item_id=item_id, status=WatchStatus.NOT_STARTED)
        db.add(progress)

    if item.media_type == MediaType.MOVIE:
        if payload.total_episodes not in (None, 0) or payload.watched_episodes not in (None, 0):
            raise HTTPException(
                status_code=400,
                detail="Movies do not support episode-based progress",
            )
        progress.total_episodes = None
        progress.watched_episodes = None
    else:
        if payload.total_episodes is None or payload.watched_episodes is None:
            raise HTTPException(
                status_code=400,
                detail="TV shows require total_episodes and watched_episodes",
            )
        if payload.watched_episodes > payload.total_episodes:
            raise HTTPException(
                status_code=400,
                detail="watched_episodes cannot exceed total_episodes",
            )
        progress.total_episodes = payload.total_episodes
        progress.watched_episodes = payload.watched_episodes

    progress.status = payload.status

    db.commit()
    db.refresh(progress)

    return ProgressResponse.model_validate(progress)


@router.get("/{item_id}", response_model=ProgressResponse)
@limiter.limit(settings.default_rate_limit)
async def get_progress(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
) -> ProgressResponse:
    progress = db.execute(select(Progress).where(Progress.item_id == item_id)).scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return ProgressResponse.model_validate(progress)