import uuid
from typing import Any

from sqlalchemy.orm import Session as DBSession

from app.models.chart import Chart
from app.services import groq_service, history_service

_VALID_CHART_TYPES = {"bar", "line", "pie", "scatter", "table"}


class ChartServiceError(Exception):
    pass


def suggest_chart_type(
    db: DBSession, user_id: uuid.UUID, query_id: uuid.UUID, columns: list[str], sample_rows: list[list[Any]]
) -> tuple[str, str]:
    # Ownership check only — suggestions aren't persisted, this just makes
    # sure the caller actually owns the query_id they're asking about.
    history_service.get_history_item(db, user_id, query_id)

    chart_type, reasoning = groq_service.suggest_chart_type(columns, sample_rows)
    if chart_type not in _VALID_CHART_TYPES:
        raise ChartServiceError(f"model suggested an unsupported chart type: {chart_type}")

    return chart_type, reasoning


def generate_chart(
    db: DBSession, user_id: uuid.UUID, query_id: uuid.UUID, chart_type: str, columns: list[str]
) -> Chart:
    history_service.get_history_item(db, user_id, query_id)

    if chart_type not in _VALID_CHART_TYPES:
        raise ChartServiceError(f"unsupported chart type: {chart_type}")

    config = groq_service.generate_chart_config(chart_type, columns)

    # Defense in depth, same principle as SQL validation in Milestone 4:
    # never trust the model's output enough to render it directly. If it
    # names a column that doesn't actually exist in this result set, reject
    # it here rather than letting the frontend crash on a missing key.
    column_set = set(columns)
    x_key = config.get("x_key")
    y_keys = config.get("y_keys") or []

    if x_key not in column_set:
        raise ChartServiceError(f"generated config references unknown column as x_key: {x_key}")
    unknown_y_keys = [key for key in y_keys if key not in column_set]
    if unknown_y_keys:
        raise ChartServiceError(f"generated config references unknown column(s) in y_keys: {unknown_y_keys}")
    if not y_keys:
        raise ChartServiceError("generated config has no y_keys")

    chart = Chart(query_id=query_id, chart_type=chart_type, config_json=config)
    db.add(chart)
    db.commit()
    db.refresh(chart)
    return chart
