from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.models import MediaType, MovieShow, Review
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.review import ReviewCreateRequest, ReviewResponse

router = APIRouter(tags=["Reviews"])
settings = get_settings()


@router.post("/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.default_rate_limit)
async def create_review(
    request: Request,
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
) -> ReviewResponse:
    query = select(MovieShow).where(MovieShow.tmdb_id == payload.tmdb_id)
    if payload.type is not None:
        query = query.where(MovieShow.media_type == payload.type)

    item = db.execute(query).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Library item not found")

    review = Review(item_id=item.id, rating=payload.rating, comment=payload.comment.strip())
    db.add(review)
    db.commit()
    db.refresh(review)

    return ReviewResponse.model_validate(review)


@router.get("/reviews/{movie_id}", response_model=PaginatedResponse[ReviewResponse])
@limiter.limit(settings.default_rate_limit)
async def get_reviews(
    request: Request,
    response: Response,
    movie_id: int,
    type: MediaType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ReviewResponse]:
    query = select(MovieShow).where(MovieShow.tmdb_id == movie_id)
    if type is not None:
        query = query.where(MovieShow.media_type == type)

    item = db.execute(query).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Library item not found")

    total = db.scalar(select(func.count()).select_from(Review).where(Review.item_id == item.id)) or 0

    reviews = db.execute(
        select(Review)
        .where(Review.item_id == item.id)
        .order_by(Review.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    response.headers["X-Total-Count"] = str(total)

    return PaginatedResponse[ReviewResponse](
        data=[ReviewResponse.model_validate(review) for review in reviews],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )