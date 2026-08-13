from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.setting import settings

_bearer = HTTPBearer(auto_error=False)


def create_access_token(
    subject: str, extra: Optional[dict] = None, expires_minutes: Optional[int] = None
) -> str:
    """Issue a signed JWT access token."""
    cfg = settings.auth
    exp = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or cfg.access_token_expire_minutes
    )
    payload: dict = {"sub": subject, "exp": exp, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def decode_token(token: str) -> dict:
    cfg = settings.auth
    return jwt.decode(token, cfg.jwt_secret, algorithms=[cfg.jwt_algorithm])


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """FastAPI dependency: validate the Bearer token and return its claims."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已过期") from None
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效令牌") from None
    return {"sub": payload.get("sub"), "payload": payload}
