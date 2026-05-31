"""
topic_selector.py — Score and select the best topic for today's post.

Scoring: curiosity, financial_benefit, urgency, relevance, shareability, audience_size
NEW: lead_generation, trust
"""

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

# Target audience keywords for relevance scoring
AUDIENCE_KEYWORDS = {
    "high": ["business owner", "shop owner", "entrepreneur", "msme", "startup", "self-employed", "freelancer"],
    "medium": ["student", "professional", "job seeker", "citizen", "women", "artisan"],
    "low": ["corporate", "enterprise", "multinational", "foreign"],
}

# Financial trigger keywords
MONEY_KEYWORDS = ["lakh", "crore", "rs", "rupee", "loan", "subsidy", "fund", "grant", "financial", "benefit", "save", "earning", "income", "amount", "collateral-free", "free"]

# Urgency keywords
URGENCY_KEYWORDS = ["deadline", "last date", "today", "now", "urgent", "alert", "warning", "expires", "before", "don't miss", "hurry", "limited", "closing soon", "final"]

# Trust keywords
TRUST_KEYWORDS = ["government", "official", "scheme", "approved", "certificate", "mandatory", "act", "rule", "ministry", "pm", "notification", "gazette", "legal"]

# Curiosity triggers
CURIOSITY_PATTERNS = [r"\?", r"!", r"how", r"why", r"what if", r"secret", r"hidden", r"unknown", r"revealed", r"breaking", r"shocking"]

# Generic/boring patterns to reject
GENERIC_PATTERNS = [
    r"^what is",
    r"^benefits of",
    r"^guide to",
    r"^how to apply",
    r"^introduction to",
    r"^overview of",
    r"^everything you need to know",
    r"^all about",
    r"^complete guide",
    r"^step by step guide",
]


