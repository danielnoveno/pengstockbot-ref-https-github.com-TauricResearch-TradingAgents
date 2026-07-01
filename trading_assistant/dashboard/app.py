"""FastAPI Web Dashboard - Bloomberg Terminal Style."""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


def create_app(db, watchlist_manager, price_tracker, scanner, notifier):
    app = FastAPI(title="AI Trading Terminal", version="2.0.0")

    from .. import config

    templates_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"
    templates = Jinja2Templates(directory=str(templates_dir))

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ── Shared helpers ──────────────────────────────────────

    async def _llm_complete(prompt: str) -> Optional[str]:
        """Try Google → OpenRouter → Groq for LLM completion."""
        if config.GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.GOOGLE_API_KEY)
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(prompt)
                return response.text
            except Exception:
                pass

        import httpx
        if config.OPENROUTER_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "google/gemini-2.0-flash-001",
                            "messages": [{"role": "user", "content": prompt}]
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]
            except Exception:
                pass

        if config.GROQ_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {config.GROQ_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [{"role": "user", "content": prompt}]
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]
            except Exception:
                pass

        return None

    async def _fetch_news(ticker: str = "", market: str = "ALL", limit: int = 15) -> list[dict]:
        """Shared news fetcher from ActuallyFreeAPI + Google News RSS."""
        import httpx
        news_items = []

        market_queries = {
            "ALL": "",
            "IDX": "Indonesia stock market IHSG BEI IDX",
            "US": "US stock market Wall Street NASDAQ NYSE",
            "CRYPTO": "cryptocurrency Bitcoin Ethereum crypto",
            "GLOBAL": "global stock market economy"
        }
        market_query = market_queries.get(market, "")

        # Source 1: ActuallyFreeAPI
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                params = {"limit": limit * 2}
                if ticker:
                    params["ticker"] = ticker
                resp = await client.get(
                    "https://actually-free-api.vercel.app/api/news",
                    params=params
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("data", []):
                        title = (item.get("title") or "").lower()
                        desc = (item.get("description") or "").lower()
                        if market != "ALL" and market_query:
                            keywords = market_query.lower().split()
                            if not any(kw in title or kw in desc for kw in keywords):
                                continue
                        news_items.append({
                            "title": item.get("title", ""),
                            "description": item.get("description", ""),
                            "source": item.get("source", ""),
                            "link": item.get("link", ""),
                            "pub_date": item.get("pub_date", ""),
                            "tickers": item.get("tickers", []),
                        })
        except Exception:
            pass

        # Source 2: Google News RSS (fallback)
        if len(news_items) < 5:
            try:
                import feedparser
                search_query = f"{market_query} {ticker} stock market".strip() if market_query else f"stock market news"
                rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:limit - len(news_items)]:
                    news_items.append({
                        "title": entry.get("title", ""),
                        "description": entry.get("summary", "")[:200],
                        "source": entry.get("source", {}).get("title", "Google News"),
                        "link": entry.get("link", ""),
                        "pub_date": entry.get("published", ""),
                        "tickers": [],
                    })
            except Exception:
                pass

        return news_items[:limit]

    # ── Pages ──────────────────────────────────────────────

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return templates.TemplateResponse(request, "index.html")

    # ── API: Prices ────────────────────────────────────────

    @app.get("/api/prices")
    async def get_prices():
        """Fetch LIVE prices from price_tracker."""
        tickers = watchlist_manager.get_tickers()
        result = price_tracker.scan_all(tickers[:config.MAX_TICKERS_SCAN])
        return JSONResponse(result["prices"])

    @app.get("/api/prices/{ticker}")
    async def get_price(ticker: str):
        """Fetch LIVE price for single ticker."""
        data = price_tracker.get_current_price(ticker)
        if not data:
            raise HTTPException(status_code=404, detail="No data")
        return JSONResponse(data)

    @app.get("/api/prices/{ticker}/history")
    async def get_price_history(ticker: str, hours: int = 24):
        history = db.get_price_history(ticker, hours)
        return JSONResponse(history)

    @app.get("/api/quotes")
    async def get_multi_quotes(tickers: str):
        """Get quick quotes for multiple tickers (comma-separated)."""
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        if not ticker_list:
            raise HTTPException(status_code=400, detail="No tickers provided")
        result = {}
        for ticker in ticker_list[:20]:
            data = price_tracker.get_current_price(ticker)
            if data:
                result[ticker] = data
        return JSONResponse(result)

    # ── API: Watchlist ────────────────────────────────────

    @app.get("/api/watchlist")
    async def get_watchlist():
        return JSONResponse(watchlist_manager.get_all())

    @app.post("/api/watchlist/add")
    async def add_to_watchlist(request: Request):
        data = await request.json()
        ticker = data.get("ticker", "").upper()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker required")
        watchlist_manager.add(ticker)
        return {"status": "ok", "message": f"{ticker} ditambahkan"}

    @app.post("/api/watchlist/remove")
    async def remove_from_watchlist(request: Request):
        data = await request.json()
        ticker = data.get("ticker", "")
        watchlist_manager.remove(ticker)
        return {"status": "ok", "message": f"{ticker} dihapus"}

    # ── API: Alerts ────────────────────────────────────────

    @app.get("/api/alerts")
    async def get_alerts(limit: int = None):
        if limit is None:
            limit = config.MAX_ALERTS_DISPLAY
        alerts = db.get_recent_alerts(limit)
        return JSONResponse(alerts)

    # ── API: Trending ─────────────────────────────────────

    @app.get("/api/trending")
    async def get_trending():
        trending = db.get_trending(hours=24)
        return JSONResponse(trending)

    # ── API: Analysis ─────────────────────────────────────

    @app.get("/api/analysis/{ticker}")
    async def get_analysis(ticker: str):
        analysis = db.get_latest_analysis(ticker)
        if not analysis:
            raise HTTPException(status_code=404, detail="No analysis found")
        return JSONResponse(analysis)

    @app.post("/api/analyze/{ticker}")
    async def trigger_analysis(ticker: str):
        """Trigger deep analysis - uses TradingAgents or fallback to technical analysis."""
        try:
            from ..analysis.deep_analyzer import DeepAnalyzer
            cfg = app.state.config if hasattr(app.state, 'config') else None
            analyzer = DeepAnalyzer(db, cfg)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, analyzer.analyze, ticker)
            if result:
                return JSONResponse(result)
        except Exception as e:
            print(f"TradingAgents failed: {e}")

        # Fallback: TA-Lib analysis
        try:
            import yfinance as yf
            import numpy as np
            import talib

            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            if hist.empty:
                raise HTTPException(status_code=404, detail="No data for ticker")

            close = hist['Close'].values.astype(np.float64)
            high = hist['High'].values.astype(np.float64)
            low = hist['Low'].values.astype(np.float64)

            rsi = talib.RSI(close, timeperiod=14)[-1]
            macd, signal, _ = talib.MACD(close)
            sma20 = talib.SMA(close, timeperiod=20)[-1]
            sma50 = talib.SMA(close, timeperiod=50)[-1]
            adx = talib.ADX(high, low, close, timeperiod=14)[-1]
            current_price = close[-1]

            signals = []
            if rsi < 30: signals.append("RSI OVERSOLD")
            elif rsi > 70: signals.append("RSI OVERBOUGHT")
            if macd[-1] > signal[-1]: signals.append("MACD BULLISH")
            else: signals.append("MACD BEARISH")
            if current_price > sma20 > sma50: signals.append("UPTREND")
            elif current_price < sma20 < sma50: signals.append("DOWNTREND")
            if adx > 25: signals.append("STRONG TREND")

            bullish_score = sum([
                rsi < 40, macd[-1] > signal[-1],
                current_price > sma20, current_price > sma50
            ])
            decision = "BUY" if bullish_score >= 3 else "SELL" if bullish_score <= 1 else "HOLD"

            summary = f"""=== AI ANALYSIS: {ticker} ===
Price: ${current_price:.2f}
RSI: {rsi:.1f} | MACD: {'Bullish' if macd[-1] > signal[-1] else 'Bearish'}
SMA20: ${sma20:.2f} | SMA50: ${sma50:.2f} | ADX: {adx:.1f}
Signals: {', '.join(signals)}
Decision: {decision} ({bullish_score}/4 bullish)"""

            return JSONResponse({
                "ticker": ticker, "decision": decision, "summary": summary,
                "confidence": bullish_score / 4, "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # ── API: Market Overview ──────────────────────────────

    @app.get("/api/market-overview")
    async def get_market_overview():
        overview = scanner.get_market_overview()
        return JSONResponse(overview)

    # ── API: Scan Now ─────────────────────────────────────

    @app.post("/api/scan")
    async def trigger_scan():
        tickers = watchlist_manager.get_tickers()
        result = price_tracker.scan_all(tickers[:config.MAX_TICKERS_SCAN])
        return JSONResponse({
            "prices_count": len(result["prices"]),
            "alerts_count": len(result["alerts"]),
            "alerts": result["alerts"],
        })

    # ── API: Notifications ────────────────────────────────

    @app.get("/api/notifications/status")
    async def notification_status():
        channels = notifier.get_configured_channels()
        return JSONResponse({
            "channels": channels,
            "telegram": notifier.telegram.is_configured(),
            "discord": notifier.discord.is_configured(),
            "email": notifier.email.is_configured(),
        })

    @app.post("/api/notifications/test")
    async def test_notification():
        result = notifier.send("TEST NOTIFICATION\nAI Trading Assistant berhasil terkoneksi!")
        return JSONResponse(result)

    # ── API: System Status ────────────────────────────────

    @app.get("/api/status")
    async def get_status():
        stats = watchlist_manager.get_stats()
        channels = notifier.get_configured_channels()
        return JSONResponse({
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "watchlist": stats,
            "notification_channels": channels,
            "config": {
                "refresh_interval": config.DASHBOARD_REFRESH_INTERVAL,
                "max_tickers": config.MAX_TICKERS_SCAN,
                "price_alert": config.PRICE_CHANGE_ALERT,
            },
        })

    # ── API: Chart Data (TradingView Lightweight) ─────────

    @app.get("/api/chart/{ticker}")
    async def get_chart_data(ticker: str, period: str = "3mo"):
        """Get OHLCV chart data for TradingView Lightweight Charts."""
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                raise HTTPException(status_code=404, detail="No data available")

            candles = []
            volume = []
            for date, row in hist.iterrows():
                timestamp = int(date.timestamp())
                candles.append({
                    "time": timestamp,
                    "open": round(float(row['Open']), 2),
                    "high": round(float(row['High']), 2),
                    "low": round(float(row['Low']), 2),
                    "close": round(float(row['Close']), 2),
                })
                volume.append({
                    "time": timestamp,
                    "value": int(row['Volume']),
                    "color": "rgba(59, 130, 246, 0.3)" if row['Close'] >= row['Open'] else "rgba(239, 68, 68, 0.3)",
                })

            return {"ticker": ticker, "candles": candles, "volume": volume, "count": len(candles)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ── API: Technical Analysis (TA-Lib + ta) ─────────────

    @app.get("/api/technical/{ticker}")
    async def get_technical_analysis(ticker: str, period: str = "3mo"):
        """Get technical indicators using TA-Lib and ta library."""
        try:
            import yfinance as yf
            import numpy as np
            import pandas as pd

            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty or len(hist) < 20:
                raise HTTPException(status_code=404, detail="Insufficient data")

            close = hist['Close'].values.astype(np.float64)
            high = hist['High'].values.astype(np.float64)
            low = hist['Low'].values.astype(np.float64)
            volume = hist['Volume'].values.astype(np.float64)

            result = {"ticker": ticker, "timestamp": datetime.now().isoformat()}

            try:
                import talib
                result["rsi"] = round(float(talib.RSI(close, timeperiod=14)[-1]), 2)
                macd, signal, hist_macd = talib.MACD(close)
                result["macd"] = round(float(macd[-1]), 4)
                result["macd_signal"] = round(float(signal[-1]), 4)
                result["macd_histogram"] = round(float(hist_macd[-1]), 4)
                result["macd_bullish"] = bool(macd[-1] > signal[-1])
                upper, middle, lower = talib.BBANDS(close)
                result["bb_upper"] = round(float(upper[-1]), 2)
                result["bb_middle"] = round(float(middle[-1]), 2)
                result["bb_lower"] = round(float(lower[-1]), 2)
                result["sma20"] = round(float(talib.SMA(close, timeperiod=20)[-1]), 2)
                result["sma50"] = round(float(talib.SMA(close, timeperiod=50)[-1]), 2)
                result["ema12"] = round(float(talib.EMA(close, timeperiod=12)[-1]), 2)
                result["adx"] = round(float(talib.ADX(high, low, close, timeperiod=14)[-1]), 2)
                result["atr"] = round(float(talib.ATR(high, low, close, timeperiod=14)[-1]), 2)
                result["patterns"] = {
                    "doji": bool(talib.CDLDOJI(hist['Open'].values, high, low, close)[-1]),
                    "hammer": bool(talib.CDLHAMMER(hist['Open'].values, high, low, close)[-1]),
                    "engulfing": int(talib.CDLENGULFING(hist['Open'].values, high, low, close)[-1]),
                }
                result["source"] = "TA-Lib"
            except ImportError:
                import ta
                df = pd.DataFrame(hist)
                rsi_ind = ta.momentum.RSIIndicator(close=df['Close'], window=14)
                result["rsi"] = round(float(rsi_ind.rsi().iloc[-1]), 2)
                macd_ind = ta.trend.MACD(close=df['Close'])
                result["macd"] = round(float(macd_ind.macd().iloc[-1]), 4)
                result["macd_signal"] = round(float(macd_ind.macd_signal().iloc[-1]), 4)
                result["macd_histogram"] = round(float(macd_ind.macd_diff().iloc[-1]), 4)
                result["macd_bullish"] = bool(macd_ind.macd().iloc[-1] > macd_ind.macd_signal().iloc[-1])
                bb = ta.volatility.BollingerBands(close=df['Close'], window=20)
                result["bb_upper"] = round(float(bb.bollinger_hband().iloc[-1]), 2)
                result["bb_middle"] = round(float(bb.bollinger_mavg().iloc[-1]), 2)
                result["bb_lower"] = round(float(bb.bollinger_lband().iloc[-1]), 2)
                result["sma20"] = round(float(df['Close'].rolling(20).mean().iloc[-1]), 2)
                result["sma50"] = round(float(df['Close'].rolling(50).mean().iloc[-1]), 2)
                result["source"] = "ta library"

            result["price"] = round(float(close[-1]), 2)
            result["change_pct"] = round(float(((close[-1] - close[-2]) / close[-2]) * 100), 2)
            result["volume"] = int(volume[-1])

            signals = []
            if result.get("rsi"):
                if result["rsi"] < 30: signals.append("OVERSOLD")
                elif result["rsi"] > 70: signals.append("OVERBOUGHT")
            if result.get("macd_bullish"): signals.append("MACD_BULLISH")
            else: signals.append("MACD_BEARISH")
            if result.get("sma20") and result.get("sma50"):
                if result["price"] > result["sma20"] > result["sma50"]: signals.append("UPTREND")
                elif result["price"] < result["sma20"] < result["sma50"]: signals.append("DOWNTREND")
            result["signals"] = signals

            return JSONResponse(result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ── API: Search Stocks ────────────────────────────────

    @app.get("/api/search")
    async def search_stocks(q: str):
        try:
            if len(q) < 1:
                return {"results": []}
            from yfinance.search import Search
            s = Search(q)
            results = s.response
            search_results = []
            if isinstance(results, dict) and "quotes" in results:
                for item in results["quotes"][:10]:
                    search_results.append({
                        "ticker": item.get("symbol", ""),
                        "name": item.get("longname", item.get("shortname", "")),
                        "exchange": item.get("exchange", ""),
                        "type": item.get("quoteType", ""),
                    })
            return {"results": search_results}
        except Exception as e:
            return {"results": [], "error": str(e)}

    # ── API: Financial News ──────────────────────────────

    @app.get("/api/news")
    async def get_news(ticker: str = "", category: str = "markets", market: str = "ALL", limit: int = 15):
        news_items = await _fetch_news(ticker=ticker, market=market, limit=limit)
        return {"news": news_items, "count": len(news_items), "market": market}

    # ── API: News Sentiment Analysis ─────────────────────

    @app.post("/api/news/analyze")
    async def analyze_news_sentiment(request: Request):
        try:
            body = await request.json()
            news_items = body.get("news", [])
            if not news_items:
                return {"analysis": "No news to analyze"}

            news_text = "\n".join([
                f"- {n.get('title', '')}. {n.get('description', '')[:100]}"
                for n in news_items[:10]
            ])
            prompt = f"""Analyze these financial news headlines and provide sentiment analysis.
For each news item, determine if it's POSITIVE, NEGATIVE, or NEUTRAL for the market.
Then provide an overall market sentiment summary.

News items:
{news_text}

Respond in this exact JSON format:
{{
    "overall_sentiment": "POSITIVE/NEGATIVE/NEUTRAL",
    "sentiment_score": 0.0 to 1.0 (1=very positive, 0=very negative),
    "impact_summary": "Brief summary of market impact",
    "items": [
        {{"title": "news title", "sentiment": "POSITIVE/NEGATIVE/NEUTRAL", "impact": "brief impact explanation"}}
    ]
}}"""

            result = await _llm_complete(prompt)
            if result:
                try:
                    start = result.find('{')
                    end = result.rfind('}') + 1
                    if start >= 0 and end > start:
                        analysis = json.loads(result[start:end])
                        return {"analysis": analysis}
                except Exception:
                    pass
                return {"analysis": {"raw_response": result}}

            return {"analysis": {"overall_sentiment": "NEUTRAL", "sentiment_score": 0.5, "impact_summary": "AI analysis unavailable", "items": []}}
        except Exception as e:
            return {"error": str(e)}

    # ── API: Hot News / Breaking News ────────────────────

    @app.get("/api/hot-news")
    async def get_hot_news():
        """Get hot/breaking news with AI impact analysis."""
        all_news = await _fetch_news(market="ALL", limit=20)
        top_news = all_news[:5]

        impact_analysis = None
        if top_news:
            news_text = "\n".join([f"- {n['title']}" for n in top_news])
            prompt = f"""Quick market impact analysis for these top news headlines.
For each, rate impact level (HIGH/MEDIUM/LOW) and affected market (US/IDX/CRYPTO/GLOBAL).

News:
{news_text}

Respond in JSON format:
{{
    "impacts": [
        {{"title": "news title", "impact_level": "HIGH/MEDIUM/LOW", "affected_market": "US/IDX/CRYPTO/GLOBAL", "brief": "one line impact"}}
    ]
}}"""
            result = await _llm_complete(prompt)
            if result:
                try:
                    start = result.find('{')
                    end = result.rfind('}') + 1
                    if start >= 0 and end > start:
                        impact_analysis = json.loads(result[start:end])
                except Exception:
                    pass

        return {"hot_news": top_news, "impact_analysis": impact_analysis, "total_count": len(all_news)}

    # ── API: News Engine (no AI cost) ─────────────────────

    @app.get("/api/news/scored")
    async def get_scored_news(market: str = "ALL", limit: int = 20):
        """News with sentiment + topics + impact scoring. Zero AI cost."""
        from trading_assistant.analysis.news_engine import batch_score
        news_items = await _fetch_news(market=market, limit=limit)
        result = batch_score(news_items)
        return result

    @app.get("/api/news/suggestions")
    async def get_news_suggestions(market: str = "ALL", limit: int = 20):
        """Market suggestions based on news. Zero AI cost."""
        from trading_assistant.analysis.news_engine import batch_score, generate_suggestions
        news_items = await _fetch_news(market=market, limit=limit)
        result = batch_score(news_items)
        suggestions = generate_suggestions(result["articles"])
        return {"suggestions": suggestions, "aggregate": result["aggregate"]}

    @app.get("/api/news/summarize")
    async def summarize_article(url: str = "", title: str = ""):
        """Summarize a single article. Uses extractive method (no AI)."""
        from trading_assistant.analysis.news_engine import extractive_summary, analyze_sentiment, extract_topics, estimate_impact
        text = title
        if url:
            try:
                import feedparser
                d = feedparser.parse(url)
                if d.entries:
                    text = f"{title}. {d.entries[0].get('summary', '')}"
            except Exception:
                pass
        summary = extractive_summary(text, max_sentences=3)
        sentiment = analyze_sentiment(text)
        topics = extract_topics(text)
        impact = estimate_impact(text)
        return {"summary": summary, "sentiment": sentiment, "topics": topics, "impact": impact}

    # ── WebSocket: Real-time Prices ───────────────────────

    @app.websocket("/ws/prices")
    async def websocket_prices(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                tickers = watchlist_manager.get_tickers()
                prices = {}
                for ticker in tickers[:config.MAX_TICKERS_SCAN]:
                    latest = db.get_latest_price(ticker)
                    if latest:
                        prices[ticker] = latest
                await websocket.send_json(prices)
                await asyncio.sleep(config.DASHBOARD_REFRESH_INTERVAL)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    return app
