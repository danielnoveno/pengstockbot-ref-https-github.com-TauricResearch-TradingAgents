"""Centralized configuration untuk Trading Assistant."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── LLM Settings ──────────────────────────────────────────
# Default: Google Gemini (GRATIS - 15 RPM, 1500 req/hari)
LLM_PROVIDER = os.getenv("TRADING_AGENTS_LLM_PROVIDER", "google")
DEEP_THINK_LLM = os.getenv("TRADING_AGENTS_DEEP_THINK_LLM", "gemini-2.5-flash")
QUICK_THINK_LLM = os.getenv("TRADING_AGENTS_QUICK_THINK_LLM", "gemini-2.5-flash")
LLM_TEMPERATURE = float(os.getenv("TRADING_AGENTS_TEMPERATURE", "0.1"))

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# ── Market Settings ───────────────────────────────────────
# Default watchlist - pilih yang paling likuid
DEFAULT_WATCHLIST = [
    # US Blue Chips
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD",
    "SPY", "QQQ", "JPM", "V", "JNJ", "WMT",
    # Crypto
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD",
    # IDX (kalau bisa diakses)
    "BBCA.JK", "BBRI.JK", "TLKM.JK", "GOTO.JK",
]

# Extra watchlists (tambahkan manual lewat dashboard)
US_WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
CRYPTO_WATCHLIST = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"]

# ── Scanner Settings ──────────────────────────────────────
PRICE_CHECK_INTERVAL = 60          # detik (Layer 1)
SCANNER_INTERVAL = 300             # detik (Layer 2)
DEEP_ANALYSIS_INTERVAL = 1800      # detik (Layer 3, triggered)

# Alert thresholds
PRICE_CHANGE_ALERT = 3.0           # % untuk price alert
VOLUME_SPIKE_MULTIPLIER = 2.0      # x average volume
HUGE_VOLUME_MULTIPLIER = 5.0       # x average volume untuk huge alert

# ── Notification Settings ─────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")  # App password untuk Gmail
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

# ── Dashboard Settings ────────────────────────────────────
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8088"))

# ── Database Settings ─────────────────────────────────────
DATABASE_PATH = DATA_DIR / "trading_assistant.db"

# ── TradingAgents Path ────────────────────────────────────
TRADINGAGENTS_DIR = BASE_DIR / "tradingagents"
