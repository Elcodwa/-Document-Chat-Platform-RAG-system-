"""
Authentication primitives: password hashing and JWT access/refresh tokens.

JWT payload shape (kept intentionally small):
    {
        "sub": "<user_id>",
        "tenant_id": "<tenant_id>",
        "is_admin": true/false,
        "type": "access" | "refresh",
        "exp": <unix timestamp>
    }

The tenant_id embedded in the token is what makes every downstream query
tenant-scoped (see core/tenant_context.py). A user can never pass a
different tenant_id on a request to "see" another tenant's data - the
tenant is derived only from the verified token, never from client input.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings
from app.exceptions import AuthenticationError

settings = get_settings()

# bcrypt has a hard 72-byte input limit - truncate defensively rather than
# letting the library raise on unusually long passphrases.
_MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    truncated = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        truncated = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
        return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def _create_token(*, subject: UUID, tenant_id: UUID, is_admin: bool, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "is_admin": is_admin,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(*, user_id: UUID, tenant_id: UUID, is_admin: bool) -> str:
    return _create_token(
        subject=user_id,
        tenant_id=tenant_id,
        is_admin=is_admin,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(*, user_id: UUID, tenant_id: UUID, is_admin: bool) -> str:
    return _create_token(
        subject=user_id,
        tenant_id=tenant_id,
        is_admin=is_admin,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token.") from exc

    if payload.get("type") != expected_type:
        raise AuthenticationError("Invalid token type.")
    return payload
