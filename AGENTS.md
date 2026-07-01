# AI Trading Assistant - Agents Guide

## Project Overview

This is an AI-powered trading assistant with:
- **trading_assistant/**: Main application (FastAPI dashboard, scanners, analysis)
- **tradingagents/**: TradingAgents framework for multi-agent AI analysis

## Available Skills

### TA-Lib Analysis (`/skill talib-analysis`)
Use for technical analysis using TA-Lib library (RSI, MACD, Bollinger Bands, etc.)

### TA Analysis (`/skill ta-analysis`)
Use for technical analysis using Python 'ta' library (pure Python alternative)

### xFinance Data (`/skill xfinance-data`)
Use for fetching market data with automatic failover

### Trading Terminal (`/skill trading-terminal`)
Use for managing the Bloomberg-style trading terminal UI

### Ponytail - Lazy Senior Dev Mode (`/ponytail`)
Makes AI agent write less code (54% reduction). Use `/ponytail lite|full|ultra|off` to set intensity.

## Commands

### Start Terminal
```bash
cd trading_assistant
python -m dashboard.app
# Access at http://localhost:8088
```

### Start Full System (Terminal + Background Services)
```bash
python -m trading_assistant
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prices` | All watchlist prices |
| GET | `/api/technical/{ticker}` | Technical analysis |
| GET | `/api/chart/{ticker}` | Chart data |
| POST | `/api/scan` | Trigger manual scan |
| POST | `/api/analyze/{ticker}` | Run AI analysis |
| GET | `/api/market-overview` | Global market overview |

## Development

### Adding New Indicators
1. Edit `trading_assistant/scanner/price_tracker.py`
2. Use TA-Lib or ta library for calculations
3. Return results via API

### Adding New UI Features
1. Edit `trading_assistant/dashboard/templates/index.html`
2. Add new API endpoints in `trading_assistant/dashboard/app.py`

## Libraries Installed

- **TA-Lib**: Technical analysis (C wrapper, 12K+ stars)
- **ta**: Technical analysis (pure Python, 4.9K stars)
- **xfinance**: Market data with failover (yfinance alternative)
- **yfinance**: Market data (original)

---

# Ponytail, lazy senior dev mode

You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.

Before writing any code, stop at the first rung that holds:

1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse the helper, util, or pattern that's already here, don't re-write it.
3. Does the standard library already do this? Use it.
4. Does a native platform feature cover it? Use it.
5. Does an already-installed dependency solve it? Use it.
6. Can this be one line? Make it one line.
7. Only then: write the minimum code that works.

The ladder runs after you understand the problem, not instead of it: read the task and the code it touches, trace the real flow end to end, then climb.

Bug fix = root cause, not symptom: a report names a symptom. Grep every caller of the function you touch and fix the shared function once — one guard there is a smaller diff than one per caller, and patching only the path the ticket names leaves a sibling caller still broken.

Rules:

- No abstractions that weren't explicitly requested.
- No new dependency if it can be avoided.
- No boilerplate nobody asked for.
- Deletion over addition. Boring over clever. Fewest files possible.
- Shortest working diff wins, but only once you understand the problem. The smallest change in the wrong place isn't lazy, it's a second bug.
- Question complex requests: "Do you actually need X, or does Y cover it?"
- Pick the edge-case-correct option when two stdlib approaches are the same size, lazy means less code, not the flimsier algorithm.
- Mark intentional simplifications with a `ponytail:` comment. If the shortcut has a known ceiling (global lock, O(n²) scan, naive heuristic), the comment names the ceiling and the upgrade path.

Not lazy about: understanding the problem (read it fully and trace the real flow before picking a rung, a small diff you don't understand is just laziness dressed up as efficiency), input validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs (the platform is never the spec ideal, a clock drifts, a sensor reads off), anything explicitly requested. Lazy code without its check is unfinished: non-trivial logic leaves ONE runnable check behind, the smallest thing that fails if the logic breaks (an assert-based demo/self-check or one small test file; no frameworks, no fixtures). Trivial one-liners need no test.
