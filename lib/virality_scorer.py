"""
virality_scorer.py — Score posts on 10 metrics before publishing.

Metrics: curiosity, financial_opportunity, urgency, trust, visual_appeal,
         shareability, engagement_potential, local_relevance, lead_generation, humanization

All must be >= 8/10. Auto-regenerate if any fail.
Also computes reference_similarity score (target >= 85%).
"""

import json
import random
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


class ViralityScorer:
    """Score Instagram posts on 10 virality metrics."""

    def __init__(self):
        self.config = self._load_config()
        self.metrics_config = self.config.get("viratility_metrics", {})
        self.threshold = 8
        self.min_reference_similarity = self.config.get("pipeline", {}).get("min_reference_similarity", 85)

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def score_post(self, post: dict) -> dict:
        """
        Score a post on all 10 metrics.
        post keys: headline, caption, image_prompt, topic, category, hashtags, info_blocks, pillar
        Returns: {
            "scores": {metric: score},
            "overall_score": float,
            "passed": bool,
            "reference_similarity": int,
            "feedback": list[str],
        }
        """
        scores = {
            "curiosity": self._score_curiosity(post),
            "financial_opportunity": self._score_financial_opportunity(post),
            "urgency": self._score_urgency(post),
            "trust": self._score_trust(post),
            "visual_appeal": self._score_visual_appeal(post),
            "shareability": self._score_shareability(post),
            "engagement_potential": self._score_engagement(post),
            "local_relevance": self._score_local_relevance(post),
            "lead_generation": self._score_lead_generation(post),
            "humanization": self._score_humanization(post),
        }

        weights = {
            "curiosity": 1.5,
            "financial_opportunity": 1.5,
            "urgency": 1.2,
            "trust": 1.2,
            "visual_appeal": 1.0,
            "shareability": 1.0,
            "engagement_potential": 1.0,
            "local_relevance": 0.8,
            "lead_generation": 1.5,
            "humanization": 1.3,
        }

        weighted_total = sum(scores[k] * weights.get(k, 1) for k in scores)
        max_total = sum(10 * weights.get(k, 1) for k in scores)
        overall = round((weighted_total / max_total) * 100, 1)

        # Check if all metrics meet threshold
        failed_metrics = [k for k, v in scores.items() if v < self.threshold]
        passed = len(failed_metrics) == 0

        # Reference similarity (style match)
        ref_sim = self._reference_similarity(post)

        # Generate feedback
        feedback = self._generate_feedback(scores, failed_metrics)

        return {
            "scores": scores,
            "overall_score": overall,
            "passed": passed,
            "failed_metrics": failed_metrics,
            "reference_similarity": ref_sim,
            "feedback": feedback,
        }

    # ── Individual Scorers (1-10) ────────────────────────────────────────────

    def _score_curiosity(self, post: dict) -> int:
        headline = post.get("headline", "")
        score = 5
        if "?" in headline: score += 2
        if any(w in headline.lower() for w in ["why", "how", "what if", "secret", "hidden", "missing", "don't know"]): score += 2
        if any(e in headline for e in ["❓", "🚨", "💰", "🔥"]): score += 1
        if re.search(r'\d+', headline): score += 1
        return min(max(score, 1), 10)

    def _score_financial_opportunity(self, post: dict) -> int:
        headline = post.get("headline", "")
        topic = post.get("topic", "")
        category = post.get("category", "")
        score = 4
        text = (headline + " " + topic).lower()
        if any(w in text for w in ["lakh", "crore", "rs", "₹", "loan", "subsidy", "fund"]): score += 3
        if re.search(r'[\d,]+\s*(lakh|crore)', text): score += 2
        if category in ["loan_subsidy", "government_schemes"]: score += 1
        if any(w in text for w in ["free", "without", "save", "zero collateral"]): score += 1
        return min(max(score, 1), 10)

    def _score_urgency(self, post: dict) -> int:
        headline = post.get("headline", "")
        score = 4
        text = headline.lower()
        if any(w in text for w in ["deadline", "last date", "urgent", "alert", "warning", "today", "now"]): score += 3
        if any(e in headline for e in ["🚨", "⚠️", "⏰"]): score += 2
        if "don't miss" in text or "before" in text: score += 2
        return min(max(score, 1), 10)

    def _score_trust(self, post: dict) -> int:
        headline = post.get("headline", "")
        score = 5
        text = headline.lower()
        if any(w in text for w in ["government", "official", "scheme", "approved", "ministry", "pm"]): score += 2
        if post.get("source") in ["pib", "msme", "startup_india"]: score += 2
        if any(w in text for w in ["announced", "launched", "notification"]): score += 1
        # Penalize clickbait
        if any(w in text for w in ["shocking", "mind-blowing", "you won't believe", "crazy"]): score -= 2
        return min(max(score, 1), 10)

    def _score_visual_appeal(self, post: dict) -> int:
        """Score based on image prompt quality and template selection."""
        prompt = post.get("image_prompt", "")
        template = post.get("template", "")
        score = 5
        if prompt and len(prompt) > 50: score += 1
        if template: score += 1
        if post.get("use_face"): score += 2
        if post.get("info_blocks") and len(post.get("info_blocks", [])) >= 3: score += 1
        return min(max(score, 1), 10)

    def _score_shareability(self, post: dict) -> int:
        headline = post.get("headline", "")
        category = post.get("category", "")
        score = 5
        text = headline.lower()
        if category in ["loan_subsidy", "government_schemes"]: score += 2
        if any(w in text for w in ["every business", "all shop", "everyone", "must know"]): score += 2
        if any(e in headline for e in ["🚨", "💰", "🔥", "⚠️"]): score += 1
        if "?" in headline: score += 1
        return min(max(score, 1), 10)

    def _score_engagement(self, post: dict) -> int:
        caption = post.get("caption", "")
        score = 5
        if "comment" in caption.lower(): score += 2
        if "save" in caption.lower(): score += 2
        if "share" in caption.lower() or "tag" in caption.lower(): score += 2
        if "dm" in caption.lower(): score += 1
        if "?" in caption: score += 1
        return min(max(score, 1), 10)

    def _score_local_relevance(self, post: dict) -> int:
        headline = post.get("headline", "")
        score = 4
        text = headline.lower()
        if any(w in text for w in ["maharashtra", "mumbai", "pune", "nagpur", "india", "indian"]): score += 3
        if "business" in text or "msme" in text or "startup" in text: score += 1
        if post.get("pillar") in ["government_schemes", "loans_subsidies", "business_registration"]: score += 1
        return min(max(score, 1), 10)

    def _score_lead_generation(self, post: dict) -> int:
        """How likely is this post to generate leads for Prisha?"""
        category = post.get("category", "")
        pillar = post.get("pillar", "")
        caption = post.get("caption", "")
        score = 4
        # High-lead categories
        if category in ["loan_subsidy", "government_schemes", "business_registration"]: score += 2
        if category in ["compliance", "tax"]: score += 1
        # CTA quality
        if "dm" in caption.lower(): score += 2
        if "contact" in caption.lower() or "call" in caption.lower(): score += 1
        # Specific scheme mention = higher intent
        if any(w in caption.lower() for w in ["pmegp", "mudra", "udyam", "gst", "fssai", "shop act"]): score += 1
        return min(max(score, 1), 10)

    def _score_humanization(self, post: dict) -> int:
        """Does this feel like real media content or a robotic post?"""
        headline = post.get("headline", "")
        caption = post.get("caption", "")
        score = 7  # Start high

        # Penalize robotic language
        robotic_phrases = [
            "it is important to note", "in conclusion", "furthermore",
            "this article will discuss", "as mentioned earlier",
            "dear readers", "to sum up", "in today's world",
        ]
        text = (headline + " " + caption).lower()
        for phrase in robotic_phrases:
            if phrase in text:
                score -= 2
                break

        # Penalize keyword stuffing
        word_counts = {}
        for word in text.split():
            word_counts[word] = word_counts.get(word, 0) + 1
        if any(c > 5 for c in word_counts.values()):
            score -= 2

        # Bonus for natural tone
        if any(w in text for w in ["here's", "don't miss", "stop scrolling", "read carefully"]):
            score += 1

        # Penalize government brochure style
        if any(w in text for w in ["apply at your nearest", "visit our center", "all types of services"]):
            score -= 3

        # Penalize cyber cafe ad style
        if any(w in text for w in ["xerocopy", "printout", "visit us", "call now for all work"]):
            score -= 2

        return min(max(score, 1), 10)

    # ── Reference Similarity ─────────────────────────────────────────────────

    def _reference_similarity(self, post: dict) -> int:
        """
        Compare post style to reference DNA (target >= 85%).
        Checks: headline style, info density, color hints, face usage, news-style elements.
        """
        score = 0
        max_score = 100
        headline = post.get("headline", "")

        # 1. Headline impact (25 points)
        if any(e in headline for e in ["🚨", "⚠️", "💰", "🔥", "❓", "🏛"]): score += 10
        if "?" in headline or "!" in headline: score += 5
        word_count = len(headline.split())
        if 3 <= word_count <= 8: score += 10
        elif word_count <= 10: score += 5

        # 2. Information density (25 points)
        info_blocks = post.get("info_blocks", [])
        if len(info_blocks) >= 4: score += 15
        elif len(info_blocks) >= 3: score += 10
        if any(isinstance(b, dict) and b.get("icon") for b in info_blocks): score += 10
        elif any(isinstance(b, dict) for b in info_blocks): score += 5

        # 3. Face usage (20 points)
        if post.get("use_face"): score += 20

        # 4. News-style elements (15 points)
        category = post.get("category", "")
        if category in ["loan_subsidy", "government_schemes", "compliance"]: score += 10
        if post.get("source") in ["pib", "msme"]: score += 5

        # 5. CTA presence (15 points)
        cta = post.get("cta", "")
        if cta: score += 10
        if any(w in cta.lower() for w in ["dm", "comment", "save", "share"]): score += 5

        return min(score, max_score)

    # ── Feedback ─────────────────────────────────────────────────────────────

    def _generate_feedback(self, scores: dict, failed: list) -> list:
        """Generate specific improvement suggestions for failed metrics."""
        feedback_map = {
            "curiosity": "Add curiosity triggers: question marks, 'why/how/what if' patterns, surprise elements",
            "financial_opportunity": "Mention specific amounts (Rs Lakh/Crore), highlight money benefits",
            "urgency": "Add time sensitivity: deadlines, 'limited time', 'apply now'",
            "trust": "Reference official sources (government, PIB, ministry), use scheme names",
            "visual_appeal": "Include face (human element), use info cards with icons, pick better template",
            "shareability": "Add 'every business/shop owner' language, make it relatable, add share CTA",
            "engagement_potential": "Add comment prompts, save prompts, share prompts, question CTAs",
            "local_relevance": "Reference Maharashtra/India, use local business context",
            "lead_generation": "Add DM/CTA, mention specific scheme names, make it actionable",
            "humanization": "Remove robotic language, avoid government brochure style, write like a real person",
        }
        return [feedback_map.get(m, f"Improve {m}") for m in failed]


