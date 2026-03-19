from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.models import MovieShow, Review
from app.schemas.recommended import RecommendationResponse
from app.services.gemini_service import recommend_movies_from_library

router = APIRouter(tags=["Recommendations"])
settings = get_settings()


@router.get("/recommended", response_model=RecommendationResponse)
@limiter.limit(settings.default_rate_limit)
async def get_recommendations(
    request: Request,
    max_recommendations: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    avg_rating_subquery = (
        select(Review.item_id, func.avg(Review.rating).label("avg_rating"))
        .group_by(Review.item_id)
        .subquery()
    )

    rows = db.execute(
        select(MovieShow, avg_rating_subquery.c.avg_rating)
        .outerjoin(avg_rating_subquery, avg_rating_subquery.c.item_id == MovieShow.id)
    ).all()

    library_payload = [
        {
            "tmdb_id": item.tmdb_id,
            "title": item.title,
            "media_type": item.media_type.value,
            "genre": item.genre,
            "platform": item.platform,
            "rating": float(avg_rating) if avg_rating is not None else None,
        }
        for item, avg_rating in rows
    ]

    recommendations = recommend_movies_from_library(
        library_items=library_payload,
        max_recommendations=max_recommendations,
    )

    return RecommendationResponse(recommendations=recommendations)