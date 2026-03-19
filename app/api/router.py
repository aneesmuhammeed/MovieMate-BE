from fastapi import APIRouter

from app.core.config import get_settings
from app.api.v1.router import v1_router

api_router = APIRouter()
settings = get_settings()


@api_router.get("", tags=["API"])
async def api_versions() -> dict[str, list[str]]:
	return {"versions": [settings.api_version]}


api_router.include_router(v1_router, prefix=f"/{settings.api_version}")