from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

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