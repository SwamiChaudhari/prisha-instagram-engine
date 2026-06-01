"""
style_analyzer.py — Analyze reference style and select best template for a topic.

Selects from 5 premium templates:
  authority_card    — Dark gradient, headline, stat highlights, cards, CTA
  breaking_impact   — Bold solid bg, accent bars, row cards, big stats
  compare_contrast  — Split layout, before/after, checklist
  infographic_story — Vertical numbered steps, progress dots, summary
  social_proof      — Testimonial, stat callout, quote typography
"""

import random
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
TEMPLATES_PATH = PROJECT_ROOT / "templates" / "layout_templates.yaml"

# Template selection rules based on category + topic keywords
TEMPLATE_RULES = {
    "breaking_impact": {
        "categories": ["compliance", "tax", "compliance_updates"],
        "keywords": ["deadline", "urgent", "alert", "warning", "new rule", "update",
                     "breaking", "mandatory", "penalty", "fine", "act", "section"],
        "priority": 1,
    },
    "authority_card": {
        "categories": ["loan_subsidy", "government_schemes", "loans_subsidies",
                       "business_registration", "registration"],
        "keywords": ["loan", "subsidy", "scheme", "benefit", "apply", "eligible",
                     "lakh", "crore", "fund", "grant", "free", "registration",
                     "udyam", "gst", "fssai", "shop act", "msme"],
        "priority": 1,
    },
    "infographic_story": {
        "categories": ["certificates", "student_services", "digital_services"],
        "keywords": ["register", "certificate", "step", "guide", "how to", "process",
                     "apply", "document", "process", "aadhaar", "pan", "passport",
                     "scholarship", "csc"],
        "priority": 1,
    },
    "social_proof": {
        "categories": ["business_growth", "success_stories"],
        "keywords": ["grow", "success", "tip", "strategy", "hack", "improve",
                     "increase", "profit", "case study", "story", "result"],
        "priority": 1,
    },
    "compare_contrast": {
        "categories": ["myth_vs_reality", "compliance_updates"],
        "keywords": ["myth", "reality", "truth", "vs", "compare", "difference",
                     "without", "with", "before", "after", "mistake"],
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
        """Select the best premium template for this topic."""
        # If strategy engine specifies a valid new template, use it
        valid_new = {"authority_card", "breaking_impact", "compare_contrast",
                     "infographic_story", "social_proof"}
        if strategy_template in valid_new:
            return strategy_template
        # Also accept old names — _map_legacy_template will handle

        # Score each template for this topic
        scores = {}
        topic_lower = topic.lower()

        for template_name, rules in TEMPLATE_RULES.items():
            score = 0
            if category in rules.get("categories", []):
                score += 3
            for kw in rules.get("keywords", []):
                if kw in topic_lower:
                    score += 2
            scores[template_name] = score

        if scores:
            best = max(scores, key=scores.get)
            if scores[best] > 0:
                return best

        # Default based on category
        defaults = {
            "loan_subsidy": "authority_card",
            "loans_subsidies": "authority_card",
            "government_schemes": "authority_card",
            "business_registration": "authority_card",
            "registration": "infographic_story",
            "compliance": "breaking_impact",
            "compliance_updates": "breaking_impact",
            "tax": "breaking_impact",
            "certificates": "infographic_story",
            "student_services": "infographic_story",
            "scholarship": "infographic_story",
            "business_growth": "social_proof",
            "success_stories": "social_proof",
            "myth_vs_reality": "compare_contrast",
            "digital_services": "infographic_story",
        }
        return defaults.get(category, "authority_card")

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
        """Get the color scheme for a template (pillar-aware)."""
        colors = self.style.get("colors", {})
        template = self.templates.get(template_name, {})

        # Template-specific accent color mapping
        accent_map = {
            "breaking_impact": colors.get("accent_red", "#e63946"),
            "authority_card": colors.get("accent_green", "#06d6a0"),
            "infographic_story": colors.get("accent_blue", "#4cc9f0"),
            "social_proof": colors.get("accent_yellow", "#f4a261"),
            "compare_contrast": colors.get("accent_red", "#e85d04"),
        }

        return {
            "background_primary": colors.get("background_primary", "#0A0E11"),
            "background_secondary": colors.get("background_secondary", "#1A1A2E"),
            "text_primary": colors.get("text_primary", "#FFFFFF"),
            "text_secondary": colors.get("text_secondary", "#B0B0B0"),
            "accent": accent_map.get(template_name, colors.get("accent_blue", "#4cc9f0")),
            "accent_green": colors.get("accent_green", "#06d6a0"),
            "accent_yellow": colors.get("accent_yellow", "#FFD700"),
            "accent_red": colors.get("accent_red", "#e63946"),
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
        ("5 steps to register your business", "business_registration"),
        ("Myth: You need PAN to start business", "myth_vs_reality"),
        ("From zero to 10 lakh turnover success story", "success_stories"),
        ("How to apply for Aadhaar card online", "digital_services"),
    ]

    for topic, category in test_cases:
        template = analyzer.select_template(topic, category)
        colors = analyzer.get_color_scheme(template)
        print(f"[{category}] {topic[:55]}")
        print(f"  Template: {template}")
        print(f"  Accent: {colors['accent']}")
        print()
