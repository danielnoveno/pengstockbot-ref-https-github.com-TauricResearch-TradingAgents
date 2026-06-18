"""SQLite database untuk menyimpan data harga, alerts, dan analisis."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT '',
                market TEXT DEFAULT 'IDX',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER DEFAULT 0,
                change_pct REAL DEFAULT 0.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                data TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                decision TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                report_summary TEXT DEFAULT '',
                full_report TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS trending_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                score REAL DEFAULT 0.0,
                reason TEXT DEFAULT '',
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def add_to_watchlist(self, ticker: str, name: str = "", market: str = "IDX"):
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO watchlist (ticker, name, market) VALUES (?, ?, ?)",
                (ticker, name, market)
            )
            self.conn.commit()
        except Exception:
            pass

    def remove_from_watchlist(self, ticker: str):
        self.conn.execute("UPDATE watchlist SET is_active = 0 WHERE ticker = ?", (ticker,))
        self.conn.commit()

    def get_watchlist(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM watchlist WHERE is_active = 1"
        ).fetchall()
        return [dict(r) for r in rows]

    def save_price(self, ticker: str, price: float, volume: int = 0, change_pct: float = 0.0):
        self.conn.execute(
            "INSERT INTO price_history (ticker, price, volume, change_pct) VALUES (?, ?, ?, ?)",
            (ticker, price, volume, change_pct)
        )
        self.conn.commit()

    def get_latest_price(self, ticker: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM price_history WHERE ticker = ? ORDER BY timestamp DESC LIMIT 1",
            (ticker,)
        ).fetchone()
        return dict(row) if row else None

    def get_price_history(self, ticker: str, hours: int = 24) -> list[dict]:
        rows = self.conn.execute(
            """SELECT * FROM price_history
               WHERE ticker = ? AND timestamp > datetime('now', ?)
               ORDER BY timestamp DESC""",
            (ticker, f"-{hours} hours")
        ).fetchall()
        return [dict(r) for r in rows]

    def save_alert(self, ticker: str, alert_type: str, message: str,
                   severity: str = "info", data: dict = None):
        self.conn.execute(
            """INSERT INTO alerts (ticker, alert_type, message, severity, data)
               VALUES (?, ?, ?, ?, ?)""",
            (ticker, alert_type, message, severity, json.dumps(data or {}))
        )
        self.conn.commit()

    def get_recent_alerts(self, limit: int = 50) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def save_analysis(self, ticker: str, decision: str, confidence: float,
                      summary: str, full_report: dict = None):
        self.conn.execute(
            """INSERT INTO analysis_results
               (ticker, decision, confidence, report_summary, full_report)
               VALUES (?, ?, ?, ?, ?)""",
            (ticker, decision, confidence, summary, json.dumps(full_report or {}))
        )
        self.conn.commit()

    def get_latest_analysis(self, ticker: str) -> Optional[dict]:
        row = self.conn.execute(
            """SELECT * FROM analysis_results
               WHERE ticker = ? ORDER BY created_at DESC LIMIT 1""",
            (ticker,)
        ).fetchone()
        return dict(row) if row else None

    def save_trending(self, ticker: str, score: float, reason: str):
        self.conn.execute(
            "INSERT INTO trending_stocks (ticker, score, reason) VALUES (?, ?, ?)",
            (ticker, score, reason)
        )
        self.conn.commit()

    def get_trending(self, hours: int = 24) -> list[dict]:
        rows = self.conn.execute(
            """SELECT * FROM trending_stocks
               WHERE detected_at > datetime('now', ?)
               ORDER BY score DESC LIMIT 20""",
            (f"-{hours} hours",)
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self.conn.close()
