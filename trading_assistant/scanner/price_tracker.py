"""Layer 1: Real-time price tracking dengan berita & indikator lengkap."""

import yfinance as yf
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PriceTracker:
    def __init__(self, db):
        self.db = db

    def get_current_price(self, ticker: str) -> Optional[dict]:
        """Ambil harga saat ini dari Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if hist.empty:
                return None

            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0
            change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close != 0 else 0

            return {
                "ticker": ticker,
                "price": round(current_price, 2),
                "prev_close": round(prev_close, 2),
                "change_pct": round(change_pct, 2),
                "volume": volume,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Gagal ambil harga {ticker}: {e}")
            return None

    def get_news(self, ticker: str) -> str:
        """Ambil berita terbaru untuk ticker DENGAN LINK."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                return "Tidak ada berita terbaru."

            lines = []
            for n in news[:5]:
                title = n.get("title", "")
                publisher = n.get("publisher", "")
                link = n.get("link", "")
                if title:
                    if link:
                        lines.append(f"  [{title}]({link})")
                    else:
                        lines.append(f"  {title}")
                    if publisher:
                        lines.append(f"    Sumber: {publisher}")
            return "\n".join(lines) if lines else "Tidak ada berita terbaru."
        except Exception as e:
            logger.warning(f"Gagal ambil berita {ticker}: {e}")
            return "Gagal mengambil berita."

    def get_news_list(self, ticker: str) -> list[dict]:
        """Ambil berita sebagai list of dicts (untuk formatter)."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                return []

            result = []
            for n in news[:5]:
                title = n.get("title", "")
                publisher = n.get("publisher", "")
                link = n.get("link", "")
                if title:
                    result.append({
                        "title": title,
                        "publisher": publisher,
                        "url": link,
                    })
            return result
        except Exception as e:
            logger.warning(f"Gagal ambil berita list {ticker}: {e}")
            return []

    def get_technical_indicators(self, ticker: str) -> Optional[dict]:
        """Hitung indikator teknikal lengkap."""
        try:
            import numpy as np
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            if hist.empty or len(hist) < 20:
                return None

            close = hist['Close']

            # RSI (14)
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()

            # Moving Averages
            sma20 = close.rolling(20).mean()
            sma50 = close.rolling(50).mean()

            current = close.iloc[-1]
            rsi_val = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else None

            return {
                "ticker": ticker,
                "price": round(float(current), 2),
                "rsi": round(rsi_val, 1) if rsi_val else None,
                "macd": round(float(macd.iloc[-1]), 4),
                "macd_signal": round(float(signal.iloc[-1]), 4),
                "macd_bullish": bool(macd.iloc[-1] > signal.iloc[-1]),
                "sma20": round(float(sma20.iloc[-1]), 2) if not np.isnan(sma20.iloc[-1]) else None,
                "sma50": round(float(sma50.iloc[-1]), 2) if not np.isnan(sma50.iloc[-1]) else None,
                "above_sma20": bool(current > sma20.iloc[-1]) if not np.isnan(sma20.iloc[-1]) else None,
                "above_sma50": bool(current > sma50.iloc[-1]) if not np.isnan(sma50.iloc[-1]) else None,
            }
        except Exception as e:
            logger.warning(f"Gagal hitung indikator {ticker}: {e}")
            return None

    def get_sentiment(self, ticker: str) -> str:
        """Quick sentiment check dari berita."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not news:
                return "Netral - tidak ada berita signifikan."

            # Simple keyword-based sentiment
            positive_words = ["naik", "surge", "rally", "profit", "untung", "rekor", "bagus",
                            "growth", "beli", "buy", "upgrade", "strong", "positif"]
            negative_words = ["turun", "jatuh", "crash", "rugi", "loss", "corporate", "masalah",
                            "downgrade", "jual", "sell", "weak", "negatif", "risiko"]

            pos_count = 0
            neg_count = 0
            for n in news[:5]:
                title = n.get("title", "").lower()
                for w in positive_words:
                    if w in title:
                        pos_count += 1
                for w in negative_words:
                    if w in title:
                        neg_count += 1

            if pos_count > neg_count:
                return f"POSITIF ({pos_count} berita positif vs {neg_count} negatif)"
            elif neg_count > pos_count:
                return f"NEGATIF ({neg_count} berita negatif vs {pos_count} positif)"
            else:
                return "NETRAL (berita campuran)"
        except Exception:
            return "Netral - tidak dapat menentukan sentimen."

    def check_alerts(self, ticker: str, price_data: dict) -> list[dict]:
        """Cek apakah ada alert yang perlu dikirim - dengan data lengkap."""
        alerts = []
        change = abs(price_data["change_pct"])

        # Get indicators and news for alerts
        indicators = None
        news = ""
        if change >= 2.5:
            indicators = self.get_technical_indicators(ticker)
            news = self.get_news(ticker)

        if change >= 5.0:
            alerts.append({
                "ticker": ticker,
                "type": "price_big_move",
                "severity": "critical",
                "message": f"{'NAIK' if price_data['change_pct'] > 0 else 'TURUN'} {abs(price_data['change_pct']):.2f}%",
                "data": price_data,
                "indicators": indicators,
                "news": news,
                "needs_full_analysis": True,
            })
        elif change >= 3.0:
            alerts.append({
                "ticker": ticker,
                "type": "price_alert",
                "severity": "warning",
                "message": f"{'Naik' if price_data['change_pct'] > 0 else 'Turun'} {abs(price_data['change_pct']):.2f}%",
                "data": price_data,
                "indicators": indicators,
                "news": news,
                "needs_full_analysis": False,
            })

        return alerts

    def scan_all(self, tickers: list[str]) -> dict:
        """Scan semua ticker dan return data + alerts."""
        prices = {}
        all_alerts = []

        for ticker in tickers:
            data = self.get_current_price(ticker)
            if data:
                prices[ticker] = data
                self.db.save_price(ticker, data["price"], data["volume"], data["change_pct"])
                alerts = self.check_alerts(ticker, data)
                all_alerts.extend(alerts)

        return {"prices": prices, "alerts": all_alerts}
