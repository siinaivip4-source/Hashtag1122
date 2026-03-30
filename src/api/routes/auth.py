from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import secrets

from src.core.config import config
from src.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPES = "openid email profile"


def _redirect_uri(request: Request) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/auth/google/callback"


@router.get("/me")
async def auth_me(request: Request) -> dict:
    if not config.auth_enabled:
        return {"email": "dev@tp.com.vn", "name": "Dev User", "allowed": True}
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    return {
        "email": user.get("email"),
        "name": user.get("name"),
        "allowed": config.is_email_allowed(user.get("email")),
    }


@router.get("/google")
async def auth_google(request: Request):
    if not config.auth_enabled:
        return RedirectResponse(url="/", status_code=302)
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = {
        "client_id": config.google_client_id,
        "redirect_uri": _redirect_uri(request),
        "response_type": "code",
        "scope": SCOPES,
        "prompt": "consent",
        "state": state,
    }
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=url, status_code=302)


@router.get("/google/callback", name="auth_google_callback")
async def auth_google_callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
):
    if error:
        logger.warning(f"Google OAuth error: {error}")
        return RedirectResponse(url="/login?error=denied", status_code=302)
    if not code:
        return RedirectResponse(url="/login?error=no_code", status_code=302)
    if not config.auth_enabled:
        return RedirectResponse(url="/", status_code=302)

    expected_state = request.session.pop("oauth_state", None)
    if not expected_state or not state or state != expected_state:
        logger.warning("Google OAuth state mismatch")
        return RedirectResponse(url="/login?error=state", status_code=302)

    redirect_uri = _redirect_uri(request)
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": config.google_client_id,
                "client_secret": config.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if token_res.status_code != 200:
        logger.error(f"Google token error: {token_res.status_code} {token_res.text}")
        return RedirectResponse(url="/login?error=token_failed", status_code=302)

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return RedirectResponse(url="/login?error=no_token", status_code=302)

    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if user_res.status_code != 200:
        logger.error(f"Google userinfo error: {user_res.status_code}")
        return RedirectResponse(url="/login?error=userinfo_failed", status_code=302)

    user_info = user_res.json()
    email = user_info.get("email")

    request.session["user"] = {
        "email": user_info.get("email"),
        "name": user_info.get("name") or user_info.get("email"),
    }

    if not config.is_email_allowed(email):
        logger.info(f"Login rejected: email domain not allowed: {email}")
        return RedirectResponse(url="/login?error=domain", status_code=302)

    logger.info(f"Login success: {email}")
    return RedirectResponse(url="/", status_code=302)


@router.get("/logout")
async def auth_logout(request: Request):
    if "user" in request.session:
        del request.session["user"]
    return RedirectResponse(url="/login", status_code=302)
