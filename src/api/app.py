"""FastAPI application setup"""
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import api_router
from src.api.ws import ws_router, ConnectionManagers
from src.api.services.queue_manager import QueueManager
from src.api.services.library_cache import LibraryCache
from src.api.services.log_collector import LogCollector
from src.config import DownloaderConfig, load_config
from src.downloader import WeebCentralDownloader
from src.utils import resolve_safe_path


async def verify_api_token(request: Request):
    """Simple middleware to check for API token in headers or query."""
    token = os.getenv("API_TOKEN")
    if not token:
        return

    # Skip auth for read-only routes if we want, but task says protect state-changing routes
    # For now, let's keep it simple: if API_TOKEN is set, all non-GET API routes need it.
    if request.method != "GET" and request.url.path.startswith("/api/"):
        header_token = request.headers.get("X-API-Token")
        query_token = request.query_params.get("token")
        
        if header_token != token and query_token != token:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Unauthorized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize shared resources."""
    config_path = os.getenv("CONFIG_FILE", "config.toml")
    config = load_config(config_path)
    downloader = WeebCentralDownloader(config)

    ws_managers = ConnectionManagers()

    log_collector = LogCollector(ws_managers=ws_managers)
    log_collector.install()

    library_cache = LibraryCache(config.output_dir)
    queue_manager = QueueManager(downloader, config, log_collector, library_cache, ws_managers)

    app.state.config = config
    app.state.config_path = config_path
    app.state.downloader = downloader
    app.state.library_cache = library_cache
    app.state.queue_manager = queue_manager
    app.state.log_collector = log_collector
    app.state.ws = ws_managers

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

    # CORS: Allow localhost (dev) and server's own address
    # For production, we should ideally know the specific domain
    allowed_origins = [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:8000",  # Production server (self)
        "http://127.0.0.1:8000",
    ]

    # Add optional HOST env for remote access
    host_env = os.getenv("HOST")
    if host_env and host_env not in ["0.0.0.0", "127.0.0.1", "localhost"]:
        allowed_origins.append(f"http://{host_env}:8000")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Content-Type", "X-API-Token"],
    )

    # Security headers for production SPA
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' ws: wss:; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        return response

    # Rate limiting middleware (sliding window, in-memory)
    _rate_buckets: dict[str, list[float]] = defaultdict(list)
    _rate_limit = 60    # max requests per window
    _rate_window = 60.0  # window in seconds

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            client = request.client.host if request.client else "unknown"
            now = time.time()
            bucket = _rate_buckets[client]
            # Purge expired entries
            cutoff = now - _rate_window
            while bucket and bucket[0] < cutoff:
                bucket.pop(0)
            if len(bucket) >= _rate_limit:
                raise HTTPException(status_code=429, detail="Too many requests")
            bucket.append(now)
        return await call_next(request)

    # Simple auth middleware for state-changing API routes
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        await verify_api_token(request)
        return await call_next(request)

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
            try:
                # full_path might be empty for root
                if full_path:
                    file_path = Path(resolve_safe_path(str(web_dir), full_path))
                    if file_path.exists() and file_path.is_file():
                        return FileResponse(str(file_path))
            except ValueError:
                # Path traversal attempt or invalid path
                pass

            # Fallback to index.html for client-side routing
            index_path = web_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return HTMLResponse("<h1>UI not built. Run frontend build first.</h1>", status_code=404)

    return app
