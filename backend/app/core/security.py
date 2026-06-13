"""Security utilities — password hashing, JWT, and refresh token management."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AppException

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt (cost=12)."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_id: UUID) -> str:
    """Create a JWT access token with 15-minute expiry.

    Payload: sub=user_id, exp=now+15min, iat=now.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> UUID:
    """Decode and validate a JWT access token, returning the user_id.

    Raises AppException(40101) if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise AppException(code=40101, message="未认证", status_code=401)
        return UUID(user_id_str)
    except JWTError:
        raise AppException(code=40101, message="未认证", status_code=401) from None


def create_refresh_token() -> str:
    """Generate a 128-character hex refresh token (64 random bytes)."""
    return secrets.token_hex(64)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hash of a refresh token for secure DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()
