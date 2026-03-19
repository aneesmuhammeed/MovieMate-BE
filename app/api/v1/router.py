from fastapi import APIRouter

from app.api.routers.external import router as external_router
from app.api.routers.library import router as library_router
from app.api.routers.progress import router as progress_router
from app.api.routers.recommended import router as recommended_router
from app.api.routers.review import router as review_router

v1_router = APIRouter()
v1_router.include_router(external_router)
v1_router.include_router(library_router)
v1_router.include_router(progress_router)
v1_router.include_router(review_router)
v1_router.include_router(recommended_router)