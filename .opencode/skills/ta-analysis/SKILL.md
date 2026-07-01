---
name: ta-analysis
description: Use when user needs technical analysis using Python 'ta' library (pure Python alternative to TA-Lib). Trigger on keywords like ta library, pandas ta, technical analysis python, RSI python, MACD python. Use ONLY for technical analysis calculations with pandas DataFrames.
---

# TA Library Technical Analysis Skill

Use the `ta` library for technical analysis with pandas DataFrames. Pure Python, no C dependencies.

## Quick Reference

```python
import ta

# From pandas DataFrame with columns: Open, High, Low, Close, Volume

# RSI
df['rsi'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()

# MACD
macd = ta.trend.MACD(close=df['Close'])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['macd_histogram'] = macd.macd_diff()

# Bollinger Bands
bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
df['bb_upper'] = bb.bollinger_hband()
df['bb_middle'] = bb.bollinger_mavg()
df['bb_lower'] = bb.bollinger_lband()

# Stochastic Oscillator
stoch = ta.momentum.StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'])
df['stoch_k'] = stoch.stoch()
df['stoch_d'] = stoch.stoch_signal()

# ADX (Average Directional Index)
adx = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14)
df['adx'] = adx.adx()
df['adx_pos'] = adx.adx_pos()
df['adx_neg'] = adx.adx_neg()

# ATR (Average True Range)
df['atr'] = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14).average_true_range()

# OBV (On Balance Volume)
df['obv'] = ta.volume.OnBalanceVolumeIndicator(close=df['Close'], volume=df['Volume']).on_balance_volume()

# VWAP
df['vwap'] = ta.volume.VolumeWeightedAveragePrice(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume']).volume_weighted_average_price()

# Ichimoku
ichimoku = ta.trend.IchimokuIndicator(high=df['High'], low=df['Low'], window1=9, window2=26, window3=52)
df['ichimoku_a'] = ichimoku.ichimoku_a()
df['ichimoku_b'] = ichimoku.ichimoku_b()
```

## Convenience: Add All Indicators

```python
# Add all indicators at once
from ta import add_all_ta_features
add_all_ta_features(df, open="Open", high="High", low="Low", close="Close", volume="Volume")

# Or add only momentum indicators
from ta import add_momentum_ta
add_momentum_ta(df, high="High", low="Low", close="Close", volume="Volume")
```

## Signal Detection

```python
# RSI signals
rsi = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
oversold = rsi < 30
overbought = rsi > 70

# MACD crossover
macd = ta.trend.MMACD(close=df['Close'])
macd_diff = macd.macd_diff()
bullish_cross = (macd_diff > 0) & (macd_diff.shift(1) <= 0)

# Bollinger Band squeeze
bb = ta.volatility.BollingerBands(close=df['Close'], window=20)
bb_width = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
squeeze = bb_width < bb_width.rolling(20).mean()
```

## Integration with Project

```python
# Pure Python - no C compiler needed
import ta
import yfinance as yf

def get_indicators(ticker: str) -> dict:
    df = yf.Ticker(ticker).history(period="3mo")
    
    rsi = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
    macd = ta.trend.MACD(close=df['Close'])
    
    return {
        'rsi': rsi.iloc[-1],
        'macd': macd.macd().iloc[-1],
        'macd_signal': macd.macd_signal().iloc[-1],
    }
```

## When to Use Over TA-Lib

- No C compiler available (Windows easier install)
- Working directly with pandas DataFrames
- Need Ichimoku or other advanced indicators
- Pure Python environment