if __name__ == "__main__":
    scorer = ViralityScorer()
    test_post = {
        "headline": "💰 Government Giving Rs 25 Lakh Subsidy — Are You Eligible?",
        "caption": "Did you know? The PMEGP scheme gives up to Rs 25 lakh...\n\nComment your business type below!\n\nDM 'INFO' for help with registration.",
        "topic": "PMEGP loan scheme gives Rs 25 lakh subsidy",
        "category": "loan_subsidy",
        "pillar": "loans_subsidies",
        "hashtags": ["PMEGP", "MudraLoan", "BusinessLoan"],
        "info_blocks": [
            {"text": "Up to Rs 25 lakh", "icon": "💰"},
            {"text": "No collateral", "icon": "✓"},
            {"text": "For new businesses", "icon": "🏢"},
            {"text": "Easy online apply", "icon": "📱"},
        ],
        "use_face": True,
        "source": "pib",
        "cta": "📩 DM 'INFO'",
    }
    result = scorer.score_post(test_post)
    print("Scores:")
    for m, s in result["scores"].items():
        status = "✓" if s >= 8 else "✗"
        print(f"  {status} {m}: {s}/10")
    print(f"\nOverall: {result['overall_score']}%")
    print(f"Reference Similarity: {result['reference_similarity']}%")
    print(f"Passed: {result['passed']}")
    if result["feedback"]:
        print(f"Feedback: {result['feedback']}")
