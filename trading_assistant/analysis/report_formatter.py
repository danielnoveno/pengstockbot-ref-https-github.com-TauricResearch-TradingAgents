"""Report formatter - format laporan analisis lengkap & bahasa sederhana untuk pemula."""

from datetime import datetime


class ReportFormatter:

    # ── Helper: RSI Explanation ────────────────────────────
    @staticmethod
    def _explain_rsi(rsi: float) -> str:
        """Jelaskan RSI dalam bahasa sederhana."""
        if rsi is None:
            return ""
        if rsi < 30:
            return f"RSI {rsi:.0f} = SAHAM MURAH (oversold) → potensi naik, tapi hati-hati bisa turun lagi"
        elif rsi < 40:
            return f"RSI {rsi:.0f} = mulai murah → bisa mulai lihat-lihat"
        elif rsi < 60:
            return f"RSI {rsi:.0f} = NORMAL → harga wajar, tidak terlalu mahal atau murah"
        elif rsi < 70:
            return f"RSI {rsi:.0f} = mulai mahal → hati-hati, bisa turun"
        else:
            return f"RSI {rsi:.0f} = SANGAT MAHAL (overbought) → sering turun setelah ini"

    # ── Helper: MACD Explanation ───────────────────────────
    @staticmethod
    def _explain_macd(macd: float, signal: float, hist: float) -> str:
        """Jelaskan MACD dalam bahasa sederhana."""
        if macd is None or signal is None:
            return ""
        if hist > 0:
            return f"MACD = garis biru di atas gari kuning → tren sedang NAIK"
        else:
            return f"MACD = garis biru di bawah garis kuning → tren sedang TURUN"

    # ── Helper: Trend Explanation ──────────────────────────
    @staticmethod
    def _explain_trend(above_sma20, above_sma50) -> str:
        """Jelaskan trend dalam bahasa sederhana."""
        if above_sma20 and above_sma50:
            return "Harga di atas MA20 & MA50 → SAHAM SEDANG NAIK (uptrend)"
        elif not above_sma20 and not above_sma50:
            return "Harga di bawah MA20 & MA50 → SAHAM SEDANG TURUN (downtrend)"
        elif above_sma20 and not above_sma50:
            return "Harga di atas MA20 tapi bawah MA50 → mulai pulih, tapi belum pasti"
        else:
            return "Harga di bawah MA20 tapi atas MA50 → hati-hati, bisa koreksi"

    # ── Helper: Volume Explanation ─────────────────────────
    @staticmethod
    def _explain_volume(ratio: float) -> str:
        """Jelaskan volume dalam bahasa sederhana."""
        if ratio >= 5:
            return f"Volume {ratio:.1f}x lipat dari biasanya → BEGITU BANYAK orang beli/jual! Ini peristiwa besar."
        elif ratio >= 3:
            return f"Volume {ratio:.1f}x lipat → banyak yang mulai beli/jual, perhatikan!"
        elif ratio >= 2:
            return f"Volume {ratio:.1f}x lipat → ada ketertarikan lebih dari biasanya"
        elif ratio >= 1.5:
            return f"Volume {ratio:.1f}x lipat → sedikit lebih aktif dari biasanya"
        else:
            return f"Volume normal, tidak ada yang aneh"

    # ── Helper: Simple verdict ─────────────────────────────
    @staticmethod
    def _simple_verdict(rsi, macd_bullish, above_sma20, above_sma50, volume_ratio=None) -> str:
        """Buat verdict sederhana untuk pemula."""
        score = 0
        reasons = []

        if rsi is not None:
            if rsi < 30:
                score += 2
                reasons.append("RSI oversold (saham murah)")
            elif rsi < 50:
                score += 1
                reasons.append("RSI mendekati murah")
            elif rsi > 70:
                score -= 2
                reasons.append("RSI overbought (saham mahal)")
            elif rsi > 50:
                score -= 1
                reasons.append("RSI mendekati mahal")

        if macd_bullish:
            score += 1
            reasons.append("MACD bullish (tren naik)")
        else:
            score -= 1
            reasons.append("MACD bearish (tren turun)")

        if above_sma20 and above_sma50:
            score += 1
            reasons.append("Uptrend")
        elif not above_sma20 and not above_sma50:
            score -= 1
            reasons.append("Downtrend")

        if volume_ratio and volume_ratio >= 2:
            if score > 0:
                score += 1
                reasons.append(f"Volume tinggi ({volume_ratio:.1f}x) menguatkan sinyal")
            else:
                reasons.append(f"Volume tinggi ({volume_ratio:.1f}x) tapi tren sedang turun")

        if score >= 2:
            action = "🟢 POTENSI BELI"
            why = "Beberapa indikator menunjukkan saham ini sedang murah dan tren mulai naik."
        elif score <= -2:
            action = "🔴 HATI-HATI / POTENSI JUAL"
            why = "Beberapa indikator menunjukkan saham ini mahal dan tren sedang turun."
        elif score > 0:
            action = "🟡 COCEK LAGI"
            why = "Ada tanda positif tapi belum cukup kuat. Perlu lihat berita dan faktor lain."
        elif score < 0:
            action = "🟡 WASPADA"
            why = "Ada tanda negatif tapi belum parah. Pantau terus."
        else:
            action = "⚪ NETRAL"
            why = "Tidak ada sinyal kuat. Harga sedang stabil."

        return f"{action}\n\n{why}\n\nAlasan:\n" + "\n".join(f"  - {r}" for r in reasons)

    # ══════════════════════════════════════════════════════
    #  MAIN FORMATTERS
    # ══════════════════════════════════════════════════════

    @staticmethod
    def format_news(news) -> str:
        """Format berita dengan link yang bisa diklik."""
        if not news:
            return "  Tidak ada berita terbaru."

        # Support both string and list of dicts
        if isinstance(news, str):
            return news

        lines = []
        for n in news[:5]:
            title = n.get("title", "")
            publisher = n.get("publisher", "")
            url = n.get("url", "")
            if title:
                if url:
                    lines.append(f"  {title}")
                    lines.append(f"    Baca: {url}")
                else:
                    lines.append(f"  {title}")
                if publisher:
                    lines.append(f"    Sumber: {publisher}")
        return "\n".join(lines) if lines else "  Tidak ada berita terbaru."

    @staticmethod
    def format_price_alert(alert: dict, news=None, indicators: dict = None) -> str:
        """Format price alert LENGKAP dengan penjelasan."""
        ticker = alert["ticker"]
        data = alert.get("data", {})
        change = data.get("change_pct", 0)
        price = data.get("price", 0)

        is_jk = ".JK" in ticker
        price_str = f"Rp{price:,.0f}" if is_jk else f"${price:,.2f}"
        icon = "🟢" if change > 0 else "🔴"
        direction = "NAIK" if change > 0 else "TURUN"

        lines = [
            f"{icon} **ALERT: {ticker} {direction} {abs(change):.2f}%**",
            "━" * 35,
            f"💰 Harga sekarang: {price_str}",
            f"📊 Perubahan: {direction} {abs(change):.2f}% dari kemarin",
            "",
        ]

        # Penjelasan sederhana
        if abs(change) >= 5:
            lines.append("⚠️ **INI PERUBAHAN BESAR!**")
            lines.append(f"Saham ini {'naik' if change > 0 else 'turun'} sangat signifikan hari ini.")
            lines.append("Ini bisa karena berita besar atau aksi korporat.")
            lines.append("")
        elif abs(change) >= 3:
            lines.append(f"📋 **Perubahan cukup signifikan.** Saham ini bergerak lebih dari biasanya.")
            lines.append("")

        # Technical indicators
        if indicators:
            rsi = indicators.get("rsi")
            macd_bullish = indicators.get("macd_bullish")
            above_sma20 = indicators.get("above_sma20")
            above_sma50 = indicators.get("above_sma50")
            sma20 = indicators.get("sma20")
            sma50 = indicators.get("sma50")

            lines.append("📈 **Indikator Teknikal:**")
            if rsi is not None:
                lines.append(f"  • {ReportFormatter._explain_rsi(rsi)}")
            if macd_bullish is not None:
                lines.append(f"  • {ReportFormatter._explain_macd(None, None, 1 if macd_bullish else -1)}")
            if above_sma20 is not None and sma20:
                lines.append(f"  • MA20: {'di atas' if above_sma20 else 'di bawah'} ({sma20:,.0f})" if is_jk else f"  • MA20: {'di atas' if above_sma20 else 'di bawah'} (${sma20:,.2f})")
            if above_sma50 is not None and sma50:
                lines.append(f"  • MA50: {'di atas' if above_sma50 else 'di bawah'} ({sma50:,.0f})" if is_jk else f"  • MA50: {'di atas' if above_sma50 else 'di bawah'} (${sma50:,.2f})")

            # Verdict
            lines.append("")
            verdict = ReportFormatter._simple_verdict(rsi, macd_bullish, above_sma20, above_sma50)
            lines.append(f"🎯 **Verdict Sederhana:**")
            lines.append(verdict)
            lines.append("")

        # News
        if news:
            lines.append("📰 **Berita Terkait (klik link untuk baca):**")
            lines.append(ReportFormatter.format_news(news))
            lines.append("")

        lines.append("💡 **Ingat:** Ini bukan saran beli/jual. Kamu yang putuskan!")
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)

    @staticmethod
    def format_volume_alert(ticker: str, ratio: float, volume: int, avg_vol: int, price: float, news: str = "") -> str:
        """Format volume alert LENGKAP."""
        is_jk = ".JK" in ticker
        price_str = f"Rp{price:,.0f}" if is_jk else f"${price:,.2f}"

        lines = [
            f"📊 **VOLUME SPIKE: {ticker}**",
            "━" * 35,
            f"💰 Harga: {price_str}",
            f"📊 Volume hari ini: {volume:,}",
            f"📊 Volume biasa: {avg_vol:,}",
            f"📊 Ratio: {ratio:.1f}x lipat dari biasanya",
            "",
            "💡 **Apa artinya?**",
            ReportFormatter._explain_volume(ratio),
            "",
        ]

        if ratio >= 3:
            lines.append("⚠️ **Kemungkinan penyebab:**")
            lines.append("  - Berita besar tentang perusahaan ini")
            lines.append("  - Aksi beli/jual besar dari institusi")
            lines.append("  - Rumor atau pengumuman penting")
            lines.append("")
            lines.append("💡 **Saran:** Cek berita terbaru tentang saham ini sebelum putuskan!")

        if news:
            lines.append("📰 **Berita Terkait (klik link untuk baca):**")
            lines.append(ReportFormatter.format_news(news))

        lines.append(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        return "\n".join(lines)

    @staticmethod
    def format_full_analysis(ticker: str, indicators: dict, news, sentiment: str, hot_info: str = "") -> str:
        """Format analisis LENGKAP untuk satu saham - semua ada di satu pesan."""
        is_jk = ".JK" in ticker

        # Company name mapping (sederhana)
        company_names = {
            "BBCA.JK": "Bank Central Asia (BCA)",
            "BBRI.JK": "Bank Rakyat Indonesia (BRI)",
            "BMRI.JK": "Bank Mandiri",
            "TLKM.JK": "Telkom Indonesia",
            "ASII.JK": "Astra International",
            "UNVR.JK": "Unilever Indonesia",
            "GOTO.JK": "GoTo Gojek Tokopedia",
            "BREN.JK": "Barito Renewables",
            "ICBP.JK": "Indofood CBP",
            "ADRO.JK": "Adaro Energy",
        }
        company_name = company_names.get(ticker, ticker.replace(".JK", ""))

        lines = [
            f"📋 **ANALISIS LENGKAP: {ticker}**",
            f"📍 {company_name}",
            "━" * 35,
            "",
        ]

        # Price info
        if indicators:
            price = indicators.get("price", 0)
            rsi = indicators.get("rsi")
            macd_bullish = indicators.get("macd_bullish")
            above_sma20 = indicators.get("above_sma20")
            above_sma50 = indicators.get("above_sma50")
            sma20 = indicators.get("sma20")
            sma50 = indicators.get("sma50")

            price_str = f"Rp{price:,.0f}" if is_jk else f"${price:,.2f}"
            lines.append(f"💰 **Harga:** {price_str}")
            lines.append("")

            # Technical analysis section
            lines.append("📈 **ANALISIS TEKNIKAL:**")
            lines.append("(Grafik & angka-angka yang menunjukkan pola harga)")
            lines.append("")

            if rsi is not None:
                lines.append(f"📌 **RSI (Kekuatan Harga):** {rsi:.0f}")
                lines.append(f"   → {ReportFormatter._explain_rsi(rsi)}")
                lines.append("")

            if macd_bullish is not None:
                lines.append(f"📌 **MACD (Arah Trend):**")
                lines.append(f"   → {ReportFormatter._explain_macd(None, None, 1 if macd_bullish else -1)}")
                lines.append("")

            if sma20:
                pos20 = "DI ATAS" if above_sma20 else "DI BAWAH"
                lines.append(f"📌 **MA20 (Tren Pendek):** {pos20} ({'Rp{:,.0f}'.format(sma20) if is_jk else '${:,.2f}'.format(sma20)})")
            if sma50:
                pos50 = "DI ATAS" if above_sma50 else "DI BAWAH"
                lines.append(f"📌 **MA50 (Tren Panjang):** {pos50} ({'Rp{:,.0f}'.format(sma50) if is_jk else '${:,.2f}'.format(sma50)})")
            if sma20 and sma50:
                lines.append(f"   → {ReportFormatter._explain_trend(above_sma20, above_sma50)}")
            lines.append("")

            # Simple verdict
            lines.append("🎯 **KESIMPULAN SEDERHANA:**")
            verdict = ReportFormatter._simple_verdict(rsi, macd_bullish, above_sma20, above_sma50)
            lines.append(verdict)
            lines.append("")

        # News section
        lines.append("📰 **BERITA YANG MEMPENGARUHI HARGA (klik link untuk baca):**")
        if news:
            lines.append(ReportFormatter.format_news(news))
        else:
            lines.append("  Tidak ada berita signifikan saat ini.")
        lines.append("")

        # Sentiment section
        lines.append("😊 **SENTIMEN PASAR:**")
        if sentiment:
            lines.append(f"  {sentiment}")
        else:
            lines.append("  Netral - tidak ada sentimen kuat.")
        lines.append("")

        # Hot info
        if hot_info:
            lines.append("🔥 **INFO HOT:**")
            lines.append(f"  {hot_info}")
            lines.append("")

        # Educational note
        lines.append("📚 **CATATAN UNTUK PEMULA:**")
        lines.append("  - RSI < 30 = murah (oversold), RSI > 70 = mahal (overbought)")
        lines.append("  - MACD naik = tren sedang naik, MACD turun = tren sedang turun")
        lines.append("  - Volume tinggi = banyak orang tertarik, bisa bagus atau waspada")
        lines.append("  - Selalu cek berita! Berita bisa mengubah harga dengan cepat")
        lines.append("")
        lines.append("⚠️ **PENTING:** Ini bukan saran beli/jual! Kamu yang putuskan.")
        lines.append("   Lakukan riset sendiri atau konsultasi dengan ahli.")
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        return "\n".join(lines)

    @staticmethod
    def format_trending_report(trending: list[dict]) -> str:
        """Format trending stocks dengan penjelasan lengkap."""
        if not trending:
            return "📊 Tidak ada saham trending saat ini."

        lines = [
            "🔥 **SAHAM YANG LAGI RAMAI DIPERBINCANGKAN**",
            "━" * 35,
            "(Saham-saham yang pergerakannya paling menarik perhatian hari ini)",
            ""
        ]

        for i, t in enumerate(trending[:8], 1):
            ticker = t.get("ticker", "")
            is_jk = ".JK" in ticker
            score = t.get("score", 0)
            reasons = t.get("reasons", [])
            indicators = t.get("indicators", {})
            price = indicators.get("price", 0)
            rsi = indicators.get("rsi")

            price_str = f"Rp{price:,.0f}" if is_jk else f"${price:,.2f}"

            lines.append(f"**{i}. {ticker}** - {price_str}")

            # Signal strength
            if score >= 4:
                lines.append(f"   ⭐⭐⭐ SINYAL KUAT ({score} poin)")
            elif score >= 2:
                lines.append(f"   ⭐⭐ SINYAL SEDANG ({score} poin)")
            else:
                lines.append(f"   ⭐ SINYAL RINGAN ({score} poin)")

            # Reasons explained
            for reason in reasons:
                if "RSI" in reason:
                    rsi_val = float(reason.split("(")[1].split(")")[0])
                    lines.append(f"   → {ReportFormatter._explain_rsi(rsi_val)}")
                elif "MACD" in reason.lower():
                    lines.append(f"   → {reason} = tren sedang bergerak ke arah tersebut")
                elif "Volume" in reason:
                    lines.append(f"   → {reason} = banyak yang beli/jual")
                else:
                    lines.append(f"   → {reason}")
            lines.append("")

        lines.append("💡 **Tips:** Sinyal kuat belum tentu bagus untuk beli sekarang.")
        lines.append("   Cek berita dan kondisi market dulu!")
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)

    @staticmethod
    def format_market_overview(overview: dict) -> str:
        """Format market overview dengan penjelasan."""
        lines = [
            "🌍 **KONDISI PASAR HARI INI**",
            "━" * 35,
            ""
        ]

        for name, data in overview.items():
            icon = data.get("status", "")
            change = data.get("change_pct", 0)
            price = data.get("price", 0)

            status = "NAIK" if change > 0 else "TURUN" if change < 0 else "STABIL"
            lines.append(f"{icon} **{name}**: {change:+.2f}% ({status})")

            # Penjelasan untuk pemula
            if name == "IHSG":
                if change > 1:
                    lines.append("   → Pasar saham Indonesia sedang BAGUS hari ini!")
                elif change < -1:
                    lines.append("   → Pasar saham Indonesia sedang LESU hari ini.")
                else:
                    lines.append("   → Pasar saham Indonesia stabil hari ini.")
            elif name == "S&P 500" or name == "NASDAQ":
                if change > 1:
                    lines.append("   → Pasar saham AS sedang bagus, biasanya bikin pasar Asia ikut naik.")
                elif change < -1:
                    lines.append("   → Pasar saham AS turun, bisa mempengaruhi pasar Asia.")
            elif name == "BTC":
                if change > 3:
                    lines.append("   → Bitcoin naik signifikan! Crypto market sedang aktif.")
                elif change < -3:
                    lines.append("   → Bitcoin turun signifikan. Hati-hati di crypto market.")
            lines.append("")

        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)

    @staticmethod
    def format_morning_briefing(overview: dict, trending: list[dict], watchlist_summary: str) -> str:
        """Format morning briefing - ringkasan pagi untuk pemula."""
        lines = [
            "☀️ **SELAMAT PAGI! BRIEFING PAGI HARI INI**",
            "━" * 35,
            "",
            "📋 Apa yang terjadi di pasar:",
            "",
        ]

        # Market overview
        for name, data in overview.items():
            icon = data.get("status", "")
            change = data.get("change_pct", 0)
            status = "NAIK" if change > 0 else "TURUN" if change < 0 else "STABIL"
            lines.append(f"  {icon} {name}: {change:+.2f}% ({status})")

        lines.append("")

        # Hot stocks
        if trending:
            lines.append("🔥 **Saham yang lagi ramai:**")
            for t in trending[:5]:
                ticker = t.get("ticker", "")
                price = t.get("indicators", {}).get("price", 0)
                reasons = t.get("reasons", [])
                is_jk = ".JK" in ticker
                price_str = f"Rp{price:,.0f}" if is_jk else f"${price:,.2f}"
                lines.append(f"  • {ticker} ({price_str}): {', '.join(reasons[:2])}")
            lines.append("")

        # Watchlist summary
        if watchlist_summary:
            lines.append("📊 **Watchlist kamu:**")
            lines.append(watchlist_summary)
            lines.append("")

        lines.append("💡 **Tips hari ini:**")
        lines.append("  - Cek berita dulu sebelum putuskan beli/jual")
        lines.append("  - Jangan beli karena FOMO (takut ketinggalan)")
        lines.append("  - Tentukan target harga dan stop loss sebelum beli")
        lines.append("")
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)

    @staticmethod
    def format_evening_summary(prices: dict, alerts: list, analysis: list) -> str:
        """Format evening summary - ringkasan sore/malam."""
        lines = [
            "🌙 **RINGKASAN HARI INI**",
            "━" * 35,
            "",
        ]

        # Top movers
        if prices:
            sorted_prices = sorted(
                prices.values(),
                key=lambda x: abs(x.get("change_pct", 0)),
                reverse=True
            )

            lines.append("📈 **Top Movers (Perubahan Terbesar):**")
            for p in sorted_prices[:7]:
                icon = "🟢" if p["change_pct"] > 0 else "🔴"
                is_jk = ".JK" in p.get("ticker", "")
                price_str = f"Rp{p.get('price', 0):,.0f}" if is_jk else f"${p.get('price', 0):,.2f}"
                lines.append(f"  {icon} {p['ticker']}: {p['change_pct']:+.2f}% ({price_str})")
            lines.append("")

        # Today's alerts
        if alerts:
            lines.append(f"🚨 **Alert hari ini:** ({len(alerts)} alert)")
            for a in alerts[:5]:
                lines.append(f"  • {a.get('message', '')[:80]}")
            lines.append("")

        # Analysis summary
        if analysis:
            lines.append(f"🤖 **Analisis AI hari ini:** ({len(analysis)} saham)")
            for a in analysis:
                decision = a.get("decision", "N/A")
                icon = "🟢" if "BUY" in decision else "🔴" if "SELL" in decision else "🟡"
                lines.append(f"  {icon} {a.get('ticker', '')}: {decision}")
            lines.append("")

        # Lessons
        lines.append("📝 **Pelajaran hari ini:**")
        gainers = [p for p in prices.values() if p.get("change_pct", 0) > 2]
        losers = [p for p in prices.values() if p.get("change_pct", 0) < -2]
        if gainers:
            names = [g["ticker"] for g in gainers[:3]]
            lines.append(f"  • Yang naik banyak: {', '.join(names)} - cek kenapa mereka naik!")
        if losers:
            names = [l["ticker"] for l in losers[:3]]
            lines.append(f"  • Yang turun banyak: {', '.join(names)} - cek kenapa mereka turun!")
        if not gainers and not losers:
            lines.append("  • Hari ini pasar relatif stabil, tidak ada pergerakan ekstrem.")

        lines.append("")
        lines.append("💡 **Tips:** Tidur yang cukup, besok ada sesi trading baru!")
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)
