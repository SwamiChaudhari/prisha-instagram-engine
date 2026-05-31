"""
headline_engine.py — Generate and score multiple headlines, pick the best.

Generates 15+ variations using different patterns/emotions.
Scores each on curiosity, brevity, emotional_trigger, clarity.
Never uses the first generated headline.
"""

import random
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

HEADLINE_PATTERNS = {
    "money_question": [
        "💰 Can You Get {amount}? Here's How",
        "💰 {target}: Don't Miss This Financial Benefit",
        "💰 New Benefit Worth {amount} For {target}",
        "💰 Government Giving {amount} — Are You Eligible?",
        "💰 This Changes Everything For {target}",
    ],
    "warning": [
        "⚠️ {target}: This Mistake Costs Lakhs",
        "⚠️ Before You Apply, Read This",
        "⚠️ Most {target} Don't Know This Rule",
        "⚠️ Deadline Alert For {target}",
        "⚠️ {target}: Don't Ignore This Update",
    ],
    "breaking": [
        "🚨 Breaking: {topic}",
        "🚨 New Rule For {target} Starting Now",
        "🚨 Major Update Every {target} Must Know",
        "🚨 Government Announces {topic}",
        "🚨 This Affects Every {target} In India",
    ],
    "curiosity": [
        "❓ Why Are {target} Rushing For This?",
        "❓ What {target} Don't Know About {topic}",
        "❓ Is Your {business} Missing This Benefit?",
        "❓ The Secret Behind {topic}",
        "❓ {target}: This Changes Everything",
    ],
    "urgency": [
        "🔥 {target}: Limited Time Benefit",
        "🔥 Trending Now: {topic}",
        "🔥 Every {target} Is Talking About This",
        "🔥 Why {target} Are Applying Today",
        "🔥 {topic} — Apply Before It's Too Late",
    ],
    "official": [
        "🏛 Government Launches {scheme}",
        "🏛 New Scheme For {target} — {topic}",
        "🏛 {scheme} Opens: Here's What To Know",
        "🏛 Official: {topic}",
        "🏛 {target}: Government Announces New Benefit",
    ],
}


class HeadlineEngine:
    """Generate, score, and select the best headline."""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def generate_best_headline(self, topic: str, category: str = "", target: str = "Business Owners", scheme: str = "", amount: str = "", business: str = "Business") -> dict:
        """
        Generate 15+ headline variations and return the highest-scoring one.
        Returns: {"headline": str, "scores": dict, "pattern": str}
        """
        # Generate variations from all patterns
        all_headlines = []
        placeholders = {
            "target": target,
            "topic": topic[:60],
            "scheme": scheme or topic[:40],
            "amount": amount or "",
            "business": business,
            "story": topic[:40],
            "benefit": "Government Benefits",
        }

        for pattern_name, templates in HEADLINE_PATTERNS.items():
            for template in templates:
                try:
                    headline = template.format(**placeholders)
                    all_headlines.append({"headline": headline, "pattern": pattern_name})
                except KeyError:
                    pass

        # Shuffle and take 15+
        random.shuffle(all_headlines)
        candidates = all_headlines[:max(15, len(all_headlines))]

        # Score each headline
        scored = []
        for c in candidates:
            c["scores"] = self._score_headline(c["headline"])
            scored.append(c)

        # Sort by total score
        scored.sort(key=lambda x: x["scores"]["_total"], reverse=True)

        # Never use the first generated — use the best scored
        best = scored[0] if scored else {"headline": topic, "pattern": "default", "scores": {}}

        return best

    def _score_headline(self, headline: str) -> dict:
        """Score a headline on 4 metrics."""
        scores = {
            "curiosity": self._score_curiosity(headline),
            "brevity": self._score_brevity(headline),
            "emotional_trigger": self._score_emotional_trigger(headline),
            "clarity": self._score_clarity(headline),
        }
        scores["_total"] = sum(scores.values())
        return scores

    def _score_curiosity(self, h: str) -> int:
        score = 5
        if "?" in h: score += 2
        if any(w in h.lower() for w in ["secret", "hidden", "why", "what if", "don't know", "missing"]): score += 2
        if any(e in h for e in ["❓", "💰", "🚨"]): score += 1
        return min(score, 10)

    def _score_brevity(self, h: str) -> int:
        words = len(h.split())
        if words <= 5: return 10
        if words <= 7: return 9
        if words <= 9: return 7
        if words <= 12: return 5
        return 3

    def _score_emotional_trigger(self, h: str) -> int:
        score = 4
        emotional_indicators = ["🚨", "⚠️", "💰", "🔥", "❓", "🏛", "don't miss", "alert", "breaking", "urgent", "important", "must know", "lakh", "crore", "free", "without"]
        for ind in emotional_indicators:
            if ind.lower() in h.lower():
                score += 1
        return min(score, 10)

    def _score_clarity(self, h: str) -> int:
        score = 7
        # Penalize if too long
        if len(h) > 80: score -= 2
        # Penalize if no clear subject
        if not any(w in h.lower() for w in ["business", "shop", "msme", "startup", "government", "loan", "scheme", "gst", "udyam", "fssai"]):
            score -= 1
        # Bonus for specific amounts
        if re.search(r'[\d,]+\s*(lakh|crore|rs|₹)', h.lower()):
            score += 1
        return min(max(score, 1), 10)


def main():
    engine = HeadlineEngine()
    result = engine.generate_best_headline(
        topic="PMEGP loan scheme gives Rs 25 lakh subsidy to small businesses",
        category="loan_subsidy",
        target="Small Business Owners",
        scheme="PMEGP",
        amount="Rs 25 Lakh",
    )
    print(f"Best headline: {result['headline']}")
    print(f"Pattern: {result['pattern']}")
    print(f"Scores: {result['scores']}")


if __name__ == "__main__":
    main()
