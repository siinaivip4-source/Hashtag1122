from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request

from src.core.config import config


def get_session_user(request: Request) -> Optional[dict]:
    if not config.auth_enabled:
        return {"email": "dev@tp.com.vn", "name": "Dev User"}
    return request.session.get("user")


def require_tp_user(
    request: Request,
    user: Annotated[Optional[dict], Depends(get_session_user)],
) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    if not config.is_email_allowed(user.get("email")):
        raise HTTPException(
            status_code=403,
            detail="Chỉ tài khoản email @tp.com.vn được truy cập",
        )
    return user
