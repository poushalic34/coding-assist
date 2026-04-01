from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import get_settings

_schema_ready = False
_schema_lock = Lock()


def is_db_configured() -> bool:
    settings = get_settings()
    return bool(settings.postgres_host and settings.postgres_password)


def _connection_kwargs() -> dict[str, Any]:
    settings = get_settings()
    kwargs: dict[str, Any] = {
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "dbname": settings.postgres_db,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
        "sslmode": settings.postgres_sslmode,
        "connect_timeout": 3,
        "cursor_factory": RealDictCursor,
    }
    cert_path = Path(settings.postgres_sslrootcert)
    if cert_path.exists():
        kwargs["sslrootcert"] = str(cert_path)
    elif settings.postgres_sslmode == "verify-full":
        kwargs["sslrootcert"] = "system"
    return kwargs


@contextmanager
def db_cursor():
    connection = psycopg2.connect(**_connection_kwargs())
    try:
        with connection:
            with connection.cursor() as cursor:
                yield cursor
    finally:
        connection.close()


def ensure_schema() -> None:
    global _schema_ready
    if _schema_ready or not is_db_configured():
        return

    with _schema_lock:
        if _schema_ready:
            return
        with db_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_state (
                    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    state JSONB NOT NULL DEFAULT '{}'::jsonb,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS assistant_history (
                    id BIGSERIAL PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    problem_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    latest_verdict TEXT NOT NULL,
                    coaching_mode TEXT NOT NULL,
                    focus_area TEXT,
                    hint_level TEXT NOT NULL,
                    guided_hint TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    complexity_suggestion TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS assistant_history_lookup_idx
                ON assistant_history (conversation_id, problem_id, created_at DESC);
                """
            )
        _schema_ready = True
