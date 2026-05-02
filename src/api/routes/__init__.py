"""API route aggregation"""
import os
from fastapi import APIRouter, Request
from src.api.routes.search import router as search_router
from src.api.routes.download import router as download_router
from src.api.routes.library import router as library_router
from src.api.routes.reader import router as reader_router
from src.api.routes.config_routes import router as config_router
from src.api.routes.stats import router as stats_router
from src.api.routes.logs import router as logs_router
from src.api.routes.tracked import router as tracked_router


def get_output_dir(request: Request) -> str:
    """Normalize and return the configured output directory."""
    return os.path.abspath(request.app.state.config.output_dir)


api_router = APIRouter(prefix="/api")
api_router.include_router(search_router)
api_router.include_router(download_router)
api_router.include_router(library_router)
api_router.include_router(reader_router)
api_router.include_router(config_router)
api_router.include_router(stats_router)
api_router.include_router(logs_router)
api_router.include_router(tracked_router)
