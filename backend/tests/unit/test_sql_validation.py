from app.services.sql_service import validate_sql


def test_accepts_plain_select():
    is_valid, error = validate_sql("SELECT * FROM users")
    assert is_valid
    assert error is None


def test_accepts_union():
    is_valid, _ = validate_sql("SELECT id FROM users UNION SELECT id FROM archived_users")
    assert is_valid


def test_accepts_select_with_cte():
    is_valid, _ = validate_sql("WITH recent AS (SELECT * FROM orders) SELECT * FROM recent")
    assert is_valid


def test_rejects_multi_statement_injection():
    is_valid, error = validate_sql("SELECT * FROM users; DROP TABLE users;")
    assert not is_valid
    assert "single SQL statement" in error


def test_rejects_delete():
    is_valid, error = validate_sql("DELETE FROM users")
    assert not is_valid
    assert "SELECT statements are allowed" in error


def test_rejects_data_modifying_cte():
    # A SELECT at the top level can still smuggle a write via a CTE —
    # Postgres allows `WITH x AS (INSERT ... RETURNING *) SELECT * FROM x`.
    is_valid, error = validate_sql(
        "WITH x AS (INSERT INTO users (email) VALUES ('a') RETURNING id) SELECT * FROM x"
    )
    assert not is_valid
    assert "Insert" in error


def test_rejects_unparseable_sql():
    is_valid, error = validate_sql("SELEKT * FORM users")
    assert not is_valid
    assert error is not None
