"""Telegram Bot notification sender dengan support gambar."""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class TelegramSender:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str, parse_mode: str = None) -> bool:
        if not self.is_configured():
            return False

        try:
            chunks = self._split_message(text)
            for chunk in chunks:
                payload = {
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "disable_web_page_preview": True,
                }
                if parse_mode:
                    payload["parse_mode"] = parse_mode

                resp = requests.post(
                    f"{self.base_url}/sendMessage",
                    json=payload,
                    timeout=10,
                )
                if resp.status_code != 200:
                    logger.warning(f"Telegram error: {resp.status_code} - {resp.text}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """Kirim gambar dengan caption."""
        if not self.is_configured():
            return False

        try:
            # Telegram caption limit 1024 chars
            if len(caption) > 1020:
                # Kirim gambar tanpa caption, lalu kirim teks terpisah
                with open(photo_path, 'rb') as photo:
                    resp = requests.post(
                        f"{self.base_url}/sendPhoto",
                        data={"chat_id": self.chat_id},
                        files={"photo": photo},
                        timeout=15,
                    )
                if resp.status_code == 200:
                    return self.send_message(caption)
                return False

            with open(photo_path, 'rb') as photo:
                resp = requests.post(
                    f"{self.base_url}/sendPhoto",
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption,
                    },
                    files={"photo": photo},
                    timeout=15,
                )

            if resp.status_code != 200:
                logger.warning(f"Telegram photo error: {resp.status_code} - {resp.text}")
                return False
            return True

        except Exception as e:
            logger.error(f"Telegram send photo error: {e}")
            return False

    def send_alert(self, text: str) -> bool:
        return self.send_message(text)

    def _split_message(self, text: str, max_length: int = 4000) -> list[str]:
        if len(text) <= max_length:
            return [text]

        chunks = []
        lines = text.split("\n")
        current = ""

        for line in lines:
            if len(current) + len(line) + 1 > max_length:
                chunks.append(current)
                current = line
            else:
                current += "\n" + line if current else line

        if current:
            chunks.append(current)

        return chunks
