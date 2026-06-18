"""FastAPI Web Dashboard untuk Trading Assistant."""

import json
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


def create_app(db, watchlist_manager, price_tracker, scanner, notifier):
    app = FastAPI(title="AI Trading Assistant", version="1.0.0")

    # Setup templates
    templates_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"
    templates = Jinja2Templates(directory=str(templates_dir))

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ── Pages ──────────────────────────────────────────────
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    # ── API: Prices ────────────────────────────────────────
    @app.get("/api/prices")
    async def get_prices():
        tickers = watchlist_manager.get_tickers()
        prices = {}
        for ticker in tickers[:30]:
            latest = db.get_latest_price(ticker)
            if latest:
                prices[ticker] = latest
        return JSONResponse(prices)

    @app.get("/api/prices/{ticker}")
    async def get_price(ticker: str):
        latest = db.get_latest_price(ticker)
        if not latest:
            raise HTTPException(status_code=404, detail="Price not found")
        return JSONResponse(latest)

    @app.get("/api/prices/{ticker}/history")
    async def get_price_history(ticker: str, hours: int = 24):
        history = db.get_price_history(ticker, hours)
        return JSONResponse(history)

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
    async def get_alerts(limit: int = 50):
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
        """Trigger deep analysis untuk ticker tertentu."""
        from ..analysis.deep_analyzer import DeepAnalyzer
        analyzer = DeepAnalyzer(db, app.state.config if hasattr(app.state, 'config') else None)

        # Run analysis in background
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, analyzer.analyze, ticker)

        if result:
            return JSONResponse(result)
        raise HTTPException(status_code=500, detail="Analysis failed")

    # ── API: Market Overview ──────────────────────────────
    @app.get("/api/market-overview")
    async def get_market_overview():
        overview = scanner.get_market_overview()
        return JSONResponse(overview)

    # ── API: Scan Now ─────────────────────────────────────
    @app.post("/api/scan")
    async def trigger_scan():
        """Trigger manual scan semua watchlist."""
        tickers = watchlist_manager.get_tickers()
        result = price_tracker.scan_all(tickers)
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
        """Test kirim notifikasi ke semua channel."""
        result = notifier.send("🧪 **TEST NOTIFICATION**\nAI Trading Assistant berhasil terkoneksi!")
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
        })

    return app
