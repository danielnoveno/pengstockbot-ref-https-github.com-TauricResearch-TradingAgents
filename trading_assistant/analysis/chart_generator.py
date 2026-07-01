"""Chart generator - buat grafik harga & indikator teknikal."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CHART_DIR = Path(__file__).parent.parent / "data" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

plt.style.use('dark_background')
COLORS = {
    'price': '#00d4aa',
    'ma20': '#ffaa00',
    'ma50': '#ff4444',
    'volume': '#4488ff',
    'rsi': '#ff66ff',
    'macd': '#00d4aa',
    'signal': '#ffaa00',
    'hist_up': '#00ff00',
    'hist_down': '#ff0000',
    'bg': '#1a1a2e',
    'text': '#e0e0e0',
}


def _calc_indicators(close):
    """Shared RSI/MACD/SMA calculation — single source of truth for charts."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    macd_hist = macd - signal

    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    return rsi, macd, signal, macd_hist, sma20, sma50


def generate_price_chart(ticker: str, period: str = "3mo") -> str:
    """Buat grafik harga + Moving Average + Volume. Return path gambar."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return None

        is_jk = ".JK" in ticker
        price_fmt = lambda x: f"Rp{x:,.0f}" if is_jk else f"${x:,.2f}"

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), height_ratios=[3, 1],
                                        gridspec_kw={'hspace': 0.05})
        fig.patch.set_facecolor(COLORS['bg'])

        dates = hist.index
        close = hist['Close']
        volume = hist['Volume']
        _, _, _, _, sma20, sma50 = _calc_indicators(close)

        ax1.set_facecolor(COLORS['bg'])
        ax1.plot(dates, close, color=COLORS['price'], linewidth=1.5, label='Harga')
        if not sma20.isna().all():
            ax1.plot(dates, sma20, color=COLORS['ma20'], linewidth=1, label='MA20', alpha=0.8)
        if not sma50.isna().all():
            ax1.plot(dates, sma50, color=COLORS['ma50'], linewidth=1, label='MA50', alpha=0.8)
        ax1.fill_between(dates, close, close.min() * 0.99, alpha=0.1, color=COLORS['price'])
        ax1.set_title(f'{ticker} - Harga & Moving Average', color=COLORS['text'], fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left', fontsize=8)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: price_fmt(x)))
        ax1.tick_params(axis='x', labelbottom=False)
        ax1.grid(True, alpha=0.2)

        ax2.set_facecolor(COLORS['bg'])
        colors = [COLORS['hist_up'] if hist['Close'].iloc[i] >= hist['Open'].iloc[i]
                  else COLORS['hist_down'] for i in range(len(hist))]
        ax2.bar(dates, volume, color=colors, alpha=0.7, width=0.8)
        ax2.set_ylabel('Volume', color=COLORS['text'], fontsize=10)
        ax2.grid(True, alpha=0.2)

        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, fontsize=8)

        last_price = close.iloc[-1]
        ax1.annotate(
            price_fmt(last_price),
            xy=(dates[-1], last_price),
            fontsize=10, fontweight='bold', color=COLORS['price'],
            xytext=(10, 10), textcoords='offset points',
            arrowprops=dict(arrowstyle='->', color=COLORS['price']),
        )

        plt.tight_layout()
        filepath = str(CHART_DIR / f"{ticker.replace('.', '_')}_price.png")
        fig.savefig(filepath, dpi=120, bbox_inches='tight', facecolor=COLORS['bg'])
        plt.close(fig)
        logger.info(f"Chart tersimpan: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Gagal buat chart {ticker}: {e}")
        return None


def generate_indicator_chart(ticker: str, period: str = "3mo") -> str:
    """Buat grafik RSI + MACD. Return path gambar."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty or len(hist) < 30:
            return None

        close = hist['Close']
        dates = hist.index
        rsi, macd, signal, macd_hist, _, _ = _calc_indicators(close)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5), height_ratios=[1, 1],
                                        gridspec_kw={'hspace': 0.3})
        fig.patch.set_facecolor(COLORS['bg'])

        ax1.set_facecolor(COLORS['bg'])
        ax1.plot(dates, rsi, color=COLORS['rsi'], linewidth=1.5)
        ax1.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Overbought (70)')
        ax1.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Oversold (30)')
        ax1.fill_between(dates, 70, 100, alpha=0.1, color='red')
        ax1.fill_between(dates, 0, 30, alpha=0.1, color='green')
        ax1.set_title(f'{ticker} - RSI (14)', color=COLORS['text'], fontsize=12, fontweight='bold')
        ax1.set_ylim(0, 100)
        ax1.legend(loc='upper right', fontsize=8)
        ax1.tick_params(axis='x', labelbottom=False)
        ax1.grid(True, alpha=0.2)

        ax2.set_facecolor(COLORS['bg'])
        ax2.plot(dates, macd, color=COLORS['macd'], linewidth=1.2, label='MACD')
        ax2.plot(dates, signal, color=COLORS['signal'], linewidth=1.2, label='Signal')
        colors_hist = [COLORS['hist_up'] if v >= 0 else COLORS['hist_down'] for v in macd_hist]
        ax2.bar(dates, macd_hist, color=colors_hist, alpha=0.5, width=0.8)
        ax2.axhline(y=0, color='white', linewidth=0.5, alpha=0.3)
        ax2.set_title(f'{ticker} - MACD', color=COLORS['text'], fontsize=12, fontweight='bold')
        ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.2)

        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, fontsize=8)

        plt.tight_layout()
        filepath = str(CHART_DIR / f"{ticker.replace('.', '_')}_indicators.png")
        fig.savefig(filepath, dpi=120, bbox_inches='tight', facecolor=COLORS['bg'])
        plt.close(fig)
        logger.info(f"Indicator chart tersimpan: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Gagal buat indicator chart {ticker}: {e}")
        return None


