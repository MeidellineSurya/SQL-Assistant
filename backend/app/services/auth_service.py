from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.session import Session as SessionModel
from app.models.user import User


class AuthError(Exception):
    pass


def register_user(db: DBSession, email: str, password: str) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise AuthError("an account with this email already exists")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: DBSession, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("invalid email or password")
    if not user.is_active:
        raise AuthError("account is disabled")
    return user


def issue_tokens(db: DBSession, user: User) -> tuple[str, str]:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    db.add(SessionModel(user_id=user.id, refresh_token=refresh_token, expires_at=expires_at))
    db.commit()

    return access_token, refresh_token


def rotate_refresh_token(db: DBSession, refresh_token: str) -> tuple[str, str]:
    session = db.scalar(select(SessionModel).where(SessionModel.refresh_token == refresh_token))
    if not session or session.expires_at < datetime.now(UTC):
        raise AuthError("refresh token is invalid or expired")

    try:
        payload = decode_token(refresh_token)
    except ValueError as exc:
        raise AuthError("refresh token is invalid or expired") from exc
    if payload.get("type") != "refresh":
        raise AuthError("token is not a refresh token")

    user = db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise AuthError("account is disabled")

    # Rotate: revoke the old session, issue a fresh pair
    db.delete(session)
    db.commit()
    return issue_tokens(db, user)


def revoke_refresh_token(db: DBSession, refresh_token: str) -> None:
    session = db.scalar(select(SessionModel).where(SessionModel.refresh_token == refresh_token))
    if session:
        db.delete(session)
        db.commit()


def change_password(db: DBSession, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)

    # The caller is already authenticated via a valid access token, so this
    # doesn't require the old password. But once the password changes, every
    # other refresh token was issued under the old credential and should stop
    # working — otherwise a stolen refresh token would survive a password
    # change meant to lock it out. This includes the session that produced
    # the current access token, forcing a fresh login everywhere.
    db.query(SessionModel).filter(SessionModel.user_id == user.id).delete()
    db.commit()
