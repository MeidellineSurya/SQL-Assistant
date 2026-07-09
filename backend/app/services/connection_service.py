import time
import uuid
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.pool import NullPool

from app.core.security import decrypt_secret, encrypt_secret
from app.models.connection import DBConnection
from app.schemas.connection import ConnectionCreate, ConnectionTestResult, ConnectionUpdate

# Connections to a *target* DB (someone else's database, credentials the user
# supplied) are never pooled or held open across requests. NullPool means
# SQLAlchemy opens a fresh connection when asked and drops it on dispose —
# no idle connection sits around holding a stranger's credentials in memory.
_CONNECT_TIMEOUT_SECONDS = 5


class ConnectionNotFoundError(Exception):
    pass


def _build_target_url(conn: DBConnection, password: str) -> URL:
    return URL.create(
        drivername="postgresql+psycopg2",
        username=conn.username,
        password=password,
        host=conn.host,
        port=conn.port,
        database=conn.database_name,
        query={"sslmode": conn.ssl_mode} if conn.ssl_mode else {},
    )


@contextmanager
def scoped_engine(conn: DBConnection) -> Iterator[Engine]:
    password = decrypt_secret(conn.encrypted_password)
    url = _build_target_url(conn, password)
    engine = create_engine(url, poolclass=NullPool, connect_args={"connect_timeout": _CONNECT_TIMEOUT_SECONDS})
    try:
        yield engine
    finally:
        engine.dispose()


def list_connections(db: DBSession, user_id: uuid.UUID) -> list[DBConnection]:
    return list(db.query(DBConnection).filter(DBConnection.user_id == user_id).order_by(DBConnection.created_at))


def get_connection(db: DBSession, user_id: uuid.UUID, connection_id: uuid.UUID) -> DBConnection:
    conn = (
        db.query(DBConnection)
        .filter(DBConnection.id == connection_id, DBConnection.user_id == user_id)
        .one_or_none()
    )
    if conn is None:
        raise ConnectionNotFoundError("connection not found")
    return conn


def create_connection(db: DBSession, user_id: uuid.UUID, payload: ConnectionCreate) -> DBConnection:
    conn = DBConnection(
        user_id=user_id,
        name=payload.name,
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        username=payload.username,
        encrypted_password=encrypt_secret(payload.password),
        ssl_mode=payload.ssl_mode,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def update_connection(
    db: DBSession, user_id: uuid.UUID, connection_id: uuid.UUID, payload: ConnectionUpdate
) -> DBConnection:
    conn = get_connection(db, user_id, connection_id)
    data = payload.model_dump(exclude_unset=True)

    password = data.pop("password", None)
    for field, value in data.items():
        setattr(conn, field, value)
    if password is not None:
        conn.encrypted_password = encrypt_secret(password)

    db.commit()
    db.refresh(conn)
    return conn


def delete_connection(db: DBSession, user_id: uuid.UUID, connection_id: uuid.UUID) -> None:
    conn = get_connection(db, user_id, connection_id)
    db.delete(conn)
    db.commit()


def test_connection(db: DBSession, user_id: uuid.UUID, connection_id: uuid.UUID) -> ConnectionTestResult:
    conn = get_connection(db, user_id, connection_id)
    start = time.monotonic()
    try:
        with scoped_engine(conn) as engine, engine.connect() as target:
            target.execute(text("SELECT 1"))
        latency_ms = int((time.monotonic() - start) * 1000)
        return ConnectionTestResult(success=True, latency_ms=latency_ms)
    except Exception as exc:  # noqa: BLE001 - surface any driver error as a test failure, not a 500
        return ConnectionTestResult(success=False, error=str(exc))
