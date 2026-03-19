from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.models import MediaType
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.services.tmdb_service import TMDBService

router = APIRouter(tags=["TMDB"])
settings = get_settings()


def _normalize_media_type(raw_type: str | None) -> MediaType | None:
    if raw_type == MediaType.MOVIE.value:
        return MediaType.MOVIE
    if raw_type == MediaType.TV.value:
        return MediaType.TV
    return None


@router.get("/search", response_model=PaginatedResponse[dict])
@limiter.limit(settings.search_rate_limit)
async def search_titles(
    request: Request,
    response: Response,
    query: str = Query(min_length=1, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    tmdb_service: TMDBService = Depends(TMDBService),
) -> PaginatedResponse[dict]:
    payload = await tmdb_service.search(query=query, page=page)

    normalized_results: list[dict] = []
    for item in payload.get("results", []):
        media_type = _normalize_media_type(item.get("media_type"))
        if media_type is None:
            continue
        normalized_results.append(
            {
                "id": item.get("id"),
                "title": item.get("title") or item.get("name"),
                "media_type": media_type,
                "overview": item.get("overview"),
                "poster_path": item.get("poster_path"),
                "release_date": item.get("release_date") or item.get("first_air_date"),
            }
        )

    data = normalized_results[:page_size]
    total = payload.get("total_results", len(normalized_results))
    response.headers["X-Total-Count"] = str(total)  

    return PaginatedResponse[dict](
        data=data,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/details/{tmdb_id}", response_model=dict)
@limiter.limit(settings.detail_rate_limit)
async def get_details(
    request: Request,
    tmdb_id: int,
    media_type: MediaType | None = Query(default=None, description="movie or tv. Optional; auto-detected when omitted."),
    tmdb_service: TMDBService = Depends(TMDBService),
) -> dict:
    payload, resolved_media_type = await tmdb_service.details(tmdb_id=tmdb_id, media_type=media_type)


    return {
        "id": payload.get("id"),
        "media_type": resolved_media_type,
        "title": payload.get("title") or payload.get("name"),
        "overview": payload.get("overview"),
        "genres": [genre.get("name") for genre in payload.get("genres", []) if genre.get("name")],
        "runtime": payload.get("runtime"),
        "number_of_seasons": payload.get("number_of_seasons"),
        "number_of_episodes": payload.get("number_of_episodes"),
        "release_date": payload.get("release_date") or payload.get("first_air_date"),
        "poster_path": payload.get("poster_path"),
        "vote_average": payload.get("vote_average"),
    }