from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.models import MovieShow, Progress, Review, WatchStatus
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.library import LibraryAddRequest, LibraryItemResponse

router = APIRouter(prefix="/library", tags=["Library"])
settings = get_settings()


@router.post("/add", response_model=LibraryItemResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.default_rate_limit)
async def add_to_library(
    request: Request,
    payload: LibraryAddRequest,
    db: Session = Depends(get_db),
) -> LibraryItemResponse:
    existing = db.execute(
        select(MovieShow).where(
            MovieShow.tmdb_id == payload.tmdb_id,
            MovieShow.media_type == payload.type,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item already in library")

    item = MovieShow(
        tmdb_id=payload.tmdb_id,
        title=payload.title.strip(),
        media_type=payload.type,
        genre=payload.genre.strip(),
        platform=payload.platform.strip(),
    )

    db.add(item)
    db.flush()

    progress = Progress(item_id=item.id, status=WatchStatus.NOT_STARTED)
    db.add(progress)
    db.commit()
    db.refresh(item)

    return LibraryItemResponse(
        id=item.id,
        tmdb_id=item.tmdb_id,
        title=item.title,
        media_type=item.media_type,
        genre=item.genre,
        platform=item.platform,
        date_added=item.date_added,
        status=WatchStatus.NOT_STARTED,
        average_rating=None,
    )


@router.get("", response_model=PaginatedResponse[LibraryItemResponse])
@limiter.limit(settings.default_rate_limit)
async def list_library(
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db),
) -> PaginatedResponse[LibraryItemResponse]:
    avg_rating_subquery = (
        select(Review.item_id, func.avg(Review.rating).label("avg_rating"))
        .group_by(Review.item_id)
        .subquery()
    )

    base_query = (
        select(MovieShow, Progress.status, avg_rating_subquery.c.avg_rating)
        .outerjoin(Progress, Progress.item_id == MovieShow.id)
        .outerjoin(avg_rating_subquery, avg_rating_subquery.c.item_id == MovieShow.id)
    )

    total = db.scalar(select(func.count()).select_from(MovieShow)) or 0

    rows = db.execute(
        base_query
        .order_by(desc(MovieShow.date_added))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    data = [
        LibraryItemResponse(
            id=item.id,
            tmdb_id=item.tmdb_id,
            title=item.title,
            media_type=item.media_type,
            genre=item.genre,
            platform=item.platform,
            date_added=item.date_added,
            status=status_value,
            average_rating=float(avg_rating) if avg_rating is not None else None,
        )
        for item, status_value, avg_rating in rows
    ]

    response.headers["X-Total-Count"] = str(total)

    return PaginatedResponse[LibraryItemResponse](
        data=data,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/filter", response_model=PaginatedResponse[LibraryItemResponse])
@limiter.limit(settings.default_rate_limit)
async def filter_library(
    request: Request,
    response: Response,
    genre: str | None = Query(default=None, min_length=1, max_length=120),
    platform: str | None = Query(default=None, min_length=1, max_length=120),
    status_filter: WatchStatus | None = Query(default=None, alias="status"),
    sort_by: str = Query(default="date_added", pattern="^(rating|title|date_added)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db),
) -> PaginatedResponse[LibraryItemResponse]:
    avg_rating_subquery = (
        select(Review.item_id, func.avg(Review.rating).label("avg_rating"))
        .group_by(Review.item_id)
        .subquery()
    )

    query = (
        select(MovieShow, Progress.status, avg_rating_subquery.c.avg_rating)
        .outerjoin(Progress, Progress.item_id == MovieShow.id)
        .outerjoin(avg_rating_subquery, avg_rating_subquery.c.item_id == MovieShow.id)
    )

    count_query = select(func.count(MovieShow.id)).outerjoin(Progress, Progress.item_id == MovieShow.id)

    if genre:
        query = query.where(MovieShow.genre.ilike(f"%{genre}%"))
        count_query = count_query.where(MovieShow.genre.ilike(f"%{genre}%"))

    if platform:
        query = query.where(MovieShow.platform.ilike(f"%{platform}%"))
        count_query = count_query.where(MovieShow.platform.ilike(f"%{platform}%"))

    if status_filter:
        query = query.where(Progress.status == status_filter)
        count_query = count_query.where(Progress.status == status_filter)

    direction = asc if sort_order == "asc" else desc
    if sort_by == "rating":
        if sort_order == "asc":
            order_by_clause = (avg_rating_subquery.c.avg_rating.is_(None), asc(avg_rating_subquery.c.avg_rating))
        else:
            order_by_clause = (avg_rating_subquery.c.avg_rating.is_(None), desc(avg_rating_subquery.c.avg_rating))
    elif sort_by == "title":
        order_by_clause = direction(MovieShow.title)
    else:
        order_by_clause = direction(MovieShow.date_added)

    total = db.scalar(count_query) or 0

    if isinstance(order_by_clause, tuple):
        ordered_query = query.order_by(*order_by_clause)
    else:
        ordered_query = query.order_by(order_by_clause)

    rows = db.execute(ordered_query.offset((page - 1) * page_size).limit(page_size)).all()

    data = [
        LibraryItemResponse(
            id=item.id,
            tmdb_id=item.tmdb_id,
            title=item.title,
            media_type=item.media_type,
            genre=item.genre,
            platform=item.platform,
            date_added=item.date_added,
            status=status_value,
            average_rating=float(avg_rating) if avg_rating is not None else None,
        )
        for item, status_value, avg_rating in rows
    ]

    response.headers["X-Total-Count"] = str(total)

    return PaginatedResponse[LibraryItemResponse](
        data=data,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )