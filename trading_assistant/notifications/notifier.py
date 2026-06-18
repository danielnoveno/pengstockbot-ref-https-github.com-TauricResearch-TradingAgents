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

    def send_with_chart(self, message: str, chart_path: str = None, channels: list[str] = None):
        """Kirim pesan dengan grafik (khusus Telegram)."""
        return self.send(message, chart_path=chart_path, channels=channels)

    def send_price_alert(self, alert: dict, chart_path: str = None, channels: list[str] = None):
        """Kirim price alert dengan grafik."""
        ticker = alert.get("ticker", "")
        data = alert.get("data", {})
        change = data.get("change_pct", 0)
        price = data.get("price", 0)

        message = alert.get("message", f"{ticker}: {change:+.2f}%")

        if channels is None:
            channels = ["Telegram", "Discord"]

        for channel in channels:
            try:
                if channel == "Telegram":
                    if chart_path:
                        self.telegram.send_photo(chart_path, message)
                    else:
                        self.telegram.send_message(message)
                elif channel == "Discord":
                    self.discord.send_price_alert(ticker, change, price)
                elif channel == "Email":
                    self.email.send_alert(f"Price Alert: {ticker}", message)
            except Exception as e:
                logger.error(f"Gagal kirim price alert ke {channel}: {e}")

    def send_analysis(self, analysis: dict, chart_path: str = None, channels: list[str] = None):
        """Kirim analysis report dengan grafik."""
        ticker = analysis.get("ticker", "")
        decision = analysis.get("decision", "UNKNOWN")
        summary = analysis.get("summary", "")

        icons = {"BUY": "🟢 BELI", "SELL": "🔴 JUAL", "HOLD": "🟡 TAHAN"}
        message = f"🤖 **ANALISIS AI: {ticker}**\nKeputusan: {icons.get(decision, decision)}\n\n{summary}"

        if channels is None:
            channels = ["Telegram", "Discord", "Email"]

        for channel in channels:
            try:
                if channel == "Telegram":
                    if chart_path:
                        self.telegram.send_photo(chart_path, message)
                    else:
                        self.telegram.send_message(message)
                elif channel == "Discord":
                    self.discord.send_analysis(ticker, decision, summary)
                elif channel == "Email":
                    self.email.send_analysis(ticker, decision, summary)
            except Exception as e:
                logger.error(f"Gagal kirim analysis ke {channel}: {e}")

    def send_trending(self, trending_text: str, channels: list[str] = None):
        if channels is None:
            channels = ["Telegram", "Discord"]

        for channel in channels:
            try:
                if channel == "Telegram":
                    self.telegram.send_message(trending_text)
                elif channel == "Discord":
                    self.discord.send_trending(trending_text)
            except Exception as e:
                logger.error(f"Gagal kirim trending ke {channel}: {e}")

    def send_daily_summary(self, summary_text: str, channels: list[str] = None):
        if channels is None:
            channels = ["Telegram", "Discord", "Email"]

        for channel in channels:
            try:
                if channel == "Telegram":
                    self.telegram.send_message(summary_text)
                elif channel == "Discord":
                    self.discord.send_webhook(summary_text)
                elif channel == "Email":
                    self.email.send_daily_summary(summary_text)
            except Exception as e:
                logger.error(f"Gagal kirim summary ke {channel}: {e}")
