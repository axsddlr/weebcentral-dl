"""FastAPI application setup"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import api_router
from src.api.ws import ws_router
from src.api.services.queue_manager import QueueManager
from src.api.services.log_collector import LogCollector
from src.config import DownloaderConfig, load_config
from src.downloader import WeebCentralDownloader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize shared resources."""
    config = load_config()
    downloader = WeebCentralDownloader(config)

    log_collector = LogCollector()
    log_collector.install()

    queue_manager = QueueManager(downloader, config, log_collector)

    app.state.downloader = downloader
    app.state.config = config
    app.state.queue_manager = queue_manager
    app.state.log_collector = log_collector

    await queue_manager.start()
    yield
    await queue_manager.stop()
    log_collector.uninstall()


def create_app() -> FastAPI:
    app = FastAPI(
        title="WeebCentral Downloader",
        description="Web UI for WeebCentral Manga Downloader",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS for dev mode (vite dev server on different port)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router)
    app.include_router(ws_router)

    # Serve static SPA files
    web_dir = Path(__file__).parent.parent / "web"
    if web_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(web_dir / "assets")), name="static")

        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str):
            """SPA fallback: serve index.html for all non-API routes."""
            # Try to serve the exact file first
            file_path = web_dir / full_path
            if full_path and file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            # Fallback to index.html for client-side routing
            index_path = web_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return HTMLResponse("<h1>UI not built. Run frontend build first.</h1>", status_code=404)

    return app
