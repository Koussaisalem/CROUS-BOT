from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    crous_search_url: str
    telegram_bot_token: str
    telegram_chat_id: str
    poll_interval_seconds: int
    poll_jitter_seconds: int
    http_timeout_seconds: int
    http_max_retries: int
    state_db_path: str
    log_level: str
    user_agent: str


def _get_int(name: str, default: int, minimum: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    value = int(raw_value)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _get_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        crous_search_url=_get_required("CROUS_SEARCH_URL"),
        telegram_bot_token=_get_required("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_get_required("TELEGRAM_CHAT_ID"),
        poll_interval_seconds=_get_int("POLL_INTERVAL_SECONDS", default=180, minimum=30),
        poll_jitter_seconds=_get_int("POLL_JITTER_SECONDS", default=20, minimum=0),
        http_timeout_seconds=_get_int("HTTP_TIMEOUT_SECONDS", default=15, minimum=5),
        http_max_retries=_get_int("HTTP_MAX_RETRIES", default=2, minimum=0),
        state_db_path=os.getenv("STATE_DB_PATH", "data/state.db").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        user_agent=os.getenv(
            "USER_AGENT", "CROUS-BOT/1.0 (+personal-use; respectful polling)"
        ).strip(),
    )