def generate_full_chart(ticker: str, period: str = "3mo") -> str:
    """Buat grafik lengkap: Harga + RSI + MACD. Return path gambar."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty or len(hist) < 30:
            return None

        is_jk = ".JK" in ticker
        price_fmt = lambda x: f"Rp{x:,.0f}" if is_jk else f"${x:,.2f}"

        close = hist['Close']
        volume = hist['Volume']
        dates = hist.index
        rsi, macd, signal_line, macd_hist, sma20, sma50 = _calc_indicators(close)

        fig, axes = plt.subplots(4, 1, figsize=(10, 10),
                                  height_ratios=[3, 1, 1, 1],
                                  gridspec_kw={'hspace': 0.15})
        fig.patch.set_facecolor(COLORS['bg'])

        ax = axes[0]
        ax.set_facecolor(COLORS['bg'])
        ax.plot(dates, close, color=COLORS['price'], linewidth=1.5, label='Harga')
        ax.plot(dates, sma20, color=COLORS['ma20'], linewidth=1, label='MA20', alpha=0.8)
        ax.plot(dates, sma50, color=COLORS['ma50'], linewidth=1, label='MA50', alpha=0.8)
        ax.fill_between(dates, close, close.min() * 0.99, alpha=0.1, color=COLORS['price'])
        ax.set_title(f'{ticker} - Analisis Teknikal Lengkap', color=COLORS['text'], fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', fontsize=8)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: price_fmt(x)))
        ax.tick_params(axis='x', labelbottom=False)
        ax.grid(True, alpha=0.2)

        last_price = close.iloc[-1]
        ax.annotate(
            price_fmt(last_price),
            xy=(dates[-1], last_price),
            fontsize=10, fontweight='bold', color=COLORS['price'],
            xytext=(10, 10), textcoords='offset points',
            arrowprops=dict(arrowstyle='->', color=COLORS['price']),
        )

        ax = axes[1]
        ax.set_facecolor(COLORS['bg'])
        colors_vol = [COLORS['hist_up'] if hist['Close'].iloc[i] >= hist['Open'].iloc[i]
                      else COLORS['hist_down'] for i in range(len(hist))]
        ax.bar(dates, volume, color=colors_vol, alpha=0.6, width=0.8)
        ax.set_ylabel('Volume', color=COLORS['text'], fontsize=9)
        ax.tick_params(axis='x', labelbottom=False)
        ax.grid(True, alpha=0.2)

        ax = axes[2]
        ax.set_facecolor(COLORS['bg'])
        ax.plot(dates, rsi, color=COLORS['rsi'], linewidth=1.2)
        ax.axhline(y=70, color='red', linestyle='--', alpha=0.4)
        ax.axhline(y=30, color='green', linestyle='--', alpha=0.4)
        ax.fill_between(dates, 70, 100, alpha=0.1, color='red')
        ax.fill_between(dates, 0, 30, alpha=0.1, color='green')
        ax.set_ylabel('RSI', color=COLORS['text'], fontsize=9)
        ax.set_ylim(0, 100)
        ax.tick_params(axis='x', labelbottom=False)
        ax.grid(True, alpha=0.2)

        ax = axes[3]
        ax.set_facecolor(COLORS['bg'])
        ax.plot(dates, macd, color=COLORS['macd'], linewidth=1, label='MACD')
        ax.plot(dates, signal_line, color=COLORS['signal'], linewidth=1, label='Signal')
        colors_hist = [COLORS['hist_up'] if v >= 0 else COLORS['hist_down'] for v in macd_hist]
        ax.bar(dates, macd_hist, color=colors_hist, alpha=0.4, width=0.8)
        ax.axhline(y=0, color='white', linewidth=0.5, alpha=0.3)
        ax.set_ylabel('MACD', color=COLORS['text'], fontsize=9)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.2)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, fontsize=8)

        plt.tight_layout()
        filepath = str(CHART_DIR / f"{ticker.replace('.', '_')}_full.png")
        fig.savefig(filepath, dpi=120, bbox_inches='tight', facecolor=COLORS['bg'])
        plt.close(fig)
        logger.info(f"Full chart tersimpan: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Gagal buat full chart {ticker}: {e}")
        return None
