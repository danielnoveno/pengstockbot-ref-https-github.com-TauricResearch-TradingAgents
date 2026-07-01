---
name: talib-analysis
description: Use when user needs technical analysis using TA-Lib library. Trigger on keywords like RSI, MACD, Bollinger Bands, SMA, EMA, ADX, Stochastic, candlestick patterns, technical indicators, TA-Lib. Use ONLY for technical analysis calculations, not for data fetching.
---

# TA-Lib Technical Analysis Skill

Use TA-Lib (Python wrapper) for computing technical indicators. Library is already installed.

## Quick Reference

```python
import talib
import numpy as np

# RSI (Relative Strength Index)
rsi = talib.RSI(close_prices, timeperiod=14)

# MACD
macd, signal, hist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)

# Bollinger Bands
upper, middle, lower = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2)

# Moving Averages
sma20 = talib.SMA(close_prices, timeperiod=20)
ema12 = talib.EMA(close_prices, timeperiod=12)

# ADX (Average Directional Index)
adx = talib.ADX(high, low, close, timeperiod=14)

# Stochastic
slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)

# ATR (Average True Range)
atr = talib.ATR(high, low, close, timeperiod=14)

# Volume indicators
obv = talib.OBV(close_prices, volume)
ad = talib.AD(high, low, close, volume)

# Candlestick patterns (returns integers)
doji = talib.CDLDOJI(open_prices, high, low, close)
hammer = talib.CDLHAMMER(open_prices, high, low, close)
engulfing = talib.CDLENGULFING(open_prices, high, low, close)
```

## Common Patterns

```python
# Get all candlestick patterns
patterns = {
    'CDLDOJI': 'Doji',
    'CDLHAMMER': 'Hammer',
    'CDLENGULFING': 'Engulfing',
    'CDLMORNINGSTAR': 'Morning Star',
    'CDL eveningstar': 'Evening Star',
    'CDL_SHOOTINGSTAR': 'Shooting Star',
}

# Detect oversold/overbought
rsi = talib.RSI(close, timeperiod=14)
oversold = rsi[-1] < 30
overbought = rsi[-1] > 70

# Trend detection
adx = talib.ADX(high, low, close, timeperiod=14)
strong_trend = adx[-1] > 25
```

## Input Requirements

- All price arrays must be numpy arrays (float64)
- OHLCV format: open, high, low, close, volume
- Minimum data points vary by indicator (e.g., RSI needs 14+, SMA needs period+)
- Data should be chronologically ordered (oldest first)

## Integration with Project

```python
# In trading_assistant/scanner/price_tracker.py
import talib

def get_technical_indicators(self, ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    hist = stock.history(period="3mo")
    
    close = hist['Close'].values.astype(np.float64)
    high = hist['High'].values.astype(np.float64)
    low = hist['Low'].values.astype(np.float64)
    
    return {
        'rsi': talib.RSI(close, timeperiod=14)[-1],
        'macd': talib.MACD(close)[0][-1],
        'sma20': talib.SMA(close, timeperiod=20)[-1],
    }
```
