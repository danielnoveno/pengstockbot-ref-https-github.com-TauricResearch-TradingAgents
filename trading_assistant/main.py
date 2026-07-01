"""AI Trading Assistant - Main entry point."""

import sys
import os
import time
import logging
import threading
import schedule
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_assistant import config
from trading_assistant.config import (
    DATABASE_PATH, DASHBOARD_HOST, DASHBOARD_PORT,
    PRICE_CHECK_INTERVAL, SCANNER_INTERVAL,
)
from trading_assistant.database.db import Database
from trading_assistant.scanner.price_tracker import PriceTracker
from trading_assistant.scanner.market_scanner import MarketScanner
from trading_assistant.analysis.deep_analyzer import DeepAnalyzer
from trading_assistant.analysis.report_formatter import ReportFormatter
from trading_assistant.analysis.chart_generator import generate_full_chart
from trading_assistant.notifications.notifier import Notifier
from trading_assistant.notifications.telegram_handler import TelegramBotCommands
from trading_assistant.watchlist.manager import WatchlistManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("trading_assistant")


class TradingAssistant:
    def __init__(self):
        logger.info("Memulai AI Trading Assistant...")

        self.db = Database(str(DATABASE_PATH))
        self.watchlist = WatchlistManager(self.db, config)
        self.price_tracker = PriceTracker(self.db)
        self.scanner = MarketScanner(self.db, price_tracker=self.price_tracker)
        self.analyzer = DeepAnalyzer(self.db, config)
        self.notifier = Notifier(config)
        self.formatter = ReportFormatter()
        self.config = config

        # Telegram bot commands
        self.telegram_bot = TelegramBotCommands(
            db=self.db, watchlist_manager=self.watchlist,
            price_tracker=self.price_tracker, scanner=self.scanner,
            notifier=self.notifier, formatter=self.formatter,
        )

        self._last_prices = {}
        self._running = True

        logger.info(f"Komponen OK | Watchlist: {len(self.watchlist.get_tickers())} ticker")
        logger.info(f"Notifikasi: {', '.join(self.notifier.get_configured_channels()) or 'Tidak ada'}")

    # ── Immediate Scan (jalankan pertama kali) ────────────
    def immediate_scan(self):
        """Scan langsung saat aplikasi dimulai."""
        try:
            logger.info(" menjalankan scan awal...")
            tickers = self.watchlist.get_tickers()

            # Scan harga
            result = self.price_tracker.scan_all(tickers)
            prices = result["prices"]
            alerts = result["alerts"]

            # Kirim alert
            for alert in alerts:
                ticker = alert["ticker"]
                data = alert.get("data", {})
                indicators = alert.get("indicators")
                news = alert.get("news", "")

                report = self.formatter.format_price_alert(
                    alert=alert, news=news, indicators=indicators,
                )

                chart_path = None
                if abs(data.get("change_pct", 0)) >= 3:
                    try:
                        chart_path = generate_full_chart(ticker)
                    except Exception:
                        pass

                self.notifier.send(report, chart_path=chart_path)

            # Kirim ringkasan harga
            if prices:
                summary_lines = ["HARGA SAAT INI:\n"]
                for ticker, data in prices.items():
                    is_jk = ".JK" in ticker
                    price_str = f"Rp{data['price']:,.0f}" if is_jk else f"${data['price']:,.2f}"
                    change = data.get("change_pct", 0)
                    icon = "+" if change >= 0 else ""
                    summary_lines.append(f"{ticker}: {price_str} ({icon}{change:.2f}%)")
                self.notifier.send("\n".join(summary_lines))

            logger.info(f"Scan selesai: {len(prices)} harga, {len(alerts)} alerts")

        except Exception as e:
            logger.error(f"Immediate scan error: {e}")

    # ── Layer 1: Price Check Loop ─────────────────────────
    def price_check_loop(self):
        """Cek harga setiap menit."""
        while self._running:
            try:
                tickers = self.watchlist.get_tickers()
                if not tickers:
                    time.sleep(PRICE_CHECK_INTERVAL)
                    continue

                result = self.price_tracker.scan_all(tickers)
                prices = result["prices"]
                alerts = result["alerts"]

                for alert in alerts:
                    ticker = alert["ticker"]
                    data = alert.get("data", {})
                    indicators = alert.get("indicators")
                    news = alert.get("news", "")

                    report = self.formatter.format_price_alert(
                        alert=alert, news=news, indicators=indicators,
                    )

                    chart_path = None
                    if abs(data.get("change_pct", 0)) >= 3:
                        try:
                            chart_path = generate_full_chart(ticker)
                        except Exception:
                            pass

                self.notifier.send(report, chart_path=chart_path)

                self._last_prices = prices

            except Exception as e:
                logger.error(f"Price check error: {e}")

            time.sleep(PRICE_CHECK_INTERVAL)

    # ── Layer 2: Scanner Loop ─────────────────────────────
    def scanner_loop(self):
        """Scan trending setiap 5 menit."""
        while self._running:
            try:
                tickers = self.watchlist.get_tickers()
                trending = self.scanner.scan_trending(tickers)
                if trending:
                    report = self.formatter.format_trending_report(trending)
                    self.notifier.send(report)
            except Exception as e:
                logger.error(f"Scanner error: {e}")
            time.sleep(SCANNER_INTERVAL)

    # ── Morning Briefing ──────────────────────────────────
    def morning_briefing(self):
        try:
            overview = self.scanner.get_market_overview()
            tickers = self.watchlist.get_tickers()
            trending = self.scanner.scan_trending(tickers)
            prices = self.price_tracker.get_prices_batch(tickers[:config.MAX_TICKERS_SCAN])
            up = sum(1 for p in prices.values() if p.get("change_pct", 0) > 0)
            down = sum(1 for p in prices.values() if p.get("change_pct", 0) < 0)
            watchlist_summary = f"  {up} naik, {down} turun dari {len(prices)} saham"
            report = self.formatter.format_morning_briefing(overview, trending, watchlist_summary)
            self.notifier.send(report)
        except Exception as e:
            logger.error(f"Morning briefing error: {e}")

    # ── Evening Summary ───────────────────────────────────
    def evening_summary(self):
        try:
            tickers = self.watchlist.get_tickers()
            prices = self.price_tracker.get_prices_batch(tickers[:config.MAX_TICKERS_SCAN])
            alerts = self.db.get_recent_alerts(config.MAX_ALERTS_DISPLAY)
            trending = self.db.get_trending(hours=12)
            report = self.formatter.format_evening_summary(prices, alerts, trending)
            self.notifier.send(report)
        except Exception as e:
            logger.error(f"Evening summary error: {e}")

    # ── Run ───────────────────────────────────────────────
    def run(self):
        # Welcome
        stats = self.watchlist.get_stats()
        channels = self.notifier.get_configured_channels()

        welcome = (
            "AI Trading Assistant dimulai!\n\n"
            f"Watchlist: {stats['total']} ticker\n"
            f"Market: {stats['by_market']}\n"
            f"Notifikasi: {', '.join(channels) or 'Tidak ada'}\n\n"
            "Sedang scan harga..."
        )
        self.notifier.send(welcome)

        # Start Telegram bot commands
        self.telegram_bot.start_polling()
        logger.info("Telegram bot commands aktif")

        # SCAN AWAL - langsung jalan
        self.immediate_scan()

        # Start background threads
        threading.Thread(target=self.price_check_loop, daemon=True).start()
        threading.Thread(target=self.scanner_loop, daemon=True).start()

        # Scheduler - from config
        schedule.every().day.at(config.MORNING_BRIEFING_TIME).do(self.morning_briefing)
        schedule.every().day.at(config.EVENING_SUMMARY_TIME).do(self.evening_summary)

        def sched():
            while self._running:
                schedule.run_pending()
                time.sleep(30)
        threading.Thread(target=sched, daemon=True).start()

        logger.info("Semua aktif! Tekan Ctrl+C untuk berhenti.")

        # Dashboard di thread terpisah
        def run_dashboard():
            try:
                import uvicorn
                from trading_assistant.dashboard.app import create_app
                app = create_app(
                    db=self.db, watchlist_manager=self.watchlist,
                    price_tracker=self.price_tracker, scanner=self.scanner,
                    notifier=self.notifier,
                )
                app.state.config = self.config
                uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT)
            except Exception as e:
                logger.error(f"Dashboard error: {e}")

        threading.Thread(target=run_dashboard, daemon=True).start()
        logger.info(f"Dashboard: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")

        # Keep alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._running = False
            self.db.close()
            logger.info("Ditutup.")


def main():
    assistant = TradingAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
