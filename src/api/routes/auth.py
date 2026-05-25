"""Authentication routes: httpOnly cookie login/logout"""
import os
import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(tags=["auth"])
_log = logging.getLogger("auth")


def _get_expected_token() -> str | None:
    token = os.getenv("API_TOKEN")
    if token:
        token = token.strip().strip("'\"")
    return token if token else None


@router.post("/auth/login")
async def login(request: Request):
    body = await request.json()
    token = body.get("token", "").strip()
    expected = _get_expected_token()
    if not expected:
        return JSONResponse(content={"status": "no_auth_configured"})
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    if token != expected:
        _log.warning("Auth login failed: token length expected=%d received=%d", len(expected), len(token))
        raise HTTPException(status_code=401, detail="Invalid token")
    resp = JSONResponse(content={"status": "ok"})
    resp.set_cookie(
        key="api_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 365,
        secure=request.url.scheme == "https",
    )
    return resp


@router.post("/auth/logout")
async def logout():
    resp = JSONResponse(content={"status": "ok"})
    resp.set_cookie(key="api_token", value="", httponly=True, samesite="lax", max_age=0)
    return resp


@router.get("/auth/status")
async def auth_status(request: Request):
    expected = _get_expected_token()
    if not expected:
        return {"enabled": False, "authenticated": True}
    cookie_token = (request.cookies.get("api_token") or "").strip()
    header_token = (request.headers.get("X-API-Token") or "").strip()
    authenticated = cookie_token == expected or header_token == expected
    return {"enabled": True, "authenticated": authenticated}
