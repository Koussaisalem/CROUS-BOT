from __future__ import annotations

import logging

import requests

from src.models import Listing

LOGGER = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_ids: tuple[str, ...], timeout_seconds: int) -> None:
        self.chat_ids = chat_ids
        self.timeout_seconds = timeout_seconds
        self.base_endpoint = f"https://api.telegram.org/bot{bot_token}"
        self.endpoint = f"{self.base_endpoint}/sendMessage"

    def send_new_listing(self, listing: Listing) -> None:
        message = _format_listing_message(listing)
        self._send_message(message)

    def send_healthcheck(self) -> None:
        self._send_message("✅ CROUS monitor healthcheck: Telegram notifications are working.")

    def send_heartbeat(self) -> None:
        self._send_message("💓 CROUS monitor heartbeat: workflow is running normally.")

    def send_error_alert(self, failure_count: int, error_text: str) -> None:
        message = (
            "⚠️ CROUS monitor warning\n\n"
            f"Consecutive failures: {failure_count}\n"
            f"Latest error: {error_text[:300]}"
        )
        self._send_message(message)

    def send_text(self, text: str, chat_id: str | None = None) -> None:
        self._send_message(text, chat_id=chat_id)

    def get_updates(self, offset: int, limit: int = 20) -> list[dict]:
        payload = {
            "offset": offset,
            "limit": limit,
            "allowed_updates": ["message", "edited_message"],
        }
        response = requests.get(
            f"{self.base_endpoint}/getUpdates",
            params=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            LOGGER.warning("Telegram getUpdates returned non-ok payload")
            return []
        result = data.get("result", [])
        if not isinstance(result, list):
            return []
        return [item for item in result if isinstance(item, dict)]

    def _send_message(self, message: str, chat_id: str | None = None) -> None:
        target_chat_ids = (chat_id,) if chat_id else self.chat_ids
        for target_chat_id in target_chat_ids:
            payload = {
                "chat_id": target_chat_id,
                "text": message,
                "disable_web_page_preview": True,
            }
            response = requests.post(self.endpoint, json=payload, timeout=self.timeout_seconds)
            if response.status_code >= 400:
                LOGGER.error(
                    "Telegram send failed for chat_id=%s status=%s body=%s",
                    target_chat_id,
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()


def _format_listing_message(listing: Listing) -> str:
    lines = ["🏠 Nouveau logement CROUS détecté", "", f"Titre: {listing.title}"]
    if listing.price_eur is not None:
        lines.append(f"Prix: {listing.price_eur} €")
    if listing.city:
        lines.append(f"Ville: {listing.city}")
    if listing.residence:
        lines.append(f"Résidence: {listing.residence}")
    lines.extend(["", f"Voir: {listing.url}"])
    return "\n".join(lines)