"""News engine — sentiment + summarizer + topic extraction. Zero AI cost."""

import re
from collections import Counter
from math import log


# ── Sentiment Keywords ────────────────────────────────────
POSITIVE = {
    "surge", "rally", "profit", "growth", "gain", "rise", "jump", "soar",
    "upgrade", "bullish", "boom", "record", "high", "strong", "buy",
    "recovery", "rebound", "breakout", "optimistic", "positive", "beat",
    "exceed", "outperform", "upgrade", "innovation", "partnership",
    "revenue", "dividend", "expansion", "milestone", "success",
}

NEGATIVE = {
    "crash", "fall", "drop", "decline", "loss", "down", "sell", "bearish",
    "plunge", "slump", "crisis", "fail", "bankrupt", "debt", "risk",
    "downgrade", "recession", "inflation", "warning", "layoff", "cut",
    "lawsuit", "fraud", "scandal", "collapse", "default", "miss",
    "disappoint", "weak", "negative", "fear", "panic", "correction",
}

IMPACT_WORDS = {
    "fed", "interest", "rate", "inflation", "gdp", "earnings", "revenue",
    "profit", "merger", "acquisition", "ipo", "ban", "tariff", "trade",
    "war", "sanction", "oil", "gold", "bitcoin", "crypto", "regulation",
    "stimulus", "quantitative", "easing", "deficit", "debt", "bond",
    "yield", "dividend", "split", "buyback", "guidance", "forecast",
}

SECTOR_KEYWORDS = {
    "tech": ["apple", "google", "microsoft", "nvidia", "meta", "amazon", "ai", "chip", "semiconductor"],
    "crypto": ["bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain", "defi", "token"],
    "finance": ["bank", "jpmorgan", "goldman", "morgan", "hsbc", "interest", "rate", "bond", "yield"],
    "energy": ["oil", "gas", "energy", "solar", "renewable", "opec", "crude", "petroleum"],
    "health": ["fda", "drug", "pharma", "vaccine", "biotech", "clinical", "trial", "approval"],
    "idx": ["indonesia", "ihsg", "idx", "bei", "jakarta", "rupiah", "bi", "bank indonesia"],
}


def analyze_sentiment(text: str) -> dict:
    """Keyword-based sentiment. Returns {score, label, pos_count, neg_count}."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    total = pos + neg
    if total == 0:
        return {"score": 0.5, "label": "NEUTRAL", "pos_count": 0, "neg_count": 0}
    score = pos / total
    if score > 0.6:
        label = "POSITIVE"
    elif score < 0.4:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
    return {"score": round(score, 2), "label": label, "pos_count": pos, "neg_count": neg}


def extractive_summary(text: str, max_sentences: int = 3) -> str:
    """Extract top sentences by importance. Zero AI cost."""
    if not text or len(text) < 50:
        return text

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if len(sentences) <= max_sentences:
        return text

    # Word frequency scoring
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = Counter(w for w in words if len(w) > 3)
    max_freq = max(word_freq.values()) if word_freq else 1
    for w in word_freq:
        word_freq[w] /= max_freq

    # Score each sentence
    scored = []
    for i, sent in enumerate(sentences):
        sent_words = re.findall(r'\b\w+\b', sent.lower())
        if not sent_words:
            continue
        score = sum(word_freq.get(w, 0) for w in sent_words) / len(sent_words)
        # Boost first sentence
        if i == 0:
            score *= 1.5
        # Boost sentences with numbers (often key facts)
        if re.search(r'\d', sent):
            score *= 1.2
        scored.append((score, i, sent))

    # Return top sentences in order
    scored.sort(reverse=True)
    top = sorted(scored[:max_sentences], key=lambda x: x[1])
    return " ".join(s[2] for s in top)


def extract_topics(text: str) -> list[str]:
    """Extract relevant topics/sectors from text."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    topics = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        if words & set(keywords):
            topics.append(sector.upper())
    return topics if topics else ["GENERAL"]


