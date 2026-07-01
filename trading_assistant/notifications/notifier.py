"""Unified notification hub - kirim notifikasi ke semua channel sekaligus."""

import logging
from .telegram_bot import TelegramSender
from .discord_bot import DiscordSender
from .email_sender import EmailSender

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, config):
        self.telegram = TelegramSender(
            bot_token=config.TELEGRAM_BOT_TOKEN,
            chat_id=config.TELEGRAM_CHAT_ID,
        )
        self.discord = DiscordSender(
            bot_token=config.DISCORD_BOT_TOKEN,
            webhook_url=config.DISCORD_WEBHOOK_URL if hasattr(config, 'DISCORD_WEBHOOK_URL') else "",
        )
        self.email = EmailSender(
            address=config.EMAIL_ADDRESS,
            password=config.EMAIL_PASSWORD,
            receiver=config.EMAIL_RECEIVER,
            smtp_server=config.EMAIL_SMTP_SERVER,
            smtp_port=config.EMAIL_SMTP_PORT,
        )

    def get_configured_channels(self) -> list[str]:
        channels = []
        if self.telegram.is_configured():
            channels.append("Telegram")
        if self.discord.is_configured():
            channels.append("Discord")
        if self.email.is_configured():
            channels.append("Email")
        return channels

    def send(self, message: str, chart_path: str = None, channels: list[str] = None):
        """Kirim pesan, opsional dengan grafik."""
        if channels is None:
            channels = ["Telegram", "Discord", "Email"]

        results = {}
        for channel in channels:
            try:
                if channel == "Telegram":
                    if chart_path:
                        results["Telegram"] = self.telegram.send_photo(chart_path, message)
                    else:
                        results["Telegram"] = self.telegram.send_message(message)
                elif channel == "Discord":
                    results["Discord"] = self.discord.send_webhook(message)
                elif channel == "Email":
                    results["Email"] = self.email.send("Trading Alert", message)
            except Exception as e:
                logger.error(f"Gagal kirim ke {channel}: {e}")
                results[channel] = False

        return results
