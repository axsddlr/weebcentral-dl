"""Configuration routes"""
import os
from fastapi import APIRouter, Request

from src.api.models import ConfigUpdateRequest
from src.config import DownloaderConfig, save_config

router = APIRouter(tags=["config"])


def config_to_response(config: DownloaderConfig) -> dict:
    return {
        "outputDir": config.output_dir,
        "latest": config.latest,
        "sequence": config.sequence,
        "zip": config.zip,
        "verbose": config.verbose,
        "useEnglishTitle": config.use_english_title,
        "comicinfo": config.comicinfo,
        "rlc": config.rlc,
        "maxSleep": config.max_sleep,
        "maxRetries": config.max_retries,
        "parallelWorkers": config.parallel_workers,
        "libraryPaths": config.library_paths,
        "checkInterval": config.check_interval,
    }


@router.get("/config")
async def get_config(request: Request):
    """Get current configuration."""
    config = request.app.state.config
    return config_to_response(config)


@router.put("/config")
async def update_config(request: Request, body: ConfigUpdateRequest):
    """Update configuration, save, and propagate to running components."""
    config = request.app.state.config
    downloader = request.app.state.downloader

    if body.outputDir is not None:
        config.output_dir = body.outputDir
        downloader.output_dir = os.path.abspath(body.outputDir)
    if body.latest is not None:
        config.latest = body.latest
    if body.sequence is not None:
        config.sequence = body.sequence
        downloader.image_downloader.sequence = body.sequence
    if body.zip is not None:
        config.zip = body.zip
        downloader.archiver.use_zip = body.zip
    if body.verbose is not None:
        config.verbose = body.verbose
    if body.useEnglishTitle is not None:
        config.use_english_title = body.useEnglishTitle
        downloader.use_english_title = body.useEnglishTitle
    if body.comicinfo is not None:
        config.comicinfo = body.comicinfo
    if body.rlc is not None:
        config.rlc = body.rlc
    if body.maxSleep is not None:
        config.max_sleep = body.maxSleep
        downloader.image_downloader.max_sleep = body.maxSleep
    if body.maxRetries is not None:
        config.max_retries = body.maxRetries
        downloader.image_downloader.max_retries = body.maxRetries
    if body.parallelWorkers is not None:
        config.parallel_workers = body.parallelWorkers
        downloader.image_downloader.parallel_workers = body.parallelWorkers
    if body.libraryPaths is not None:
        config.library_paths = body.libraryPaths
    if body.checkInterval is not None:
        config.check_interval = body.checkInterval
    save_config(config, request.app.state.config_path)
    return config_to_response(config)


@router.post("/config/reset")
async def reset_config(request: Request):
    """Reset configuration to defaults and save."""
    default = DownloaderConfig()
    request.app.state.config = default
    request.app.state.downloader.config = default
    request.app.state.queue_manager.config = default
    request.app.state.downloader.image_downloader.max_retries = default.max_retries
    request.app.state.downloader.image_downloader.max_sleep = default.max_sleep
    request.app.state.downloader.image_downloader.parallel_workers = default.parallel_workers
    request.app.state.downloader.image_downloader.sequence = default.sequence
    request.app.state.downloader.archiver.use_zip = default.zip
    request.app.state.downloader.cover_manager.output_dir = os.path.abspath(default.output_dir)
    request.app.state.downloader.archiver.output_dir = os.path.abspath(default.output_dir)
    save_config(default, request.app.state.config_path)
    return config_to_response(default)
