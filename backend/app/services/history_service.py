import base64
import uuid
from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session as DBSession

from app.models.query import QueryHistory

# Keyset (cursor) pagination instead of LIMIT/OFFSET: offset pagination re-scans
# and discards N rows on every page, getting slower as users go deeper into
# their history, and rows can shift between pages if new queries are inserted
# mid-scroll. A cursor pins to "everything strictly after this exact row" by
# (created_at, id), so each page is a fixed-cost index seek regardless of
# depth, and it's stable even if new rows are inserted concurrently.
_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


class InvalidCursorError(Exception):
    pass


class HistoryItemNotFoundError(Exception):
    pass


def encode_cursor(created_at: datetime, item_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{item_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        created_at_str, id_str = raw.split("|")
        return datetime.fromisoformat(created_at_str), uuid.UUID(id_str)
    except (ValueError, UnicodeDecodeError) as exc:
        raise InvalidCursorError("invalid pagination cursor") from exc


def list_history(
    db: DBSession, user_id: uuid.UUID, limit: int = _DEFAULT_LIMIT, cursor: str | None = None
) -> tuple[list[QueryHistory], str | None]:
    limit = min(limit, _MAX_LIMIT)

    query = db.query(QueryHistory).filter(QueryHistory.user_id == user_id)

    if cursor is not None:
        cursor_created_at, cursor_id = _decode_cursor(cursor)
        query = query.filter(
            or_(
                QueryHistory.created_at < cursor_created_at,
                and_(QueryHistory.created_at == cursor_created_at, QueryHistory.id < cursor_id),
            )
        )

    query = query.order_by(QueryHistory.created_at.desc(), QueryHistory.id.desc())
    rows = query.limit(limit + 1).all()

    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = encode_cursor(items[-1].created_at, items[-1].id) if has_more else None

    return items, next_cursor


def get_history_item(db: DBSession, user_id: uuid.UUID, item_id: uuid.UUID) -> QueryHistory:
    item = (
        db.query(QueryHistory)
        .filter(QueryHistory.id == item_id, QueryHistory.user_id == user_id)
        .one_or_none()
    )
    if item is None:
        raise HistoryItemNotFoundError("history item not found")
    return item


def delete_history_item(db: DBSession, user_id: uuid.UUID, item_id: uuid.UUID) -> None:
    item = get_history_item(db, user_id, item_id)
    db.delete(item)
    db.commit()
