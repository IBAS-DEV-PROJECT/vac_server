import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import TokenExpiredException

ACCESS_TOKEN_TYPE = "access"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str:
    """Access Token을 검증하고 user_id를 반환한다.

    명세서에 인증 실패용 에러 코드가 TOKEN_EXPIRED 하나뿐이므로
    만료/위변조를 모두 동일한 코드로 응답한다.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
    except jwt.PyJWTError as exc:
        raise TokenExpiredException from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise TokenExpiredException

    user_id = payload.get("sub")
    if not user_id:
        raise TokenExpiredException
    return str(user_id)


def create_refresh_token() -> str:
    """추측 불가능한 난수 문자열을 Refresh Token 원문으로 사용한다."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Refresh Token은 원문 저장을 금지하므로 해시로만 보관한다."""
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
