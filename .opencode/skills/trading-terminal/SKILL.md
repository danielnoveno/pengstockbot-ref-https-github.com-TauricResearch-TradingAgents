---
name: trading-terminal
description: Use when user wants to run or manage the Bloomberg-style trading terminal UI. Trigger on keywords like terminal, dashboard, UI, web interface, Bloomberg, start server, run app. Use for launching, configuring, or modifying the trading terminal.
---

# Trading Terminal Skill

Bloomberg-style web terminal for the AI Trading Assistant. Web-based now, can be wrapped with Electron/Tauri for desktop later.

## Start Terminal

```bash
# From project root
cd trading_assistant
python -m dashboard.app

# Or using main.py (includes terminal + background services)
python -m trading_assistant

# Access at http://localhost:8088
```

## Architecture

```
trading_assistant/
├── dashboard/
│   ├── app.py          # FastAPI backend
│   ├── templates/
│   │   └── index.html  # Bloomberg-style frontend
│   └── static/         # CSS/JS assets
├── scanner/
│   ├── price_tracker.py    # Layer 1: Real-time prices
│   ├── market_scanner.py   # Layer 2: Trending detection
│   └── hot_detector.py     # Hot stock detection
└── analysis/
    ├── deep_analyzer.py    # Layer 3: AI multi-agent analysis
    └── chart_generator.py  # Chart generation
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prices` | All watchlist prices |
| GET | `/api/prices/{ticker}` | Single ticker price |
| GET | `/api/prices/{ticker}/history` | Price history |
| GET | `/api/watchlist` | Get watchlist |
| POST | `/api/watchlist/add` | Add ticker to watchlist |
| POST | `/api/watchlist/remove` | Remove ticker |
| GET | `/api/alerts` | Recent alerts |
| GET | `/api/trending` | Trending stocks |
| POST | `/api/scan` | Trigger manual scan |
| POST | `/api/analyze/{ticker}` | Run AI analysis |
| GET | `/api/market-overview` | Global market overview |
| GET | `/api/status` | System status |

## Terminal Features

- **Market Overview**: IHSG, S&P 500, NASDAQ, Dow Jones, Nikkei, BTC
- **Watchlist Grid**: Real-time prices with color-coded changes
- **Alert Panel**: Critical/warning alerts with timestamps
- **Trending Panel**: Top stocks by technical score
- **AI Analysis**: Multi-agent deep analysis via TradingAgents
- **Watchlist Management**: Add/remove tickers
- **Notifications**: Telegram, Discord, Email status

## Desktop Conversion (Future)

```bash
# Option 1: Electron
npm init electron-app@latest trading-terminal
# Point to http://localhost:8088

# Option 2: Tauri (lighter)
cargo create tauri-app trading-terminal
# Embed webview pointing to terminal

# Option 3: PyWebView (Python)
pip install pywebview
# Wrap the web UI in native window
```

## Configuration

Edit `trading_assistant/config.py`:
- `DASHBOARD_HOST`: Default "0.0.0.0"
- `DASHBOARD_PORT`: Default 8088
- `PRICE_CHECK_INTERVAL`: Price refresh rate (seconds)
- `SCANNER_INTERVAL`: Scanner refresh rate (seconds)

## Integration with TA-Lib/ta

```python
# In price_tracker.py - use TA-Lib for indicators
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
        'bb_upper': talib.BBANDS(close)[0][-1],
    }
```
