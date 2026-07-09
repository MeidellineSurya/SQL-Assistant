import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from app.models.connection import DBConnection
from app.services.connection_service import get_connection, scoped_engine

_INTROSPECTION_QUERY = text(
    """
    SELECT table_name, column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position
    """
)


def refresh_schema(db: DBSession, user_id: uuid.UUID, connection_id: uuid.UUID) -> DBConnection:
    conn = get_connection(db, user_id, connection_id)

    tables: dict[str, list[dict]] = {}
    with scoped_engine(conn) as engine, engine.connect() as target:
        rows = target.execute(_INTROSPECTION_QUERY)
        for table_name, column_name, data_type, is_nullable in rows:
            tables.setdefault(table_name, []).append(
                {"name": column_name, "data_type": data_type, "is_nullable": is_nullable == "YES"}
            )

    snapshot = {"tables": [{"name": name, "columns": cols} for name, cols in tables.items()]}

    conn.schema_cache = snapshot
    conn.schema_cached_at = datetime.now(UTC)
    db.commit()
    db.refresh(conn)

    return conn
