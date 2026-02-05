"""Library routes: list and manage downloaded manga."""
import os
import shutil

from fastapi import APIRouter, Request, HTTPException

from src.api.services.library_scanner import scan_library, scan_chapters

router = APIRouter(tags=["library"])


@router.get("/library")
async def list_library(request: Request):
    """List all downloaded manga series."""
    output_dir = request.app.state.config.output_dir
    output_dir = os.path.abspath(output_dir)
    return {"series": scan_library(output_dir)}


@router.get("/library/{series_dir}/chapters")
async def list_chapters(request: Request, series_dir: str):
    """List chapters in a series."""
    output_dir = os.path.abspath(request.app.state.config.output_dir)
    chapters = scan_chapters(output_dir, series_dir)
    if not chapters and not os.path.exists(os.path.join(output_dir, series_dir)):
        raise HTTPException(status_code=404, detail="Series not found")
    return {"chapters": chapters}


@router.delete("/library/{series_dir}")
async def delete_series(request: Request, series_dir: str):
    """Delete an entire series directory."""
    output_dir = os.path.abspath(request.app.state.config.output_dir)
    series_path = os.path.join(output_dir, series_dir)

    if not os.path.exists(series_path):
        raise HTTPException(status_code=404, detail="Series not found")

    # Safety check: ensure it's inside the output directory
    if not os.path.abspath(series_path).startswith(output_dir):
        raise HTTPException(status_code=403, detail="Invalid path")

    shutil.rmtree(series_path)
    return {"deleted": True}
