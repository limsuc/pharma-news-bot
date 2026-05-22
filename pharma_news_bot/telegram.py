import logging
import sys
import time

import requests

from .config import Settings


logger = logging.getLogger(__name__)


class TelegramSender:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, message: str) -> dict:
        if self.settings.dry_run:
            logger.info("DRY_RUN enabled. Telegram message was not sent.")
            try:
                print(message)
            except UnicodeEncodeError:
                sys.stdout.buffer.write(message.encode("utf-8", errors="replace") + b"\n")
            return {"ok": True, "dry_run": True}

        if not self.settings.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is missing. Configure it in .env or GitHub Actions secrets.")

        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.settings.telegram_channel,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        last_error: Exception | None = None
        for attempt in range(1, self.settings.telegram_retry_count + 1):
            try:
                response = requests.post(url, data=payload, timeout=self.settings.request_timeout_seconds)
                if response.ok:
                    logger.info("Telegram send succeeded on attempt %s.", attempt)
                    return response.json()
                last_error = RuntimeError(f"Telegram API returned {response.status_code}: {response.text}")
            except requests.RequestException as exc:
                last_error = exc

            logger.warning("Telegram send attempt %s failed: %s", attempt, last_error)
            if attempt < self.settings.telegram_retry_count:
                time.sleep(self.settings.telegram_retry_delay_seconds)

        raise RuntimeError(f"Telegram send failed after retries: {last_error}")
