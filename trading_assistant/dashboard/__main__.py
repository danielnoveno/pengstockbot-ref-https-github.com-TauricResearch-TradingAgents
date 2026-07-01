"""Allow running as: python -m dashboard"""
import uvicorn
from trading_assistant.dashboard.app import create_app
from trading_assistant.database.db import Database
from trading_assistant.config import DATABASE_PATH, DASHBOARD_HOST, DASHBOARD_PORT
from trading_assistant.watchlist.manager import WatchlistManager
from trading_assistant.scanner.price_tracker import PriceTracker
from trading_assistant.scanner.market_scanner import MarketScanner
from trading_assistant.notifications.notifier import Notifier
from trading_assistant import config

db = Database(str(DATABASE_PATH))
watchlist = WatchlistManager(db, config)
price_tracker = PriceTracker(db)
scanner = MarketScanner(db)
notifier = Notifier(config)

app = create_app(db, watchlist, price_tracker, scanner, notifier)
app.state.config = config

if __name__ == "__main__":
    uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT)
