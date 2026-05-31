"""
style_analyzer.py — Analyze reference style and select best template for a topic.

Uses the reference DNA (dark theme, news-style, info-dense) to:
1. Select the best template for a given topic/category
2. Generate layout specifications for the image engine
3. Ensure consistency with reference style
"""

import random
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
TEMPLATES_PATH = PROJECT_ROOT / "templates" / "layout_templates.yaml"

# Template selection rules based on category + topic keywords
TEMPLATE_RULES = {
    "breaking_news": {
        "categories": ["compliance", "tax", "announcement"],
        "keywords": ["deadline", "urgent", "alert", "warning", "new rule", "update", "breaking", "mandatory", "penalty"],
        "priority": 1,
    },
    "opportunity_alert": {
        "categories": ["loan_subsidy", "government_schemes"],
        "keywords": ["loan", "subsidy", "scheme", "benefit", "apply", "eligible", "lakh", "crore", "fund", "grant", "free"],
        "priority": 1,
    },
    "government_scheme": {
        "categories": ["registration", "certificates", "government_schemes"],
        "keywords": ["register", "certificate", "scheme", "government", "official", "launch", "announce", "udyam", "gst", "fssai", "shop act"],
        "priority": 1,
    },
    "business_growth": {
        "categories": ["business_growth", "success_stories"],
        "keywords": ["grow", "success", "tip", "strategy", "hack", "guide", "how to", "improve", "increase", "profit"],
        "priority": 1,
    },
    "warning_policy": {
        "categories": ["compliance", "tax"],
        "keywords": ["penalty", "fine", "deadline", "mandatory", "required", "must", "rule", "regulation", "act", "section"],
        "priority": 2,
    },
}


class StyleAnalyzer:
    """Select template and generate layout specs based on reference DNA."""

    def __init__(self):
        self.config = self._load_config()
        self.templates = self._load_templates()
        self.style = self.config.get("style", {})

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _load_templates(self) -> dict:
        try:
            with open(TEMPLATES_PATH) as f:
                data = yaml.safe_load(f) or {}
            return data.get("templates", {})
        except Exception:
            return {}

    def select_template(self, topic: str, category: str, strategy_template: str = None) -> str:
        """
        Select the best template for this topic.
        Respects the weekly strategy template if provided.
        """
        # If strategy engine specified a template, use it (but validate)
        if strategy_template and strategy_template in self.templates:
            return strategy_template

        # Score each template for this topic
        scores = {}
        topic_lower = topic.lower()

        for template_name, rules in TEMPLATE_RULES.items():
            score = 0
            # Category match
            if category in rules.get("categories", []):
                score += 3
            # Keyword match
            for kw in rules.get("keywords", []):
                if kw in topic_lower:
                    score += 2
            scores[template_name] = score

        # Return highest scoring template
        if scores:
            best = max(scores, key=scores.get)
            if scores[best] > 0:
                return best

        # Default based on category
        defaults = {
            "loan_subsidy": "opportunity_alert",
            "government_schemes": "government_scheme",
            "business_registration": "opportunity_alert",
            "compliance": "warning_policy",
            "tax": "warning_policy",
            "certificates": "government_scheme",
            "scholarship": "opportunity_alert",
            "announcement": "breaking_news",
        }
        return defaults.get(category, "opportunity_alert")

    def get_layout_spec(self, template_name: str) -> dict:
        """Get the full layout specification for a template."""
        template = self.templates.get(template_name, {})
        return {
            "name": template_name,
            "layout": template.get("layout", {}),
            "color_overlay": template.get("color_overlay", {}),
            "mood": template.get("mood", ""),
            "style": self.style,
        }

    def get_color_scheme(self, template_name: str) -> dict:
        """Get the color scheme for a template."""
        colors = self.style.get("colors", {})
        template = self.templates.get(template_name, {})

        # Template-specific accent color
        accent_map = {
            "breaking_news": colors.get("accent_red", "#FF3333"),
            "opportunity_alert": colors.get("accent_green", "#00FF88"),
            "government_scheme": colors.get("accent_blue", "#4A90D9"),
            "business_growth": colors.get("accent_yellow", "#FFD700"),
            "warning_policy": colors.get("accent_red", "#FF3333"),
        }

        return {
            "background_primary": colors.get("background_primary", "#0A0E11"),
            "background_secondary": colors.get("background_secondary", "#1A1A2E"),
            "text_primary": colors.get("text_primary", "#FFFFFF"),
            "text_secondary": colors.get("text_secondary", "#B0B0B0"),
            "accent": accent_map.get(template_name, colors.get("accent_blue", "#4A90D9")),
            "accent_green": colors.get("accent_green", "#00FF88"),
            "accent_yellow": colors.get("accent_yellow", "#FFD700"),
            "accent_red": colors.get("accent_red", "#FF3333"),
        }

    def get_typography_spec(self, template_name: str) -> dict:
        """Get typography specifications."""
        typo = self.style.get("typography", {})
        return {
            "headline_font": typo.get("headline_font", "Bebas Neue, Anton, Impact"),
            "body_font": typo.get("body_font", "Montserrat, Poppins, Inter"),
            "headline_size": int(typo.get("headline_size", "72-96").split("-")[0]),
            "body_size": int(typo.get("body_size", "24-32").split("-")[0]),
            "cta_size": int(typo.get("cta_size", "28-36").split("-")[0]),
        }


if __name__ == "__main__":
    analyzer = StyleAnalyzer()

    test_cases = [
        ("PMEGP loan gives Rs 25 lakh subsidy", "loan_subsidy"),
        ("GST filing deadline approaching", "compliance"),
        ("New MSME registration scheme launched", "government_schemes"),
        ("ITR filing penalty for late submission", "tax"),
    ]

    for topic, category in test_cases:
        template = analyzer.select_template(topic, category)
        colors = analyzer.get_color_scheme(template)
        print(f"[{category}] {topic[:50]}")
        print(f"  Template: {template}")
        print(f"  Accent: {colors['accent']}")
        print()
