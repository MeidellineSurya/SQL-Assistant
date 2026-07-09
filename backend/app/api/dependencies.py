from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="could not validate credentials")

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise unauthorized from exc

    if payload.get("type") != "access":
        raise unauthorized

    user = db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise unauthorized

    return user
