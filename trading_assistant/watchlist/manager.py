"""Watchlist manager - kelola daftar saham/crypto yang dipantau."""

import json
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WatchlistManager:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self._load_defaults()

    def _load_defaults(self):
        """Load default watchlist ke database jika kosong."""
        existing = self.db.get_watchlist()
        if not existing:
            # Load all default tickers with auto-detected market
            for ticker in self.config.DEFAULT_WATCHLIST:
                market = self._detect_market(ticker)
                self.db.add_to_watchlist(ticker, market=market)

            logger.info("Default watchlist loaded ke database")

    def get_all(self) -> list[dict]:
        """Ambil semua watchlist."""
        return self.db.get_watchlist()

    def get_by_market(self, market: str) -> list[str]:
        """Ambil ticker berdasarkan market."""
        all_items = self.db.get_watchlist()
        return [item["ticker"] for item in all_items if item["market"] == market]

    def get_tickers(self) -> list[str]:
        """Ambil semua ticker saja."""
        return [item["ticker"] for item in self.db.get_watchlist()]

    def add(self, ticker: str, name: str = "", market: str = "AUTO") -> bool:
        """Tambah ticker ke watchlist."""
        if market == "AUTO":
            market = self._detect_market(ticker)

        self.db.add_to_watchlist(ticker, name, market)
        logger.info(f"Ditambahkan ke watchlist: {ticker} ({market})")
        return True

    def remove(self, ticker: str) -> bool:
        """Hapus ticker dari watchlist."""
        self.db.remove_from_watchlist(ticker)
        logger.info(f"Dihapus dari watchlist: {ticker}")
        return True

    def _detect_market(self, ticker: str) -> str:
        """Auto-detect market berdasarkan suffix ticker."""
        ticker = ticker.upper()
        if ticker.endswith(".JK"):
            return "IDX"
        elif ticker.endswith("-USD") or ticker.startswith("BTC") or ticker.startswith("ETH"):
            return "CRYPTO"
        elif any(ticker.endswith(s) for s in [".HK", ".T", ".L", ".NS", ".BO", ".TO", ".AX", ".SS", ".SZ"]):
            return "INTERNATIONAL"
        else:
            return "US"

    def get_stats(self) -> dict:
        """Statistic watchlist."""
        all_items = self.db.get_watchlist()
        markets = {}
        for item in all_items:
            market = item["market"]
            markets[market] = markets.get(market, 0) + 1

        return {
            "total": len(all_items),
            "by_market": markets,
        }