class TopicSelector:
    """Score topics on virality metrics and select the best one."""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def select_best(self, topics: list, used_topics: list = None) -> dict:
        """
        Score all topics and return the highest-scoring unused one.
        Filters out already-used topics and generic/educational content.
        """
        if not topics:
            return None

        used_topics = used_topics or []
        scored = []

        for topic in topics:
            # Skip if already used (fuzzy match)
            if self._is_duplicate(topic["topic"], used_topics):
                continue

            # Skip generic/educational content
            if self.is_generic(topic["topic"]):
                continue

            # Score the topic
            topic_with_scores = self.score_topic(topic)
            scored.append(topic_with_scores)

        if not scored:
            # If all filtered out, relax constraints and pick best of remaining
            for topic in topics:
                topic_with_scores = self.score_topic(topic)
                scored.append(topic_with_scores)
            # If still nothing, return None
            if not scored:
                return None

        # Sort by total score and return best
        scored.sort(key=lambda x: x.get("_total_score", 0), reverse=True)
        return scored[0]

    def score_topic(self, topic: dict) -> dict:
        """Score a topic on all metrics and return topic with scores added."""
        headline = topic.get("headline", topic.get("topic", ""))
        category = topic.get("category", "")
        source = topic.get("source", "")

        scores = {
            "curiosity": self._score_curiosity(headline),
            "financial_benefit": self._score_financial_benefit(headline, category),
            "urgency": self._score_urgency(headline),
            "relevance": self._score_relevance(headline, category),
            "shareability": self._score_shareability(headline, category),
            "audience_size": self._score_audience_size(headline, category),
            "lead_generation": self._score_lead_generation(category, source),
            "trust": self._score_trust(headline, source),
        }

        # Weighted total
        weights = {
            "curiosity": 1.5,
            "financial_benefit": 1.5,
            "urgency": 1.2,
            "relevance": 2.0,
            "shareability": 1.5,
            "audience_size": 1.0,
            "lead_generation": 1.5,
            "trust": 1.2,
        }

        total = sum(scores[k] * weights[k] for k in scores)
        max_possible = sum(10 * weights[k] for k in weights)
        normalized = round((total / max_possible) * 100, 1)

        topic["_scores"] = scores
        topic["_total_score"] = normalized
        topic["_weighted_raw"] = round(total, 2)
        return topic

    def is_generic(self, headline: str) -> bool:
        """Check if a headline is generic/educational and should be rejected."""
        lower = headline.lower().strip()
        for pattern in GENERIC_PATTERNS:
            if re.search(pattern, lower):
                return True
        # Also reject if it starts with emoji but is still generic
        emoji_stripped = re.sub(r'[^\w\s]', '', lower).strip()
        for pattern in GENERIC_PATTERNS:
            if re.search(pattern, emoji_stripped):
                return True
        return False

    # ── Individual Scorers (each 1-10) ───────────────────────────────────────

    def _score_curiosity(self, headline: str) -> int:
        """How curiosity-inducing is the headline?"""
        score = 5
        lower = headline.lower()

        # Questions are highly curious
        if "?" in headline:
            score += 2

        # Curiosity trigger words
        for pattern in CURIOSITY_PATTERNS:
            if re.search(pattern, lower):
                score += 1
                break

        # Numbers/detail increase curiosity
        if re.search(r'\d+', headline):
            score += 1

        # Short punchy headlines are more curious
        word_count = len(headline.split())
        if word_count <= 5:
            score += 1
        elif word_count > 10:
            score -= 1

        # Has emojis (attention grabbers)
        if any(ord(c) > 127 for c in headline):
            score += 1

        return min(max(score, 1), 10)

    def _score_financial_benefit(self, headline: str, category: str) -> int:
        """Does it mention money, savings, or financial benefit?"""
        score = 4
        lower = headline.lower()

        # Direct money mentions
        for kw in MONEY_KEYWORDS:
            if kw in lower:
                score += 2
                break

        # Specific amounts mentioned
        if re.search(r'(rs\.?\s*)?[\d,]+\s*(lakh|crore)', lower):
            score += 3

        # Category-based scoring
        if category in ["loan_subsidy", "government_schemes"]:
            score += 1
        if category in ["compliance"]:
            score -= 1  # Compliance posts are rarely about money

        # Benefit/savings words
        if any(w in lower for w in ["free", "without", "save", "discount", "zero", "no cost"]):
            score += 1

        return min(max(score, 1), 10)

    def _score_urgency(self, headline: str) -> int:
        """Does it have time sensitivity or urgency?"""
        score = 4
        lower = headline.lower()

        for kw in URGENCY_KEYWORDS:
            if kw in lower:
                score += 2
                break

        # Alert/warning emojis
        if any(e in headline for e in ["🚨", "⚠️", "⏰", "🔴"]):
            score += 2

        # Today/now mentions
        if any(w in lower for w in ["today", "now", "immediately", "asap"]):
            score += 2

        # Deadline mentions
        if "deadline" in lower or "last date" in lower:
            score += 3

        return min(max(score, 1), 10)

    def _score_relevance(self, headline: str, category: str) -> int:
        """How relevant to target audience?"""
        score = 5
        lower = headline.lower()

        # High-relevance audience keywords
        for kw in AUDIENCE_KEYWORDS["high"]:
            if kw in lower:
                score += 2
                break

        # Medium relevance
        for kw in AUDIENCE_KEYWORDS["medium"]:
            if kw in lower:
                score += 1
                break

        # Category-based
        high_cats = ["government_schemes", "loan_subsidy", "business_registration"]
        if category in high_cats:
            score += 1

        # Maharashtra/local relevance
        if any(w in lower for w in ["maharashtra", "mumbai", "pune", "nagpur"]):
            score += 2

        return min(max(score, 1), 10)

    def _score_shareability(self, headline: str, category: str) -> int:
        """Would people share this with others?"""
        score = 5
        lower = headline.lower()

        # Financial content is highly shareable
        if category in ["loan_subsidy", "government_schemes"]:
            score += 2

        # Content that affects others
        if any(w in lower for w in ["every business", "all shop", "everyone", "must know", "important"]):
            score += 2

        # Emotional triggers boost sharing
        if any(e in headline for e in ["🚨", "💰", "🔥", "⚠️"]):
            score += 1

        # Questions get shared more
        if "?" in headline:
            score += 1

        # Too technical = less shareable
        if any(w in lower for w in ["amendment", "notification no.", "section", "subsection", "clause"]):
            score -= 2

        return min(max(score, 1), 10)

    def _score_audience_size(self, headline: str, category: str) -> int:
        """How many people does this affect?"""
        score = 5
        lower = headline.lower()

        # Nationwide topics
        if any(w in lower for w in ["all india", "national", "every state", "pan india"]):
            score += 3

        # Maharashtra focus (our primary market)
        if any(w in lower for w in ["maharashtra", "marathi"]):
            score += 1

        # Category-based audience
        wide_audience = ["government_schemes", "loan_subsidy", "compliance", "tax"]
        if category in wide_audience:
            score += 2

        # Narrow topics
        if any(w in lower for w in ["only", "specific", "particular", "specialist"]):
            score -= 1

        return min(max(score, 1), 10)

    def _score_lead_generation(self, category: str, source: str) -> int:
        """How likely is this topic to generate leads for Prisha?"""
        score = 4

        # Categories that directly drive leads
        lead_categories = {
            "government_schemes": 3,
            "loan_subsidy": 3,
            "business_registration": 3,
            "compliance": 2,
            "tax": 2,
            "registration": 2,
            "certificates": 2,
            "scholarship": 1,
            "announcement": 0,
        }
        score += lead_categories.get(category, 0)

        # Real sources = more credible = more leads
        if source in ["pib", "msme", "startup_india"]:
            score += 1

        return min(max(score, 1), 10)

    def _score_trust(self, headline: str, source: str) -> int:
        """How trustworthy does this content appear?"""
        score = 5
        lower = headline.lower()

        # Source credibility
        trusted_sources = {"pib": 3, "msme": 2, "startup_india": 2, "india_gov": 2, "maharashtra": 2}
        score += trusted_sources.get(source, 0)

        # Trust keywords
        for kw in TRUST_KEYWORDS:
            if kw in lower:
                score += 1
                break

        # Official-sounding language
        if any(w in lower for w in ["official", "announced", "launched", "approved", "govt"]):
            score += 1

        # Too clickbaity = less trustworthy
        if any(w in lower for w in ["shocking", "mind-blowing", "you won't believe", "crazy"]):
            score -= 2

        return min(max(score, 1), 10)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _is_duplicate(self, topic: str, used_topics: list) -> bool:
        """Check if topic or similar was already posted."""
        topic_lower = topic.lower().strip()
        topic_key = re.sub(r'[^\w\s]', '', topic_lower)[:50]

        for used in used_topics:
            used_lower = used.lower().strip() if isinstance(used, str) else used.get("topic", "").lower().strip()
            used_key = re.sub(r'[^\w\s]', '', used_lower)[:50]

            # Exact match after cleaning
            if topic_key == used_key:
                return True

            # High overlap (80%+)
            if len(topic_key) > 10 and len(used_key) > 10:
                overlap = sum(1 for a, b in zip(topic_key, used_key) if a == b) / max(len(topic_key), len(used_key))
                if overlap > 0.8:
                    return True

        return False


def main():
    """Test topic selector."""
    from trend_researcher import TrendResearcher

    researcher = TrendResearcher()
    selector = TopicSelector()

    topics = researcher.research_all()
    print(f"Researched {len(topics)} topics")

    # Simulate used topics
    used = []
    best = selector.select_best(topics, used)

    if best:
        print(f"\nBest topic selected:")
        print(f"  Headline: {best['headline']}")
        print(f"  Category: {best['category']}")
        print(f"  Source: {best['source']}")
        print(f"  Total Score: {best.get('_total_score', 0)}/100")
        print(f"  Individual scores:")
        for metric, score in best.get('_scores', {}).items():
            print(f"    {metric}: {score}/10")
    else:
        print("No suitable topic found")


if __name__ == "__main__":
    main()
