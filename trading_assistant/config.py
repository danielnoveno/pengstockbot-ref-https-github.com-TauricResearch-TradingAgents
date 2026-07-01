"""Centralized configuration - ALL values from env vars with sensible defaults."""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── LLM Settings ──────────────────────────────────────────
LLM_PROVIDER = os.getenv("TRADING_AGENTS_LLM_PROVIDER", "google")  # google | openrouter | groq | nvidia | aimlapi
DEEP_THINK_LLM = os.getenv("TRADING_AGENTS_DEEP_THINK_LLM", "gemini-2.5-flash")
QUICK_THINK_LLM = os.getenv("TRADING_AGENTS_QUICK_THINK_LLM", "gemini-2.5-flash")
LLM_TEMPERATURE = float(os.getenv("TRADING_AGENTS_TEMPERATURE", "0.1"))
OUTPUT_LANGUAGE = os.getenv("OUTPUT_LANGUAGE", "Bahasa Indonesia")

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
AIML_API_KEY = os.getenv("AIML_API_KEY", "")
BYNARA_API_KEY = os.getenv("BYNARA_API_KEY", "")
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# ── Market Settings ───────────────────────────────────────
# Load from env or JSON file, fallback to defaults
def _load_watchlist():
    """Load watchlist from WATCHLIST_FILE env or JSON."""
    watchlist_file = os.getenv("WATCHLIST_FILE", "")
    if watchlist_file and Path(watchlist_file).exists():
        with open(watchlist_file) as f:
            return json.load(f)
    
    env_watchlist = os.getenv("WATCHLIST", "")
    if env_watchlist:
        return [t.strip().upper() for t in env_watchlist.split(",")]
    
    return [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD",
        "SPY", "QQQ", "JPM", "V", "JNJ", "WMT",
        "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD",
        "BBCA.JK", "BBRI.JK", "TLKM.JK", "GOTO.JK",
    ]

DEFAULT_WATCHLIST = _load_watchlist()

# ── Market Indices (single source of truth) ────────────────
MARKET_INDICES = {
    "S&P 500": os.getenv("IDX_SP500", "^GSPC"),
    "NASDAQ": os.getenv("IDX_NASDAQ", "^IXIC"),
    "Dow Jones": os.getenv("IDX_DOW", "^DJI"),
    "IHSG": os.getenv("IDX_IHSG", "^JKSE"),
    "Nikkei": os.getenv("IDX_NIKKEI", "^N225"),
    "Hang Seng": os.getenv("IDX_HANGSENG", "^HSI"),
    "BTC": os.getenv("IDX_BTC", "BTC-USD"),
    "ETH": os.getenv("IDX_ETH", "ETH-USD"),
}

# ── Scanner Settings (from env) ───────────────────────────
PRICE_CHECK_INTERVAL = int(os.getenv("PRICE_CHECK_INTERVAL", "60"))
SCANNER_INTERVAL = int(os.getenv("SCANNER_INTERVAL", "300"))
DEEP_ANALYSIS_INTERVAL = int(os.getenv("DEEP_ANALYSIS_INTERVAL", "1800"))

# Alert thresholds (from env)
PRICE_CHANGE_ALERT = float(os.getenv("PRICE_CHANGE_ALERT", "3.0"))
PRICE_CRITICAL_ALERT = float(os.getenv("PRICE_CRITICAL_ALERT", "5.0"))
VOLUME_SPIKE_MULTIPLIER = float(os.getenv("VOLUME_SPIKE_MULTIPLIER", "2.0"))
HUGE_VOLUME_MULTIPLIER = float(os.getenv("HUGE_VOLUME_MULTIPLIER", "5.0"))

# Limits (from env)
MAX_TICKERS_SCAN = int(os.getenv("MAX_TICKERS_SCAN", "30"))
MAX_NEWS_ITEMS = int(os.getenv("MAX_NEWS_ITEMS", "5"))
MAX_ALERTS_DISPLAY = int(os.getenv("MAX_ALERTS_DISPLAY", "20"))
MAX_TRENDING_DISPLAY = int(os.getenv("MAX_TRENDING_DISPLAY", "10"))

# Schedule times (from env)
MORNING_BRIEFING_TIME = os.getenv("MORNING_BRIEFING_TIME", "07:30")
EVENING_SUMMARY_TIME = os.getenv("EVENING_SUMMARY_TIME", "16:30")

# Data periods (from env)
DATA_PERIOD_SHORT = os.getenv("DATA_PERIOD_SHORT", "2d")
DATA_PERIOD_MEDIUM = os.getenv("DATA_PERIOD_MEDIUM", "1mo")
DATA_PERIOD_LONG = os.getenv("DATA_PERIOD_LONG", "3mo")

# ── Notification Settings ─────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

# ── Dashboard Settings ────────────────────────────────────
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8088"))
DASHBOARD_REFRESH_INTERVAL = int(os.getenv("DASHBOARD_REFRESH_INTERVAL", "15"))

# ── Database Settings ─────────────────────────────────────
DATABASE_PATH = DATA_DIR / os.getenv("DATABASE_NAME", "trading_assistant.db")

# ── TradingAgents Path ────────────────────────────────────
TRADINGAGENTS_DIR = BASE_DIR / "tradingagents"
