---
name: xfinance-data
description: Use when user needs to fetch market data with automatic failover. Trigger on keywords like xfinance, yfinance alternative, stock data, market data, failover, multi-source data. Use for fetching OHLCV, fundamentals, and market data with reliability.
---

# xFinance Data Skill

Use xfinance as a reliable alternative to yfinance with automatic multi-source failover.

## Quick Reference

```python
import xfinance as xf

# Single ticker
ticker = xf.Ticker("AAPL")
hist = ticker.history(period="1mo")
info = ticker.info

# Multiple tickers (concurrent)
data = xf.download(["AAPL", "MSFT", "GOOGL"], period="3mo")

# Get OHLCV
df = ticker.history(period="6mo", interval="1d")

# Get fundamentals
info = ticker.info  # dict with sector, industry, marketCap, etc.
financials = ticker.financials
balance_sheet = ticker.balance_sheet
cashflow = ticker.cashflow

# Get options
options = ticker.options
chain = ticker.option_chain

# Get dividends
dividends = ticker.dividends

# Get splits
splits = ticker.splits
```

## Failover Sources

When Yahoo Finance is unavailable, xfinance automatically falls back to:
1. **Stooq** - Free historical data
2. **SEC EDGAR** - US government data
3. **ECB** - European Central Bank (forex)
4. **Binance** - Crypto data
5. **CoinGecko** - Crypto alternative

## Caching

```python
# xfinance has built-in caching (5 min TTL)
# Create new instance for fresh data
ticker1 = xf.Ticker("AAPL")
ticker2 = xf.Ticker("AAPL")  # Separate cache

# Data is cached per Ticker instance
```

## Interval Options

```python
# Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
ticker.history(period="5d", interval="15m")  # 15-minute bars
ticker.history(period="1mo", interval="1d")   # Daily bars
ticker.history(period="1y", interval="1wk")   # Weekly bars
```

## Integration with Project

```python
# Replace yfinance with xfinance for reliability
import xfinance as xf

class PriceTracker:
    def get_current_price(self, ticker: str) -> dict:
        stock = xf.Ticker(ticker)
        hist = stock.history(period="2d")
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        return {
            'ticker': ticker,
            'price': round(current_price, 2),
            'change_pct': round(((current_price - prev_close) / prev_close) * 100, 2),
        }
```

## When to Use Over yfinance

- Yahoo Finance frequently breaks
- Need automatic failover
- Working with crypto (Binance/CoinGecko fallback)
- Production systems requiring high availability
- Rate limiting issues with Yahoo

## Installation

```bash
pip install xfinance
# Already installed in this project
```
