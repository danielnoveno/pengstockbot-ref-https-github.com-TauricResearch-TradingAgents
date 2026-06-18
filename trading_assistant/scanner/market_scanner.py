"""Layer 2: Market scanner - deteksi trending, pola teknikal, dan berita."""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import logging
import requests

logger = logging.getLogger(__name__)


class MarketScanner:
    def __init__(self, db):
        self.db = db

    def get_technical_indicators(self, ticker: str) -> Optional[dict]:
        """Hitung indikator teknikal: RSI, MACD, Moving Averages."""
        try:
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
            macd_hist = macd - signal

            # Moving Averages
            sma20 = close.rolling(20).mean()
            sma50 = close.rolling(50).mean()

            current = close.iloc[-1]
            result = {
                "ticker": ticker,
                "price": round(float(current), 2),
                "rsi": round(float(rsi.iloc[-1]), 2) if not np.isnan(rsi.iloc[-1]) else None,
                "macd": round(float(macd.iloc[-1]), 4),
                "macd_signal": round(float(signal.iloc[-1]), 4),
                "macd_histogram": round(float(macd_hist.iloc[-1]), 4),
                "sma20": round(float(sma20.iloc[-1]), 2) if not np.isnan(sma20.iloc[-1]) else None,
                "sma50": round(float(sma50.iloc[-1]), 2) if not np.isnan(sma50.iloc[-1]) else None,
                "above_sma20": bool(current > sma20.iloc[-1]) if not np.isnan(sma20.iloc[-1]) else None,
                "above_sma50": bool(current > sma50.iloc[-1]) if not np.isnan(sma50.iloc[-1]) else None,
                "macd_bullish": bool(macd.iloc[-1] > signal.iloc[-1]),
                "timestamp": datetime.now().isoformat(),
            }

            # Signal assessment
            signals = []
            if result["rsi"] and result["rsi"] < 30:
                signals.append("OVERSOLD (RSI < 30)")
            elif result["rsi"] and result["rsi"] > 70:
                signals.append("OVERBOUGHT (RSI > 70)")

            if result["macd_bullish"]:
                signals.append("MACD BULLISH CROSS")
            else:
                signals.append("MACD BEARISH")

            if result["above_sma20"] and result["above_sma50"]:
                signals.append("UPTREND (di atas MA20 & MA50)")
            elif not result["above_sma20"] and not result["above_sma50"]:
                signals.append("DOWNTREND (di bawah MA20 & MA50)")

            result["signals"] = signals
            return result

        except Exception as e:
            logger.warning(f"Gagal hitung indikator {ticker}: {e}")
            return None

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
        indices = {
            "IHSG": "^JKSE",
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "Dow Jones": "^DJI",
            "Nikkei": "^N225",
            "Hang Seng": "^HSI",
            "BTC": "BTC-USD",
        }

        overview = {}
        for name, ticker in indices.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
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
        trending = []

        for ticker in tickers:
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
