from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

from src.models import Listing


class StateStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_listings (
                    fingerprint TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def filter_new(self, listings: list[Listing]) -> list[Listing]:
        now = datetime.now(timezone.utc).isoformat()
        new_items: list[Listing] = []
        with closing(sqlite3.connect(self.db_path)) as conn:
            for listing in listings:
                row = conn.execute(
                    "SELECT 1 FROM seen_listings WHERE fingerprint = ?",
                    (listing.fingerprint,),
                ).fetchone()
                if row:
                    continue

                conn.execute(
                    """
                    INSERT INTO seen_listings (fingerprint, title, url, first_seen_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (listing.fingerprint, listing.title, listing.url, now),
                )
                new_items.append(listing)

            conn.execute(
                """
                INSERT INTO meta (key, value)
                VALUES ('last_poll_at', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (now,),
            )
            conn.commit()
        return new_items

    def get_meta(self, key: str) -> str | None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
            return row[0] if row else None

    def set_meta(self, key: str, value: str) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO meta (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            conn.commit()

    def reset_failure_count(self) -> None:
        self.set_meta("consecutive_failures", "0")

    def register_failure(self) -> int:
        current = self.get_meta("consecutive_failures")
        current_count = int(current) if current else 0
        next_count = current_count + 1
        self.set_meta("consecutive_failures", str(next_count))
        return next_count

    def should_send_heartbeat(self, interval_hours: int) -> bool:
        key = "last_heartbeat_at"
        now = datetime.now(timezone.utc)
        raw_value = self.get_meta(key)
        if not raw_value:
            self.set_meta(key, now.isoformat())
            return False

        last_value = datetime.fromisoformat(raw_value)
        if now - last_value >= timedelta(hours=interval_hours):
            self.set_meta(key, now.isoformat())
            return True
        return False

    def should_send_error_alert(self, cooldown_minutes: int) -> bool:
        key = "last_error_alert_at"
        now = datetime.now(timezone.utc)
        raw_value = self.get_meta(key)
        if not raw_value:
            self.set_meta(key, now.isoformat())
            return True

        last_value = datetime.fromisoformat(raw_value)
        if now - last_value >= timedelta(minutes=cooldown_minutes):
            self.set_meta(key, now.isoformat())
            return True
        return False