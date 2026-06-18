"""Email notification sender via SMTP."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, address: str, password: str, receiver: str,
                 smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.address = address
        self.password = password
        self.receiver = receiver
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def is_configured(self) -> bool:
        return bool(self.address and self.password and self.receiver)

    def send(self, subject: str, body: str, is_html: bool = False) -> bool:
        if not self.is_configured():
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.address
            msg["To"] = self.receiver
            msg["Subject"] = subject

            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type, "utf-8"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.address, self.password)
                server.sendmail(self.address, self.receiver, msg.as_string())

            logger.info(f"Email terkirim ke {self.receiver}")
            return True

        except Exception as e:
            logger.error(f"Email error: {e}")
            return False

    def send_alert(self, subject: str, body: str) -> bool:
        """Send alert email."""
        return self.send(f"[Trading Alert] {subject}", body)

    def send_analysis(self, ticker: str, decision: str, summary: str) -> bool:
        """Send analysis report via email."""
        icons = {"BUY": "🟢 BELI", "SELL": "🔴 JUAL", "HOLD": "🟡 TAHAN"}
        subject = f"Analisis AI: {ticker} - {icons.get(decision, decision)}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {'#4CAF50' if decision == 'BUY' else '#f44336' if decision == 'SELL' else '#FF9800'};
                        color: white; padding: 20px; text-align: center;">
                <h2>🤖 Analisis AI: {ticker}</h2>
                <h3>{icons.get(decision, decision)}</h3>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <pre style="white-space: pre-wrap; font-size: 14px;">{summary}</pre>
            </div>
            <div style="padding: 10px; text-align: center; color: #666; font-size: 12px;">
                Dikirim oleh AI Trading Assistant
            </div>
        </body>
        </html>
        """

        return self.send(subject, html_body, is_html=True)

    def send_daily_summary(self, summary_text: str) -> bool:
        """Send daily summary email."""
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2196F3; color: white; padding: 20px; text-align: center;">
                <h2>📈 Daily Trading Summary</h2>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <pre style="white-space: pre-wrap; font-size: 14px;">{summary_text}</pre>
            </div>
        </body>
        </html>
        """

        return self.send("Daily Trading Summary", html_body, is_html=True)
