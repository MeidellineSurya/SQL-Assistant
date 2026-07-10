import json
from typing import Any

from groq import Groq

from app.core.config import settings

_client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

# Schema-aware: the model only ever sees the tables/columns that actually
# exist on the user's connection (from the cached introspection in
# Milestone 2), not a generic "write me SQL" prompt. This is what keeps
# generated SQL referencing real column names instead of hallucinated ones.
_SYSTEM_PROMPT = """You are a PostgreSQL expert that translates a natural language question into a single \
read-only SQL query, given a database schema.

Rules:
- Output ONLY a single SELECT statement. Never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, or REVOKE.
- Only reference tables and columns that appear in the provided schema.
- If the question cannot be answered with the given schema, still return your best-effort SELECT query \
against the closest matching tables/columns.
- Respond with strict JSON matching this shape, and nothing else: {"sql": "<the query>"}
"""


class GroqServiceError(Exception):
    pass


def _format_schema(schema: dict[str, Any]) -> str:
    lines = []
    for table in schema.get("tables", []):
        columns = ", ".join(f"{col['name']} ({col['data_type']})" for col in table.get("columns", []))
        lines.append(f"- {table['name']}: {columns}")
    return "\n".join(lines)


def generate_sql(question: str, schema: dict[str, Any]) -> str:
    if _client is None:
        raise GroqServiceError("GROQ_API_KEY is not configured")

    schema_text = _format_schema(schema)
    user_content = f"Schema:\n{schema_text}\n\nQuestion: {question}"

    try:
        response = _client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        sql = parsed["sql"]
    except Exception as exc:  # noqa: BLE001 - any Groq/parsing failure becomes a service error
        raise GroqServiceError(f"failed to generate SQL: {exc}") from exc

    return sql.strip()
