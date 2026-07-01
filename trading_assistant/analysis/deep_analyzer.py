"""Layer 3: Deep analysis menggunakan TradingAgents framework."""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DeepAnalyzer:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self._graph = None

    def _get_graph(self):
        """Lazy init TradingAgentsGraph."""
        if self._graph is not None:
            return self._graph

        try:
            tradingagents_dir = self.config.TRADINGAGENTS_DIR
            if str(tradingagents_dir) not in sys.path:
                sys.path.insert(0, str(tradingagents_dir))

            from tradingagents.graph.trading_graph import TradingAgentsGraph
            from tradingagents.default_config import DEFAULT_CONFIG

            ta_config = DEFAULT_CONFIG.copy()
            ta_config["llm_provider"] = self.config.LLM_PROVIDER
            ta_config["deep_think_llm"] = self.config.DEEP_THINK_LLM
            ta_config["quick_think_llm"] = self.config.QUICK_THINK_LLM
            if self.config.LLM_TEMPERATURE is not None:
                ta_config["temperature"] = self.config.LLM_TEMPERATURE
            ta_config["output_language"] = self.config.OUTPUT_LANGUAGE

            self._graph = TradingAgentsGraph(
                debug=False,
                config=ta_config,
            )
            logger.info(f"TradingAgents initialized dengan provider: {self.config.LLM_PROVIDER}")
            return self._graph

        except Exception as e:
            logger.error(f"Gagal init TradingAgents: {e}")
            return None

    def analyze(self, ticker: str, date: str = None) -> Optional[dict]:
        """Jalankan analisis mendalam menggunakan TradingAgents."""
        graph = self._get_graph()
        if graph is None:
            return None

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            logger.info(f"Mulai deep analysis: {ticker} pada {date}")
            final_state, decision = graph.propagate(ticker, date)

            # Extract report summary
            summary = self._extract_summary(final_state)

            # Save to database
            self.db.save_analysis(
                ticker=ticker,
                decision=decision,
                confidence=0.0,
                summary=summary,
                full_report=final_state if isinstance(final_state, dict) else {}
            )

            result = {
                "ticker": ticker,
                "date": date,
                "decision": decision,
                "summary": summary,
                "state": final_state,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Analisis selesai: {ticker} -> {decision}")
            return result

        except Exception as e:
            logger.error(f"Gagal analisis {ticker}: {e}")
            return None

    def _extract_summary(self, state) -> str:
        """Extract ringkasan dari hasil analisis."""
        if not state or not isinstance(state, dict):
            return "Tidak ada ringkasan tersedia."

        parts = []

        if "market_report" in state and state["market_report"]:
            parts.append(f"**Market:** {str(state['market_report'])[:200]}")

        if "sentiment_report" in state and state["sentiment_report"]:
            parts.append(f"**Sentimen:** {str(state['sentiment_report'])[:200]}")

        if "news_report" in state and state["news_report"]:
            parts.append(f"**Berita:** {str(state['news_report'])[:200]}")

        if "fundamentals_report" in state and state["fundamentals_report"]:
            parts.append(f"**Fundamental:** {str(state['fundamentals_report'])[:200]}")

        if "investment_plan" in state and state["investment_plan"]:
            parts.append(f"**Plan:** {str(state['investment_plan'])[:200]}")

        if "final_trade_decision" in state and state["final_trade_decision"]:
            parts.append(f"**Decision:** {str(state['final_trade_decision'])[:300]}")

        return "\n\n".join(parts) if parts else "Ringkasan tidak tersedia."

    def quick_sentiment(self, ticker: str) -> str:
        """Quick sentiment check tanpa full TradingAgents analysis."""
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            news = stock.news

            if not news:
                return "Tidak ada berita terbaru."

            headlines = []
            for n in news[:5]:
                title = n.get("title", "")
                if title:
                    headlines.append(f"• {title}")

            return "\n".join(headlines)

        except Exception as e:
            return f"Gagal ambil berita: {e}"
