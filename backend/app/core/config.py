from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App DB (SQLAlchemy connection string)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/sql_assistant"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Fernet key for encrypting target-DB credentials (Milestone 2)
    fernet_key: str = ""

    # Groq (Milestone 3)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Query execution (Milestone 4)
    sql_max_rows: int = 500
    sql_statement_timeout_ms: int = 5000

    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
