"""Hot detector - deteksi saham yang lagi hot/trending di pasar."""

import yfinance as yf
from datetime import datetime
import logging
import requests

logger = logging.getLogger(__name__)


class HotDetector:
    def __init__(self, db):
        self.db = db

    def get_gainers_losers(self) -> dict:
        """Ambil top gainers dan losers dari Yahoo Finance."""
        result = {"gainers": [], "losers": []}

        try:
            url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
            params = {"scrIds": "day_gainers", "count": 10}
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                quotes = data.get("finance", {}).get("result", [{}])[0].get("quotes", [])
                for q in quotes:
                    result["gainers"].append({
                        "ticker": q.get("symbol", ""),
                        "name": q.get("shortName", ""),
                        "price": q.get("regularMarketPrice", 0),
                        "change_pct": q.get("regularMarketChangePercent", 0),
                        "volume": q.get("regularMarketVolume", 0),
                    })
        except Exception as e:
            logger.warning(f"Gagal ambil gainers: {e}")

        try:
            params["scrIds"] = "day_losers"
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                quotes = data.get("finance", {}).get("result", [{}])[0].get("quotes", [])
                for q in quotes:
                    result["losers"].append({
                        "ticker": q.get("symbol", ""),
                        "name": q.get("shortName", ""),
                        "price": q.get("regularMarketPrice", 0),
                        "change_pct": q.get("regularMarketChangePercent", 0),
                        "volume": q.get("regularMarketVolume", 0),
                    })
        except Exception as e:
            logger.warning(f"Gagal ambil losers: {e}")

        return result

    def detect_price_anomaly(self, ticker: str) -> dict:
        """Deteksi anomali harga (gap up/down, breakout, dll)."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if hist.empty or len(hist) < 2:
                return {}

            today = hist.iloc[-1]
            yesterday = hist.iloc[-2]

            gap = ((today['Open'] - yesterday['Close']) / yesterday['Close']) * 100
            intraday_change = ((today['Close'] - today['Open']) / today['Open']) * 100

            anomalies = []
            if abs(gap) >= 2:
                direction = "UP" if gap > 0 else "DOWN"
                anomalies.append(f"Gap {direction} {abs(gap):.1f}%")

            if abs(intraday_change) >= 3:
                direction = "UP" if intraday_change > 0 else "DOWN"
                anomalies.append(f"Intraday {direction} {abs(intraday_change):.1f}%")

            if today['Volume'] > yesterday['Volume'] * 3:
                anomalies.append("Volume 3x+ average")

            return {
                "ticker": ticker,
                "gap_pct": round(gap, 2),
                "intraday_change": round(intraday_change, 2),
                "anomalies": anomalies,
                "has_anomaly": len(anomalies) > 0,
            }
        except Exception as e:
            logger.warning(f"Gagal deteksi anomali {ticker}: {e}")
            return {}

    def scan_market_movers(self, watchlist: list[str]) -> list[dict]:
        """Scan watchlist untuk temukan market movers."""
        movers = []

        for ticker in watchlist:
            anomaly = self.detect_price_anomaly(ticker)
            if anomaly.get("has_anomaly"):
                movers.append(anomaly)

        movers.sort(key=lambda x: abs(x.get("gap_pct", 0)), reverse=True)
        return movers[:10]

    def format_hot_alert(self, hot_stocks: list[dict], gainers_losers: dict) -> str:
        """Format alert untuk hot stocks."""
        lines = ["🔥 **HOT MARKET UPDATE** 🔥\n"]

        if hot_stocks:
            lines.append("**Market Movers:**")
            for s in hot_stocks[:5]:
                lines.append(f"  • {s['ticker']}: {', '.join(s['anomalies'])}")
            lines.append("")

        if gainers_losers.get("gainers"):
            lines.append("**Top Gainers:**")
            for g in gainers_losers["gainers"][:5]:
                lines.append(f"  🟢 {g['ticker']} ({g['name']}): +{g['change_pct']:.1f}%")
            lines.append("")

        if gainers_losers.get("losers"):
            lines.append("**Top Losers:**")
            for l in gainers_losers["losers"][:5]:
                lines.append(f"  🔴 {l['ticker']} ({l['name']}): {l['change_pct']:.1f}%")

        return "\n".join(lines)
