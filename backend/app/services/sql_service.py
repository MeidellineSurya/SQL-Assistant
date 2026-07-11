import time
import uuid
from dataclasses import dataclass
from typing import Any

import sqlglot
from sqlglot import exp
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.models.query import QueryHistory
from app.services import connection_service, groq_service, history_service

# Allowlist, not a blocklist: only these top-level query shapes are accepted.
# Everything else (INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE/GRANT/COPY/
# unparseable admin commands like VACUUM) is rejected by simply not appearing
# here, rather than trying to enumerate every dangerous statement type.
_ALLOWED_TOP_LEVEL = (exp.Select, exp.Union, exp.Intersect, exp.Except)

# A statement can *look* like a SELECT at the top level while still smuggling
# a write in a nested clause — Postgres allows data-modifying CTEs, e.g.
# `WITH x AS (INSERT INTO t ... RETURNING *) SELECT * FROM x`. Walking the
# whole parsed tree (not just the top node) catches that.
_FORBIDDEN_NESTED = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Grant,
    exp.Copy,
    exp.Command,
)


class SqlServiceError(Exception):
    pass


@dataclass
class ExecutionResult:
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool


def validate_sql(sql: str) -> tuple[bool, str | None]:
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except Exception as exc:  # noqa: BLE001 - any parse failure is a validation failure, not a 500
        return False, f"could not parse SQL: {exc}"

    if len(statements) != 1:
        return False, "only a single SQL statement is allowed"

    statement = statements[0]
    if not isinstance(statement, _ALLOWED_TOP_LEVEL):
        return False, f"only SELECT statements are allowed (got {type(statement).__name__})"

    forbidden = list(statement.find_all(*_FORBIDDEN_NESTED))
    if forbidden:
        kinds = sorted({type(node).__name__ for node in forbidden})
        return False, f"disallowed statement type(s) found: {', '.join(kinds)}"

    return True, None


def generate_sql(db: DBSession, user_id: uuid.UUID, connection_id: uuid.UUID, question: str) -> QueryHistory:
    conn = connection_service.get_connection(db, user_id, connection_id)

    if not conn.schema_cache:
        raise SqlServiceError("this connection's schema hasn't been cached yet — refresh its schema first")

    sql = groq_service.generate_sql(question, conn.schema_cache)
    is_valid, _ = validate_sql(sql)

    history = QueryHistory(
        user_id=user_id,
        connection_id=conn.id,
        natural_language=question,
        generated_sql=sql,
        is_valid=is_valid,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def _run_against_target(conn, sql: str) -> ExecutionResult:
    with connection_service.scoped_engine(conn) as engine, engine.begin() as target:
        # SET LOCAL scopes both settings to this transaction only, which is
        # disposed immediately after (connection_service opens with NullPool).
        target.execute(text(f"SET LOCAL statement_timeout = {settings.sql_statement_timeout_ms}"))
        target.execute(text("SET TRANSACTION READ ONLY"))

        result = target.execute(text(sql))
        columns = list(result.keys())
        rows = result.fetchmany(settings.sql_max_rows + 1)

        truncated = len(rows) > settings.sql_max_rows
        rows = rows[: settings.sql_max_rows]

        return ExecutionResult(
            columns=columns,
            rows=[list(row) for row in rows],
            row_count=len(rows),
            truncated=truncated,
        )


def execute_sql(
    db: DBSession, user_id: uuid.UUID, history_id: uuid.UUID, sql: str
) -> tuple[QueryHistory, ExecutionResult | None]:
    original = history_service.get_history_item(db, user_id, history_id)

    if sql.strip() != original.generated_sql.strip():
        # The SQL was edited before running. Keep the original generated_sql
        # record intact — it's what the AI actually produced for that
        # question — and log this edited attempt as its own history entry
        # instead of silently overwriting the original.
        history = QueryHistory(
            user_id=user_id,
            connection_id=original.connection_id,
            natural_language=original.natural_language,
            generated_sql=sql,
        )
        db.add(history)
    else:
        history = original

    is_valid, validation_error = validate_sql(sql)
    history.is_valid = is_valid

    if not is_valid:
        history.was_executed = False
        history.error_message = validation_error
        db.commit()
        db.refresh(history)
        return history, None

    conn = connection_service.get_connection(db, user_id, history.connection_id)

    start = time.monotonic()
    try:
        result = _run_against_target(conn, sql)
    except Exception as exc:  # noqa: BLE001 - surface any driver/timeout error on the history row, not a 500
        history.was_executed = False
        history.execution_ms = int((time.monotonic() - start) * 1000)
        history.error_message = str(exc)
        db.commit()
        db.refresh(history)
        return history, None

    history.was_executed = True
    history.execution_ms = int((time.monotonic() - start) * 1000)
    history.row_count = result.row_count
    history.error_message = None
    db.commit()
    db.refresh(history)
    return history, result
