FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Railway assigns a dynamic $PORT at runtime; ${PORT:-8000} falls back to
# 8000 for `docker run` / other hosts that don't set it. Migrations run on
# every boot so a fresh deploy always has an up-to-date schema — local dev
# overrides this whole CMD via docker-compose.yml's --reload command.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
