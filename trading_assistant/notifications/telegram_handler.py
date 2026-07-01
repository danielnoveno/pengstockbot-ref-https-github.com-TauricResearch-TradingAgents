"""Telegram Bot Command Handler - bot interaktif untuk user."""

import logging
import threading
import yfinance as yf
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CHART_DIR = Path(__file__).parent.parent / "data" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)


class TelegramBotCommands:
    def __init__(self, db, watchlist_manager, price_tracker, scanner, notifier, formatter):
        self.db = db
        self.watchlist = watchlist_manager
        self.price_tracker = price_tracker
        self.scanner = scanner
        self.notifier = notifier
        self.formatter = formatter
        self._running = False

    def start_polling(self):
        """Start bot polling di background thread."""
        self._running = True
        thread = threading.Thread(target=self._poll_loop, daemon=True)
        thread.start()
        logger.info("Telegram bot polling started")

    def _poll_loop(self):
        """Poll updates dari Telegram."""
        import requests
        import time

        token = self.notifier.telegram.bot_token
        if not token:
            return

        offset = 0
        url = f"https://api.telegram.org/bot{token}"

        while self._running:
            try:
                resp = requests.get(f"{url}/getUpdates", params={"offset": offset, "timeout": 5}, timeout=10)
                data = resp.json()

                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        msg = update.get("message", {})
                        chat_id = msg.get("chat", {}).get("id")
                        text = msg.get("text", "")

                        if chat_id and text:
                            self._handle_command(chat_id, text)
            except Exception as e:
                logger.error(f"Poll error: {e}")

            time.sleep(2)

    def _handle_command(self, chat_id: int, text: str):
        """Route command ke handler yang tepat."""
        parts = text.strip().split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        handlers = {
            '/start': self._cmd_start,
            '/help': self._cmd_help,
            '/harga': self._cmd_harga,
            '/analisis': self._cmd_analisis,
            '/berita': self._cmd_berita,
            '/graffik': self._cmd_grafik,
            '/trending': self._cmd_trending,
            '/market': self._cmd_market,
            '/watchlist': self._cmd_watchlist,
            '/tambah': self._cmd_tambah,
            '/hapus': self._cmd_hapus,
            '/morning': self._cmd_morning,
            '/summary': self._cmd_summary,
            '/rsi': self._cmd_rsi,
            '/volume': self._cmd_volume,
            '/sentiment': self._cmd_sentiment,
        }

        handler = handlers.get(cmd)
        if handler:
            try:
                handler(chat_id, args)
            except Exception as e:
                self._send(chat_id, f"Error: {e}")
        elif cmd.startswith("/") and not cmd.startswith("//"):
            self._send(chat_id, f"Command tidak dikenal: {cmd}\nKetik /help untuk daftar command.")

    def _send(self, chat_id: int, text: str):
        """Kirim pesan teks."""
        self.notifier.telegram.send_message(text)

    def _send_photo(self, chat_id: int, path: str, caption: str = ""):
        """Kirim gambar."""
        self.notifier.telegram.send_photo(path, caption)

    # ══════════════════════════════════════════════════════
    # COMMAND HANDLERS
    # ══════════════════════════════════════════════════════

    def _cmd_start(self, chat_id, args):
        self._send(chat_id,
            "Selamat datang di AI Trading Bot!\n\n"
            "Ketik /help untuk melihat semua command yang tersedia."
        )

    def _cmd_help(self, chat_id, args):
        self._send(chat_id,
            "DAFTAR COMMAND:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "CEK SAHAM:\n"
            "  /harga BBCA - Cek harga real-time\n"
            "  /analisis BBCA - Analisis lengkap (TradingAgents)\n"
            "  /berita BBCA - Berita terbaru + link\n"
            "  /graffik BBCA - Kirim grafik harga\n"
            "  /rsi BBCA - Cek RSI saja\n"
            "  /volume BBCA - Cek volume\n"
            "  /sentiment BBCA - Cek sentimen pasar\n\n"
            "MARKET:\n"
            "  /trending - Saham trending hari ini\n"
            "  /market - Overview pasar global\n\n"
            "WATCHLIST:\n"
            "  /watchlist - Lihat daftar saham\n"
            "  /tambah BBCA - Tambah ke watchlist\n"
            "  /hapus BBCA - Hapus dari watchlist\n\n"
            "RINGKASAN:\n"
            "  /morning - Morning briefing\n"
            "  /summary - Ringkasan hari ini\n"
            "  /help - Tampilkan bantuan ini\n\n"
            "Contoh: Ketik /harga AAPL"
        )

    def _cmd_harga(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /harga BBCA\nAtau: /harga BBCA,TLKM,AAPL")
            return

        tickers = args[0].upper().split(",")
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                if hist.empty:
                    self._send(chat_id, f"Tidak ada data untuk {ticker}")
                    continue

                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = ((current - prev) / prev) * 100
                volume = int(hist['Volume'].iloc[-1])
                high = hist['High'].iloc[-1]
                low = hist['Low'].iloc[-1]

                is_jk = ".JK" in ticker
                pf = lambda x: f"Rp{x:,.0f}" if is_jk else f"${x:,.2f}"

                icon = "🟢" if change >= 0 else "🔴"
                self._send(chat_id,
                    f"{icon} HARGA {ticker}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Harga: {pf(current)}\n"
                    f"Tertinggi: {pf(high)}\n"
                    f"Terendah: {pf(low)}\n"
                    f"Perubahan: {change:+.2f}%\n"
                    f"Volume: {volume:,}\n"
                    f"\n{datetime.now().strftime('%H:%M:%S')}"
                )
            except Exception as e:
                self._send(chat_id, f"Error ambil {ticker}: {e}")

    def _cmd_analisis(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /analisis BBCA")
            return

        ticker = args[0].upper()
        self._send(chat_id, f"Sedang analisis {ticker}... (butuh 30-60 detik)")

        try:
            # Technical indicators
            indicators = self.price_tracker.get_technical_indicators(ticker)
            news = self.price_tracker.get_news_list(ticker)
            sentiment = self.price_tracker.get_sentiment(ticker)

            # Format
            report = self.formatter.format_full_analysis(
                ticker=ticker, indicators=indicators,
                news=news, sentiment=sentiment,
            )

            # Kirim teks
            self._send(chat_id, report)

            # Kirim grafik
            from trading_assistant.analysis.chart_generator import generate_full_chart
            chart_path = generate_full_chart(ticker)
            if chart_path:
                self._send_photo(chat_id, chart_path, f"Grafik {ticker}")

        except Exception as e:
            self._send(chat_id, f"Error analisis: {e}")

    def _cmd_berita(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /berita BBCA")
            return

        ticker = args[0].upper()
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                self._send(chat_id, f"Tidak ada berita untuk {ticker}")
                return

            lines = [f"BERITA {ticker}:\n"]
            for i, n in enumerate(news[:7], 1):
                title = n.get("title", "")
                publisher = n.get("publisher", "")
                link = n.get("link", "")
                if title:
                    lines.append(f"{i}. {title}")
                    if publisher:
                        lines.append(f"   Sumber: {publisher}")
                    if link:
                        lines.append(f"   {link}")
                    lines.append("")

            self._send(chat_id, "\n".join(lines))
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_grafik(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /graffik BBCA")
            return

        ticker = args[0].upper()
        self._send(chat_id, f"Membuat grafik {ticker}...")

        try:
            from trading_assistant.analysis.chart_generator import generate_full_chart
            chart_path = generate_full_chart(ticker)
            if chart_path:
                self._send_photo(chat_id, chart_path, f"Grafik {ticker}")
            else:
                self._send(chat_id, f"Gagal buat grafik {ticker}")
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_rsi(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /rsi BBCA")
            return

        ticker = args[0].upper()
        try:
            indicators = self.price_tracker.get_technical_indicators(ticker)
            if indicators and indicators.get("rsi"):
                rsi = indicators["rsi"]
                if rsi < 30:
                    status = "🟢 OVERSOLD (saham murah)"
                elif rsi < 50:
                    status = "🟡 Mendekati murah"
                elif rsi < 70:
                    status = "⚪ Normal"
                else:
                    status = "🔴 OVERBOUGHT (saham mahal)"

                self._send(chat_id,
                    f"RSI {ticker}: {rsi:.1f}\n"
                    f"Status: {status}\n\n"
                    f"RSI < 30 = murah (oversold)\n"
                    f"RSI > 70 = mahal (overbought)"
                )
            else:
                self._send(chat_id, f"Tidak ada data RSI untuk {ticker}")
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_volume(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /volume BBCA")
            return

        ticker = args[0].upper()
        try:
            vol_info = self.scanner.detect_volume_spike(ticker, threshold=1.0)
            if vol_info:
                ratio = vol_info["ratio"]
                if ratio >= 3:
                    status = "🔴 VOLUME SANGAT TINGGI!"
                elif ratio >= 2:
                    status = "🟡 Volume tinggi"
                elif ratio >= 1.5:
                    status = "⚪ Sedikit lebih aktif"
                else:
                    status = "🟢 Normal"

                self._send(chat_id,
                    f"VOLUME {ticker}:\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Hari ini: {vol_info['current_volume']:,}\n"
                    f"Rata-rata: {vol_info['avg_volume']:,}\n"
                    f"Ratio: {ratio:.1f}x\n"
                    f"Status: {status}"
                )
            else:
                self._send(chat_id, f"Tidak ada data volume untuk {ticker}")
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_sentiment(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /sentiment BBCA")
            return

        ticker = args[0].upper()
        try:
            sentiment = self.price_tracker.get_sentiment(ticker)
            self._send(chat_id,
                f"SENTIMEN {ticker}:\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{sentiment}"
            )
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_trending(self, chat_id, args):
        try:
            tickers = self.watchlist.get_tickers()
            trending = self.scanner.scan_trending(tickers)
            if trending:
                report = self.formatter.format_trending_report(trending)
                self._send(chat_id, report)
            else:
                self._send(chat_id, "Tidak ada saham trending saat ini.")
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_market(self, chat_id, args):
        try:
            overview = self.scanner.get_market_overview()
            report = self.formatter.format_market_overview(overview)
            self._send(chat_id, report)
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_watchlist(self, chat_id, args):
        try:
            items = self.watchlist.get_all()
            if not items:
                self._send(chat_id, "Watchlist kosong.")
                return

            lines = ["WATCHLIST:\n"]
            by_market = {}
            for item in items:
                m = item["market"]
                if m not in by_market:
                    by_market[m] = []
                by_market[m].append(item["ticker"])

            for market, tickers in by_market.items():
                lines.append(f"{market}: {', '.join(tickers)}")

            lines.append(f"\nTotal: {len(items)} ticker")
            lines.append("\nTambah: /tambah BBCA")
            lines.append("Hapus: /hapus BBCA")

            self._send(chat_id, "\n".join(lines))
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_tambah(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /tambah BBCA")
            return

        ticker = args[0].upper()
        try:
            self.watchlist.add(ticker)
            self._send(chat_id, f"{ticker} ditambahkan ke watchlist!")
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_hapus(self, chat_id, args):
        if not args:
            self._send(chat_id, "Format: /hapus BBCA")
            return

        ticker = args[0].upper()
        try:
            self.watchlist.remove(ticker)
            self._send(chat_id, f"{ticker} dihapus dari watchlist.")
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_morning(self, chat_id, args):
        try:
            overview = self.scanner.get_market_overview()
            tickers = self.watchlist.get_tickers()
            trending = self.scanner.scan_trending(tickers)
            prices = self.price_tracker.get_prices_batch(tickers[:10])
            up = sum(1 for p in prices.values() if p.get("change_pct", 0) > 0)
            down = sum(1 for p in prices.values() if p.get("change_pct", 0) < 0)
            wl_summary = f"  {up} naik, {down} turun dari {len(prices)} saham"
            report = self.formatter.format_morning_briefing(overview, trending, wl_summary)
            self._send(chat_id, report)
        except Exception as e:
            self._send(chat_id, f"Error: {e}")

    def _cmd_summary(self, chat_id, args):
        try:
            tickers = self.watchlist.get_tickers()
            prices = self.price_tracker.get_prices_batch(tickers)
            alerts = self.db.get_recent_alerts(20)
            trending = self.db.get_trending(hours=12)
            report = self.formatter.format_evening_summary(prices, alerts, trending)
            self._send(chat_id, report)
        except Exception as e:
            self._send(chat_id, f"Error: {e}")
