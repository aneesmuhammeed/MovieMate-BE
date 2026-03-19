from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.models import MediaType

settings = get_settings()


class TMDBService:
    def __init__(self) -> None:
        self.base_url = str(settings.tmdb_base_url).rstrip("/")
        self.api_key = settings.tmdb_api_key

    async def _request(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TMDB API key is not configured",
            )

        query_params = params.copy() if params else {}
        query_params["api_key"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}{path}", params=query_params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            detail = "Failed to fetch data from TMDB"
            if exc.response.status_code == status.HTTP_404_NOT_FOUND:
                detail = "TMDB item not found"
            elif exc.response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="TMDB service error",
                ) from exc

            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach TMDB service",
            ) from exc

    async def search(self, query: str, page: int = 1) -> dict[str, Any]:
        return await self._request(
            "/search/multi",
            {
                "query": query,
                "page": page,
                "include_adult": False,
            },
        )

    async def details(
        self,
        tmdb_id: int,
        media_type: MediaType | None = None,
    ) -> tuple[dict[str, Any], MediaType]:
        if media_type is not None:
            payload = await self._request(f"/{media_type.value}/{tmdb_id}")
            return payload, media_type

        for candidate in (MediaType.MOVIE, MediaType.TV):
            try:
                payload = await self._request(f"/{candidate.value}/{tmdb_id}")
                return payload, candidate
            except HTTPException as exc:
                if exc.status_code != status.HTTP_404_NOT_FOUND:
                    raise

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TMDB item not found")