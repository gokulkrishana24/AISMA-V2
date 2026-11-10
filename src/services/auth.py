from __future__ import annotations

import datetime
import os
import uuid
from typing import Any

import bcrypt
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "aisma_enterprise_super_secret_jwt_key_2026_dev_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Revoked token JTI store for secure logout invalidation
_REVOKED_TOKENS: set[str] = set()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta: datetime.timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.datetime.now(datetime.UTC)
    expire = now + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": f"jti_{uuid.uuid4().hex[:16]}",
            "token_use": "access",
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any], expires_delta: datetime.timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.datetime.now(datetime.UTC)
    expire = now + (expires_delta or datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": f"rt_{uuid.uuid4().hex[:16]}",
            "token_use": "refresh",
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def revoke_token(jti: str | None) -> None:
    if jti:
        _REVOKED_TOKENS.add(jti)


def is_token_revoked(jti: str | None) -> bool:
    return bool(jti and jti in _REVOKED_TOKENS)


def decode_access_token(token: str, expected_use: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if is_token_revoked(jti):
            raise ValueError("Token has been revoked via logout")
        if expected_use and payload.get("token_use") != expected_use:
            raise ValueError(f"Invalid token_use: expected '{expected_use}'")
        return payload
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid or expired JWT token: {e}") from e
