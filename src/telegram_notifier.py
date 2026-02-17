from __future__ import annotations

import logging

import requests

from src.models import Listing

LOGGER = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout_seconds: int) -> None:
        self.chat_id = chat_id
        self.timeout_seconds = timeout_seconds
        self.endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_new_listing(self, listing: Listing) -> None:
        message = _format_listing_message(listing)
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }
        response = requests.post(self.endpoint, json=payload, timeout=self.timeout_seconds)
        if response.status_code >= 400:
            LOGGER.error("Telegram send failed with status=%s body=%s", response.status_code, response.text)
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