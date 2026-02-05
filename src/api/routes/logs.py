"""Log routes"""
from fastapi import APIRouter, Request

router = APIRouter(tags=["logs"])


@router.get("/logs")
async def get_logs(request: Request):
    """Get log entries."""
    log_collector = request.app.state.log_collector
    return {"logs": log_collector.get_logs()}


@router.delete("/logs")
async def clear_logs(request: Request):
    """Clear all logs."""
    log_collector = request.app.state.log_collector
    log_collector.clear()
    return {"cleared": True}
