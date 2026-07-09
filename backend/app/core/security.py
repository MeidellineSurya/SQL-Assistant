from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.core.config import settings

_fernet = Fernet(settings.fernet_key.encode()) if settings.fernet_key else None


def encrypt_secret(plaintext: str) -> str:
    if _fernet is None:
        raise RuntimeError("FERNET_KEY is not configured")
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    if _fernet is None:
        raise RuntimeError("FERNET_KEY is not configured")
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("could not decrypt stored credential") from exc


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _create_token(subject: UUID, expires_delta: timedelta, token_type: Literal["access", "refresh"]) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID) -> str:
    return _create_token(user_id, timedelta(minutes=settings.access_token_expire_minutes), "access")


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(user_id, timedelta(days=settings.refresh_token_expire_days), "refresh")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("invalid or expired token") from exc
