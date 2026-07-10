import uuid

from sqlalchemy.orm import Session as DBSession

from app.models.query import QueryHistory
from app.services import connection_service, groq_service


class SqlServiceError(Exception):
    pass


def generate_sql(db: DBSession, user_id: uuid.UUID, connection_id: uuid.UUID, question: str) -> QueryHistory:
    conn = connection_service.get_connection(db, user_id, connection_id)

    if not conn.schema_cache:
        raise SqlServiceError("this connection's schema hasn't been cached yet — refresh its schema first")

    sql = groq_service.generate_sql(question, conn.schema_cache)

    history = QueryHistory(
        user_id=user_id,
        connection_id=conn.id,
        natural_language=question,
        generated_sql=sql,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
