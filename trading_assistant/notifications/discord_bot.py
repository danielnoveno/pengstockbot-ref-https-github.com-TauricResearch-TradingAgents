"""Discord Bot notification sender via Webhook."""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class DiscordSender:
    def __init__(self, bot_token: str = "", webhook_url: str = ""):
        self.bot_token = bot_token
        self.webhook_url = webhook_url

    def is_configured(self) -> bool:
        return bool(self.webhook_url or self.bot_token)

    def send_webhook(self, content: str, embed: dict = None) -> bool:
        """Send via webhook (paling mudah, tidak perlu bot running)."""
        if not self.webhook_url:
            return False

        try:
            payload = {"content": content}
            if embed:
                payload["embeds"] = [embed]

            resp = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False

    def send_alert(self, title: str, description: str, color: int = 0x00FF00) -> bool:
        """Send alert sebagai Discord embed."""
        embed = {
            "title": title,
            "description": description,
            "color": color,
        }
        return self.send_webhook("", embed=embed)

    def send_price_alert(self, ticker: str, change_pct: float, price: float) -> bool:
        """Send price alert."""
        color = 0x00FF00 if change_pct > 0 else 0xFF0000
        icon = "🟢" if change_pct > 0 else "🔴"
        direction = "NAIK" if change_pct > 0 else "TURUN"

        title = f"{icon} {ticker} {direction} {abs(change_pct):.2f}%"
        description = f"Harga: {'Rp{:,.0f}'.format(price) if '.JK' in ticker else '${:,.2f}'.format(price)}"

        return self.send_alert(title, description, color)

    def send_analysis(self, ticker: str, decision: str, summary: str) -> bool:
        """Send analysis report."""
        colors = {
            "BUY": 0x00FF00,
            "SELL": 0xFF0000,
            "HOLD": 0xFFFF00,
        }
        icons = {
            "BUY": "🟢 BELI",
            "SELL": "🔴 JUAL",
            "HOLD": "🟡 TAHAN",
        }

        return self.send_alert(
            title=f"🤖 Analisis AI: {ticker}",
            description=f"**Keputusan:** {icons.get(decision, decision)}\n\n{summary[:1500]}",
            color=colors.get(decision, 0x808080),
        )

    def send_trending(self, trending_text: str) -> bool:
        """Send trending report."""
        return self.send_alert(
            title="📊 TRENDING MARKET",
            description=trending_text[:1500],
            color=0x00BFFF,
        )