def estimate_impact(text: str) -> str:
    """Estimate market impact level from keywords."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    hits = len(words & IMPACT_WORDS)
    if hits >= 3:
        return "HIGH"
    elif hits >= 1:
        return "MEDIUM"
    return "LOW"


def score_article(title: str, description: str = "") -> dict:
    """Full scoring for an article — sentiment + topics + impact + summary."""
    combined = f"{title}. {description}" if description else title
    sentiment = analyze_sentiment(combined)
    topics = extract_topics(combined)
    impact = estimate_impact(combined)
    summary = extractive_summary(combined, max_sentences=2)
    return {
        "sentiment": sentiment["label"],
        "sentiment_score": sentiment["score"],
        "topics": topics,
        "impact": impact,
        "summary": summary,
    }


def batch_score(articles: list[dict]) -> dict:
    """Score a batch of articles and return aggregate stats."""
    scored = []
    sentiment_counts = Counter()
    topic_counts = Counter()
    impact_counts = Counter()

    for art in articles:
        title = art.get("title", "")
        desc = art.get("description", "")
        s = score_article(title, desc)
        scored.append({**art, **s})
        sentiment_counts[s["sentiment"]] += 1
        for t in s["topics"]:
            topic_counts[t] += 1
        impact_counts[s["impact"]] += 1

    total = len(articles) or 1
    return {
        "articles": scored,
        "aggregate": {
            "total": len(articles),
            "sentiment_distribution": dict(sentiment_counts),
            "sentiment_ratio": {
                "positive": round(sentiment_counts.get("POSITIVE", 0) / total, 2),
                "negative": round(sentiment_counts.get("NEGATIVE", 0) / total, 2),
                "neutral": round(sentiment_counts.get("NEUTRAL", 0) / total, 2),
            },
            "top_topics": topic_counts.most_common(5),
            "impact_distribution": dict(impact_counts),
            "overall_sentiment": sentiment_counts.most_common(1)[0][0] if sentiment_counts else "NEUTRAL",
        },
    }


def generate_suggestions(scored_articles: list[dict]) -> list[dict]:
    """Generate market suggestions from scored articles. No AI needed."""
    suggestions = []
    agg = batch_score(scored_articles)["aggregate"]

    overall = agg["overall_sentiment"]
    ratio = agg["sentiment_ratio"]

    # Market tone suggestion
    if ratio["positive"] > 0.6:
        suggestions.append({
            "type": "MARKET_TONE",
            "icon": "&#128994;",
            "title": "Market Sentiment Bullish",
            "detail": f"{ratio['positive']*100:.0f}% of news is positive. Market tone is optimistic.",
            "action": "Consider reviewing long positions in trending sectors.",
        })
    elif ratio["negative"] > 0.6:
        suggestions.append({
            "type": "MARKET_TONE",
            "icon": "&#128308;",
            "title": "Market Sentiment Bearish",
            "detail": f"{ratio['negative']*100:.0f}% of news is negative. Caution advised.",
            "action": "Review risk exposure. Consider defensive positions.",
        })
    else:
        suggestions.append({
            "type": "MARKET_TONE",
            "icon": "&#128992;",
            "title": "Market Sentiment Mixed",
            "detail": "News sentiment is balanced. No strong directional signal.",
            "action": "Wait for clearer signals. Monitor key sectors.",
        })

    # Topic-based suggestions
    top_topics = [t[0] for t in agg["top_topics"][:3]]
    topic_suggest = {
        "TECH": {"icon": "&#128187;", "title": "Tech Sector Active", "action": "Monitor tech earnings and AI developments."},
        "CRYPTO": {"icon": "&#128176;", "title": "Crypto Market Moving", "action": "Check BTC/ETH correlation with equity markets."},
        "FINANCE": {"icon": "&#127974;", "title": "Financial Sector News", "action": "Watch interest rate decisions and banking earnings."},
        "ENERGY": {"icon": "&#9889;", "title": "Energy Sector Active", "action": "Monitor oil prices and energy policy changes."},
        "HEALTH": {"icon": "&#129657;", "title": "Healthcare Updates", "action": "Watch FDA approvals and pharma earnings."},
        "IDX": {"icon": "&#127470;&#127465;", "title": "Indonesia Market News", "action": "Monitor IHSG, Rupiah, and Bank Indonesia policy."},
    }
    for t in top_topics:
        if t in topic_suggest:
            suggestions.append({"type": "SECTOR", **topic_suggest[t]})

    # High impact alerts
    high_impact = [a for a in scored_articles if a.get("impact") == "HIGH"]
    if high_impact:
        suggestions.append({
            "type": "HIGH_IMPACT",
            "icon": "&#9888;&#65039;",
            "title": f"{len(high_impact)} High-Impact Articles Detected",
            "detail": high_impact[0].get("title", ""),
            "action": "These articles may significantly move markets. Review positions.",
        })

    # Negative alert
    neg_articles = [a for a in scored_articles if a.get("sentiment") == "NEGATIVE"]
    if len(neg_articles) >= 3:
        suggestions.append({
            "type": "RISK_ALERT",
            "icon": "&#128680;",
            "title": f"{len(neg_articles)} Negative News Detected",
            "detail": "Multiple negative headlines may indicate sector weakness.",
            "action": "Review stop-loss levels and risk management.",
        })

    return suggestions
