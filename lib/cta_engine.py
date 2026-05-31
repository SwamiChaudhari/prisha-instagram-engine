"""
cta_engine.py — Rotate CTAs to avoid repetition.
"""

import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
HISTORY_PATH = PROJECT_ROOT / "data" / "generated_posts.json"

# CTA categories matched to post types
CTA_BY_TYPE = {
    "opportunity_alert": [
        "📩 DM 'INFO'",
        "📞 Contact Us Today",
        "💬 Comment 'GUIDE'",
        "📩 Send Message For Details",
        "📞 Call For Free Consultation",
    ],
    "breaking_news": [
        "🔁 Share With Friends",
        "📌 Save This Post",
        "💬 Tag Someone Who Needs This",
        "📌 Share With Business Friends",
    ],
    "government_scheme": [
        "📩 DM 'INFO'",
        "💬 Comment 'HELP'",
        "📞 Contact Us Today",
        "📩 Send Message For Details",
    ],
    "business_growth": [
        "📌 Save This Post",
        "💬 Comment Your Business Type",
        "🔁 Share With Friends",
        "💬 Tag Someone Who Needs This",
    ],
    "warning_policy": [
        "📌 Save This Post",
        "🔁 Share With Friends",
        "💬 Comment 'HELP'",
        "📞 Contact Us Today",
    ],
    "success_story": [
        "💬 Comment Your Story",
        "📌 Save This Post",
        "🔁 Share With Friends",
        "💬 Tag Someone Who Needs This",
    ],
    "quick_tips": [
        "📌 Save This Post",
        "💬 Comment 'GUIDE'",
        "🔁 Share With Friends",
        "📩 DM 'INFO'",
    ],
}


class CTAEngine:
    """Rotate CTAs to avoid repetition."""

    def __init__(self):
        self.config = self._load_config()
        self.cta_pool = self.config.get("cta_pool", [])

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def get_cta(self, template: str = None, pillar: str = None) -> str:
        """
        Get a CTA that wasn't used recently.
        Matches CTA style to post type.
        """
        # Get recent CTAs to avoid
        recent_ctas = self._get_recent_ctas(n=7)

        # Get pool for this template type
        pool = CTA_BY_TYPE.get(template, self.cta_pool)
        if not pool:
            pool = self.cta_pool or ["📩 DM 'INFO'", "📌 Save This Post", "🔁 Share With Friends"]

        # Filter out recently used
        available = [c for c in pool if c not in recent_ctas]
        if not available:
            available = pool  # Reset if all used

        return random.choice(available)

    def _get_recent_ctas(self, n: int = 7) -> list:
        """Get CTAs from recent posts."""
        try:
            if HISTORY_PATH.exists():
                with open(HISTORY_PATH) as f:
                    data = json.load(f)
                posts = data if isinstance(data, list) else data.get("posts", [])
                return [p.get("cta", "") for p in posts[-n:] if p.get("cta")]
        except Exception:
            pass
        return []


def main():
    engine = CTAEngine()
    for template in ["opportunity_alert", "breaking_news", "warning_policy"]:
        cta = engine.get_cta(template=template)
        print(f"{template}: {cta}")


if __name__ == "__main__":
    main()
