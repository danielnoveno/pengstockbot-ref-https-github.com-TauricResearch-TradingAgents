"""Layer 2: Market scanner - deteksi trending, pola teknikal, dan berita."""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MarketScanner:
    def __init__(self, db, price_tracker=None):
        self.db = db
        self.price_tracker = price_tracker

    def get_technical_indicators(self, ticker: str) -> Optional[dict]:
        """Hitung indikator teknikal — delegates to price_tracker."""
        if self.price_tracker:
            result = self.price_tracker.get_technical_indicators(ticker)
        else:
            # ponytail: fallback if price_tracker not injected (shouldn't happen)
            result = None
        if not result:
            return None
        # Add signals and timestamp for scanner consumers
        signals = []
        rsi = result.get("rsi")
        if rsi and rsi < 30:
            signals.append("OVERSOLD (RSI < 30)")
        elif rsi and rsi > 70:
            signals.append("OVERBOUGHT (RSI > 70)")
        if result.get("macd_bullish"):
            signals.append("MACD BULLISH CROSS")
        else:
            signals.append("MACD BEARISH")
        if result.get("above_sma20") and result.get("above_sma50"):
            signals.append("UPTREND (di atas MA20 & MA50)")
        elif not result.get("above_sma20") and not result.get("above_sma50"):
            signals.append("DOWNTREND (di bawah MA20 & MA50)")
        result["signals"] = signals
        result["timestamp"] = datetime.now().isoformat()
        return result

    def detect_volume_spike(self, ticker: str, threshold: float = 2.0) -> Optional[dict]:
        """Deteksi volume spike (volume > threshold x average)."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            if hist.empty or len(hist) < 5:
                return None

            avg_vol = hist['Volume'].iloc[:-1].mean()
            current_vol = hist['Volume'].iloc[-1]
            ratio = current_vol / avg_vol if avg_vol > 0 else 0

            if ratio >= threshold:
                return {
                    "ticker": ticker,
                    "current_volume": int(current_vol),
                    "avg_volume": int(avg_vol),
                    "ratio": round(ratio, 2),
                    "price": round(float(hist['Close'].iloc[-1]), 2),
                    "severity": "critical" if ratio >= 5.0 else "warning",
                    "message": f"📊 {ticker} VOLUME SPIKE {ratio:.1f}x rata-rata!",
                }
            return None
        except Exception as e:
            logger.warning(f"Gagal cek volume {ticker}: {e}")
            return None

    def get_market_overview(self) -> dict:
        """Overview kondisi market global."""
        from .. import config
        
        overview = {}
        for name, ticker in config.MARKET_INDICES.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=config.DATA_PERIOD_SHORT)
                if hist.empty:
                    continue

                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = ((current - prev) / prev) * 100 if prev != 0 else 0

                overview[name] = {
                    "price": round(float(current), 2),
                    "change_pct": round(float(change), 2),
                    "status": "🟢" if change >= 0 else "🔴",
                }
            except Exception:
                continue

        return overview

    def scan_trending(self, tickers: list[str]) -> list[dict]:
        """Scan semua ticker untuk deteksi trending/pola menarik."""
        from .. import config
        
        trending = []

        for ticker in tickers[:config.MAX_TRENDING_DISPLAY]:
            indicators = self.get_technical_indicators(ticker)
            if not indicators:
                continue

            score = 0
            reasons = []

            # RSI signals
            if indicators["rsi"]:
                if indicators["rsi"] < 30:
                    score += 3
                    reasons.append(f"RSI oversold ({indicators['rsi']})")
                elif indicators["rsi"] > 70:
                    score += 2
                    reasons.append(f"RSI overbought ({indicators['rsi']})")

            # MACD signal
            if indicators["macd_bullish"]:
                score += 2
                reasons.append("MACD bullish cross")

            # Trend
            if indicators["above_sma20"] and indicators["above_sma50"]:
                score += 1
                reasons.append("Uptrend")

            # Volume spike
            vol_info = self.detect_volume_spike(ticker, threshold=1.5)
            if vol_info:
                score += 2
                reasons.append(f"Volume spike {vol_info['ratio']}x")

            if score >= 2:
                trending.append({
                    "ticker": ticker,
                    "score": score,
                    "reasons": reasons,
                    "indicators": indicators,
                })

        trending.sort(key=lambda x: x["score"], reverse=True)
        return trending[:10]
