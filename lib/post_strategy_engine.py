"""
post_strategy_engine.py — Determine what type of post to create today.

Handles:
- Weekly content mix (Mon=Opportunity, Tue=GovScheme, etc.)
- Content pillar rotation (8 pillars)
- Human face rule (65% of posts should have faces)
- Feed diversity (no repetitive content)
"""

import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
POSTS_HISTORY_PATH = DATA_DIR / "generated_posts.json"

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class PostStrategyEngine:
    """Determine the optimal post type for today."""

    def __init__(self):
        self.config = self._load_config()
        self.face_percentage = self.config.get("face_usage", {}).get("percentage", 0.65)
        self.face_enabled = self.config.get("face_usage", {}).get("enabled", True)

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def get_today_strategy(self) -> dict:
        """
        Get today's post strategy.
        Returns: {
            "template": str,
            "pillar": str,
            "use_face": bool,
            "template_reason": str,
            "pillar_reason": str,
        }
        """
        day_name = DAY_NAMES[datetime.now(IST).weekday()]
        weekly_mix = self.config.get("weekly_mix", {})

        # 1. Get today's preferred template from weekly mix
        preferred_template = weekly_mix.get(day_name, "opportunity_alert")

        # 2. Select pillar (avoiding recent repeats)
        pillar = self._select_pillar()

        # 3. Check if face should be used today
        use_face = self._should_use_face()

        # 4. Validate against recent history — if same template used 2x this week, try alternative
        template = self._validate_template_against_history(preferred_template)

        return {
            "template": template,
            "pillar": pillar,
            "use_face": use_face,
            "day": day_name,
            "template_reason": f"weekly_mix: {day_name} → {preferred_template}",
            "pillar_reason": f"weighted rotation avoiding recent repeats",
        }

    def _select_pillar(self) -> str:
        """Select content pillar, avoiding recent repeats."""
        pillars = self.config.get("content_pillars", {})
        if not pillars:
            return "government_schemes"

        # Get recent pillars used
        recent_pillars = self._get_recent_pillars(n=7)

        # Build weighted pool (exclude yesterday's pillar)
        yesterday_pillar = recent_pillars[0] if recent_pillars else None
        weights = {}
        for name, info in pillars.items():
            w = info.get("weight", 10)
            if name == yesterday_pillar:
                w = 0  # Avoid same pillar two days in a row
            weights[name] = w

        # Weighted random selection
        total = sum(weights.values())
        if total == 0:
            return random.choice(list(pillars.keys()))

        r = random.uniform(0, total)
        cumulative = 0
        for name, w in weights.items():
            cumulative += w
            if r <= cumulative:
                return name

        return list(pillars.keys())[0]

    def _should_use_face(self) -> bool:
        """Determine if today's post should include a human face (65% target)."""
        if not self.face_enabled:
            return False

        # Check recent face usage
        recent_posts = self._get_recent_posts(n=30)
        if not recent_posts:
            return True  # First post, use face

        face_count = sum(1 for p in recent_posts if p.get("use_face", False))
        current_percentage = face_count / len(recent_posts)

        # If below target, strongly favor face
        if current_percentage < self.face_percentage:
            return random.random() < 0.8  # 80% chance
        else:
            return random.random() < 0.4  # 40% chance (maintain diversity)

    def _validate_template_against_history(self, preferred: str) -> str:
        """Ensure we don't use the same template more than 2x per week."""
        recent = self._get_recent_posts(n=7)
        if not recent:
            return preferred

        template_counts = {}
        for post in recent:
            t = post.get("template", "")
            template_counts[t] = template_counts.get(t, 0) + 1

        if template_counts.get(preferred, 0) >= 2:
            # Find alternative template
            all_templates = ["breaking_news", "opportunity_alert", "government_scheme",
                           "business_growth", "warning_policy", "success_story", "quick_tips"]
            alternatives = [t for t in all_templates
                          if template_counts.get(t, 0) < 2 and t != preferred]
            if alternatives:
                return random.choice(alternatives)

        return preferred

    def _get_recent_pillars(self, n: int = 7) -> list:
        """Get pillars from recent posts."""
        posts = self._get_recent_posts(n)
        return [p.get("pillar", "") for p in posts if p.get("pillar")]

    def _get_recent_posts(self, n: int = 30) -> list:
        """Load recent posts from history."""
        try:
            if POSTS_HISTORY_PATH.exists():
                with open(POSTS_HISTORY_PATH) as f:
                    data = json.load(f)
                posts = data if isinstance(data, list) else data.get("posts", [])
                return posts[-n:]
        except Exception:
            pass
        return []


def main():
    engine = PostStrategyEngine()
    strategy = engine.get_today_strategy()
    print("Today's strategy:")
    for k, v in strategy.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
