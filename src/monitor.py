from __future__ import annotations

import logging
import random
import time

from requests import RequestException

from src.config import Settings
from src.crous_client import CrousClient
from src.models import Listing
from src.state_store import StateStore
from src.telegram_notifier import TelegramNotifier

LOGGER = logging.getLogger(__name__)


class MonitorService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = CrousClient(
            timeout_seconds=settings.http_timeout_seconds,
            max_retries=settings.http_max_retries,
            user_agent=settings.user_agent,
        )
        self.state_store = StateStore(settings.state_db_path)
        self.notifier = TelegramNotifier(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            timeout_seconds=settings.http_timeout_seconds,
        )

    def poll_once(self, dry_run: bool = False) -> tuple[int, int]:
        listings = self.client.fetch_listings(self.settings.crous_search_url)
        new_listings = self.state_store.filter_new(listings)

        if dry_run:
            for listing in new_listings:
                LOGGER.info("[DRY-RUN] New listing: %s | %s", listing.title, listing.url)
            return len(listings), len(new_listings)

        for listing in new_listings:
            self.notifier.send_new_listing(listing)
            LOGGER.info("Sent Telegram alert for: %s", listing.url)

        return len(listings), len(new_listings)

    def run_forever(self, dry_run: bool = False) -> None:
        failure_count = 0
        while True:
            try:
                total_count, new_count = self.poll_once(dry_run=dry_run)
                failure_count = 0
                LOGGER.info("Poll finished: total=%s new=%s", total_count, new_count)
            except RequestException as exc:
                failure_count += 1
                backoff = min(300, 2 ** min(failure_count, 8))
                LOGGER.warning("HTTP failure #%s (%s). Backing off for %ss", failure_count, exc, backoff)
                time.sleep(backoff)
            except Exception:
                failure_count += 1
                backoff = min(300, 2 ** min(failure_count, 8))
                LOGGER.exception("Unexpected failure #%s. Backing off for %ss", failure_count, backoff)
                time.sleep(backoff)

            sleep_seconds = _compute_sleep(
                interval=self.settings.poll_interval_seconds,
                jitter=self.settings.poll_jitter_seconds,
            )
            LOGGER.debug("Sleeping for %ss before next poll", sleep_seconds)
            time.sleep(sleep_seconds)


def _compute_sleep(interval: int, jitter: int) -> int:
    if jitter == 0:
        return interval
    delta = random.randint(-jitter, jitter)
    return max(30, interval + delta)


def print_new_listings_preview(listings: list[Listing]) -> None:
    for listing in listings:
        LOGGER.info("New listing preview: %s (%s)", listing.title, listing.url)