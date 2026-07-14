import json
from collections.abc import Iterator
from typing import Any

from groq import Groq

from app.core.config import settings

_client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

# Schema-aware: the model only ever sees the tables/columns that actually
# exist on the user's connection (from the cached introspection in
# Milestone 2), not a generic "write me SQL" prompt. This is what keeps
# generated SQL referencing real column names instead of hallucinated ones.
_SQL_SYSTEM_PROMPT = """You are a PostgreSQL expert that translates a natural language question into a single \
read-only SQL query, given a database schema.

Rules:
- Output ONLY a single SELECT statement. Never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, or REVOKE.
- Only reference tables and columns that appear in the provided schema.
- If the question cannot be answered with the given schema, still return your best-effort SELECT query \
against the closest matching tables/columns.
- Respond with strict JSON matching this shape, and nothing else: {"sql": "<the query>"}
"""

_SUGGEST_CHART_SYSTEM_PROMPT = """You are a data visualization expert. Given the column names (and a small \
sample of rows) from a SQL query result, recommend the single best chart type to visualize it.

Valid chart types: "bar", "line", "pie", "scatter", "table". Use "table" when no chart meaningfully \
represents the data (e.g. a single row, a single value, or too many columns for a 2D chart).

Respond with strict JSON matching this shape, and nothing else: \
{"chart_type": "<one of the valid types>", "reasoning": "<one sentence>"}
"""

_GENERATE_CHART_SYSTEM_PROMPT = """You are a data visualization expert. Given a chart type and the column \
names from a SQL query result, produce a mapping of which column is the category/x-axis and which \
column(s) are the numeric series to plot.

Rules:
- x_key and every entry in y_keys MUST be exactly one of the provided column names, spelled identically.
- For "pie" charts, y_keys must contain exactly one column (the value to slice by); x_key is the label column.
- Respond with strict JSON matching this shape, and nothing else: \
{"x_key": "<column name>", "y_keys": ["<column name>", ...]}
"""

_EXPLAIN_SYSTEM_PROMPT = """You are a friendly SQL tutor. Given a user's original question and the SQL query \
that answers it, explain in plain English what the query does and how it works. Be concise (2-4 sentences), \
educational, and explain the *logic* (what's being joined, filtered, grouped, or aggregated, and why) rather \
than restating the SQL syntax verbatim.
"""


class GroqServiceError(Exception):
    pass


def _json_completion(system_prompt: str, user_content: str) -> dict[str, Any]:
    if _client is None:
        raise GroqServiceError("GROQ_API_KEY is not configured")

    try:
        response = _client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as exc:  # noqa: BLE001 - any Groq/parsing failure becomes a service error
        raise GroqServiceError(f"Groq request failed: {exc}") from exc


def _format_schema(schema: dict[str, Any]) -> str:
    lines = []
    for table in schema.get("tables", []):
        columns = ", ".join(f"{col['name']} ({col['data_type']})" for col in table.get("columns", []))
        lines.append(f"- {table['name']}: {columns}")
    return "\n".join(lines)


def generate_sql(question: str, schema: dict[str, Any]) -> str:
    schema_text = _format_schema(schema)
    user_content = f"Schema:\n{schema_text}\n\nQuestion: {question}"
    parsed = _json_completion(_SQL_SYSTEM_PROMPT, user_content)
    try:
        return parsed["sql"].strip()
    except (KeyError, AttributeError) as exc:
        raise GroqServiceError(f"malformed response from Groq: {parsed}") from exc


def suggest_chart_type(columns: list[str], sample_rows: list[list[Any]]) -> tuple[str, str]:
    user_content = f"Columns: {', '.join(columns)}\nSample rows: {json.dumps(sample_rows)}"
    parsed = _json_completion(_SUGGEST_CHART_SYSTEM_PROMPT, user_content)
    try:
        return parsed["chart_type"], parsed["reasoning"]
    except KeyError as exc:
        raise GroqServiceError(f"malformed response from Groq: {parsed}") from exc


def generate_chart_config(chart_type: str, columns: list[str]) -> dict[str, Any]:
    user_content = f"Chart type: {chart_type}\nColumns: {', '.join(columns)}"
    parsed = _json_completion(_GENERATE_CHART_SYSTEM_PROMPT, user_content)
    if "x_key" not in parsed or "y_keys" not in parsed:
        raise GroqServiceError(f"malformed response from Groq: {parsed}")
    return parsed


def stream_explanation(question: str, sql: str) -> Iterator[str]:
    if _client is None:
        raise GroqServiceError("GROQ_API_KEY is not configured")

    user_content = f"Question: {question}\n\nSQL:\n{sql}"
    try:
        stream = _client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": _EXPLAIN_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            stream=True,
            temperature=0,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as exc:  # noqa: BLE001 - any Groq/streaming failure becomes a service error
        raise GroqServiceError(f"Groq streaming request failed: {exc}") from exc
