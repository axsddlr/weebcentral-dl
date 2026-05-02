"""Configuration routes"""
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
        "rlc": config.rlc,
        "maxSleep": config.max_sleep,
        "maxRetries": config.max_retries,
        "parallelWorkers": config.parallel_workers,
    }


@router.get("/config")
async def get_config(request: Request):
    """Get current configuration."""
    config = request.app.state.config
    return config_to_response(config)


@router.put("/config")
async def update_config(request: Request, body: ConfigUpdateRequest):
    """Update configuration and save to config file."""
    config = request.app.state.config

    if body.outputDir is not None:
        config.output_dir = body.outputDir
    if body.latest is not None:
        config.latest = body.latest
    if body.sequence is not None:
        config.sequence = body.sequence
    if body.zip is not None:
        config.zip = body.zip
    if body.verbose is not None:
        config.verbose = body.verbose
    if body.useEnglishTitle is not None:
        config.use_english_title = body.useEnglishTitle
    if body.rlc is not None:
        config.rlc = body.rlc
    if body.maxSleep is not None:
        config.max_sleep = body.maxSleep
    if body.maxRetries is not None:
        config.max_retries = body.maxRetries
    if body.parallelWorkers is not None:
        config.parallel_workers = body.parallelWorkers

    save_config(config, request.app.state.config_path)
    return config_to_response(config)


@router.post("/config/reset")
async def reset_config(request: Request):
    """Reset configuration to defaults and save."""
    default = DownloaderConfig()
    request.app.state.config = default
    request.app.state.downloader.config = default
    save_config(default, request.app.state.config_path)
    return config_to_response(default)
