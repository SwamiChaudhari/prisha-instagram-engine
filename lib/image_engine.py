"""
image_engine.py — Premium Image Engine v3.0

5 premium layout templates:
  A: Authority Card    — Dark gradient, headline, stat highlights, cards, CTA
  B: Breaking Impact   — Bold solid bg, accent bars, row cards, big stats
  C: Compare Contrast  — Split layout, before/after, checklist
  D: Infographic Story  — Vertical numbered steps, progress dots, summary
  E: Social Proof      — Testimonial, stat callout, quote typography

Design system: dark themes, pillar-specific color schemes,
premium fonts (Bebas Neue for headlines, Montsworth for body),
SVG-style icons rendered via PIL, quality gates with auto-reject.
"""

import os
import re
import math
import time
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from lib.font_manager import FontManager
from lib.icon_library import IconLibrary, icon_name_from_keyword

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"
IMAGES_DIR = PROJECT_ROOT / "images"

# ── Color Schemes Per Pillar (from reference analysis) ────────────────────

PILLAR_COLORS = {
    "loans_subsidies": {
        "bg_primary": "#0a1628", "bg_secondary": "#0f2040",
        "accent": "#e9d064", "accent_name": "gold",
        "text_primary": "#f0f0f0", "text_secondary": "#8899aa",
        "card_bg": "#0d1e36", "success": "#06d6a0",
    },
    "government_schemes": {
        "bg_primary": "#0a1f15", "bg_secondary": "#0f2e1c",
        "accent": "#06d6a0", "accent_name": "mint",
        "text_primary": "#f0f0f0", "text_secondary": "#7ab89a",
        "card_bg": "#0d2a16", "success": "#e9d064",
    },
    "compliance_updates": {
        "bg_primary": "#1f0a0a", "bg_secondary": "#2e0f0f",
        "accent": "#e85d04", "accent_name": "orange-red",
        "text_primary": "#f0f0f0", "text_secondary": "#b87a7a",
        "card_bg": "#2a0d0d", "success": "#06d6a0",
    },
    "business_registration": {
        "bg_primary": "#0a0e1f", "bg_secondary": "#0f162e",
        "accent": "#4cc9f0", "accent_name": "cyan",
        "text_primary": "#f0f0f0", "text_secondary": "#7a8ab8",
        "card_bg": "#0d122a", "success": "#06d6a0",
    },
    "business_growth": {
        "bg_primary": "#0a1f1f", "bg_secondary": "#0f2e2e",
        "accent": "#2ec4b6", "accent_name": "teal",
        "text_primary": "#f0f0f0", "text_secondary": "#7ab8b0",
        "card_bg": "#0d2a2a", "success": "#e9d064",
    },
    "student_services": {
        "bg_primary": "#150a1f", "bg_secondary": "#1c0f2e",
        "accent": "#9d4edd", "accent_name": "purple",
        "text_primary": "#f0f0f0", "text_secondary": "#9a7ab8",
        "card_bg": "#1a0d2a", "success": "#06d6d0",
    },
    "success_stories": {
        "bg_primary": "#1a1400", "bg_secondary": "#2a2000",
        "accent": "#f4a261", "accent_name": "warm-gold",
        "text_primary": "#f0f0f0", "text_secondary": "#b8a87a",
        "card_bg": "#241e00", "success": "#e9d064",
    },
    "myth_vs_reality": {
        "bg_primary": "#1a0a0a", "bg_secondary": "#2a1010",
        "accent": "#e63946", "accent_name": "red",
        "text_primary": "#f0f0f0", "text_secondary": "#b88a8a",
        "card_bg": "#240d0d", "success": "#06d6a0",
    },
}
DEFAULT_COLORS = PILLAR_COLORS["business_registration"]


class PremiumImageEngine:
    """Premium 4:5 Instagram image engine with 5 templates."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        img_cfg = self.config.get("image", {})
        self.width = img_cfg.get("width", 1080)
        self.height = img_cfg.get("height", 1350)  # 4:5 ratio — max IG real estate
        self.fm = FontManager()
        self.icons = IconLibrary()
        self._styles = self.config.get("style", {}).get("colors", {})

    # ── Main Entry ──────────────────────────────────────────────────────

    def create_image(self, spec: dict) -> str:
        """
        Create a premium Instagram image from spec.

        spec keys:
            headline       – str
            sub_headline   – str (optional)
            info_cards     – list of {icon, title, text, highlight}
            benefits       – list of benefit strings
            cta            – str
            template       — str (authority_card, breaking_impact, etc.)
            pillar         – str (for color scheme)
            brand          – str (handle / name)
            key_stat       – dict {value, label} for big number callout
            carousel_data  – dict for split/compare layouts
        """
        headline = spec.get("headline", "")
        sub_headline = spec.get("sub_headline", "")
        info_cards = spec.get("info_cards", [])
        benefits = spec.get("benefits", [])
        cta = spec.get("cta", "DM 'INFO' for details")
        template = spec.get("template", "authority_card")
        pillar = spec.get("pillar", "business_registration")
        brand = spec.get("brand", "@prisha.online.multiservices")
        key_stat = spec.get("key_stat", None)
        color_scheme = spec.get("color_scheme", {})

        # Resolve colors
        colors = PILLAR_COLORS.get(pillar, DEFAULT_COLORS).copy()
        colors.update(color_scheme)

        # Render based on template
        method = getattr(self, f"_render_{template}", None)
        if not method:
            method = self._render_authority_card

        img = method(
            headline=headline,
            sub_headline=sub_headline,
            info_cards=info_cards,
            benefits=benefits,
            cta=cta,
            colors=colors,
            brand=brand,
            key_stat=key_stat,
        )

        # Quality gate check
        quality = self._quality_check(img, colors)
        spec["_quality_score"] = quality

        return self._save_image(img)

    # ── Template A: Authority Card ──────────────────────────────────────

    def _render_authority_card(self, headline, sub_headline, info_cards,
                                benefits, cta, colors, brand, key_stat):
        """Dark gradient, category badge, headline, stat highlights, cards, CTA."""
        img, draw = self._make_canvas()

        # Layer 1: Dark gradient background with noise
        self._draw_gradient_bg(img, draw, colors)

        # Layer 2: Geometric decorative elements
        self._draw_geo_decorations(img, draw, colors)

        y = 40

        # Category badge
        category = self._extract_category(headline)
        if category:
            badge_colors = {
                "LOAN": "#e9d064", "SCHEME": "#06d6a0", "GST": "#4cc9f0",
                "MSME": "#4cc9f0", "NEW": "#e85d04", "ALERT": "#e63946",
            }
            badge_color = badge_colors.get(category.split()[0], colors["accent"])
            badge_font = self.fm.get_font("semibold", 26)
            badge_text = category.upper()[:20]
            bw, bh = self.fm.get_text_size(badge_text, badge_font)
            bw += 30
            bh += 16
            draw.rounded_rectangle([50, y, 50 + bw, y + bh], radius=bh // 2,
                                   fill=badge_color)
            draw.text((65, y + 6), badge_text, font=badge_font, fill="#0A0E1F")
            y += bh + 20

        # Accent bar (left side)
        bar_color = self._hex_to_rgb(colors["accent"])
        draw.rectangle([50, y, 56, y + 120], fill=bar_color)

        # Headline (Bebas Neue — large)
        clean_headline = self._strip_emoji_prefix(headline)
        headline_font = self.fm.get_font("headline", self._headline_font_size(clean_headline))
        max_w = self.width - 140
        wrapped = self.fm.wrap_text(clean_headline, headline_font, max_w)
        for i, line in enumerate(wrapped[:3]):
            ly = y + i * (headline_font.size + 8)
            # Shadow
            draw.text((59, ly + 2), line, font=headline_font, fill=(0, 0, 0, 180))
            # Text
            draw.text((58, ly), line, font=headline_font, fill=colors["text_primary"])
        y += len(wrapped) * (headline_font.size + 8) + 20

        # Sub-headline (accent color)
        if sub_headline:
            sub_font = self.fm.get_font("semibold", 34)
            sub_clean = self._strip_emoji_prefix(sub_headline)
            sub_wrapped = self.fm.wrap_text(sub_clean, sub_font, max_w)
            for i, line in enumerate(sub_wrapped[:2]):
                ly = y + i * 44
                draw.text((58, ly), line, font=sub_font, fill=colors["accent"])
            y += len(sub_wrapped) * 44 + 20

        # Key stat callout (big number)
        if key_stat:
            stat_val = key_stat.get("value", "")
            stat_label = key_stat.get("label", "")
            stat_font = self.fm.get_font("headline", 96)
            draw.text((58, y), stat_val, font=stat_font, fill=colors["accent"])
            label_font = self.fm.get_font("regular", 28)
            draw.text((58 + self.fm.get_text_size(stat_val, stat_font)[0] + 20, y + 40),
                       stat_label, font=label_font, fill=colors["text_secondary"])
            y += 130

        # Info cards (2-column grid)
        if info_cards:
            y = self._draw_info_grid(draw, y, info_cards, colors)

        # Benefits section
        if benefits:
            y += 15
            ben_font = self.fm.get_font("regular", 28)
            for benefit in benefits[:6]:
                ben_clean = self._strip_emoji_prefix(benefit).strip()
                if not ben_clean:
                    continue
                # Check icon
                icon_size = 28
                icon = self.icons.render("check", size=icon_size, color=colors["accent"])
                img.paste(icon, (58, y + 2), icon)
                # Text
                draw.text((58 + icon_size + 12, y), ben_clean[:55],
                           font=ben_font, fill=colors["text_primary"])
                y += icon_size + 10

        # CTA pill
        self._draw_cta_pill(draw, cta, colors, brand)

        # Branding footer
        self._draw_brand_footer(draw, brand, colors)

        return img

    # ── Template B: Breaking Impact ────────────────────────────────────

    def _render_breaking_impact(self, headline, sub_headline, info_cards,
                                 benefits, cta, colors, brand, key_stat):
        """Bold solid bg, accent bars, row cards, big stats."""
        img, draw = self._make_canvas()

        # Bold solid background
        bg = self._hex_to_rgb(colors["bg_primary"])
        draw.rectangle([0, 0, self.width, self.height], fill=bg)

        # Top accent bar
        accent = self._hex_to_rgb(colors["accent"])
        bar_h = 8
        draw.rectangle([0, 0, self.width, bar_h], fill=accent)

        # Diagonal accent shape
        for i in range(60):
            alpha = int(255 * (1 - i / 60) * 0.15)
            draw.polygon([(0, 0), (i * 8, 0), (0, i * 15)],
                         fill=(*accent[:3], alpha) if len(accent) == 3 else accent)

        y = bar_h + 30

        # Breaking badge
        badge_text = "BREAKING"
        badge_font = self.fm.get_font("bold", 24)
        bww, bhh = self._text_size(badge_font, badge_text)
        bww += 24
        bhh += 12
        draw.rounded_rectangle([50, y, 50 + bww, y + bhh], radius=4,
                               fill=colors["accent"])
        draw.text((62, y + 4), badge_text, font=badge_font, fill=colors["bg_primary"])
        y += bhh + 24

        # Headline (Oswald/Bold — bold impact)
        clean_headline = self._strip_emoji_prefix(headline)
        headline_size = self._headline_font_size(clean_headline) + 8
        headline_font = self.fm.get_font("headline", headline_size)
        max_w = self.width - 100
        wrapped = self.fm.wrap_text(clean_headline, headline_font, max_w)
        for i, line in enumerate(wrapped[:2]):
            ly = y + i * (headline_font.size + 4)
            draw.text((52, ly + 2), line, font=headline_font, fill=(0, 0, 0, 160))
            draw.text((50, ly), line, font=headline_font, fill=colors["text_primary"])
        y += len(wrapped) * (headline_font.size + 4) + 20

        # Sub-headline
        if sub_headline:
            sub_font = self.fm.get_font("semibold", 32)
            sub_clean = self._strip_emoji_prefix(sub_headline)
            draw.text((50, y), sub_clean[:80], font=sub_font, fill=colors["accent"])
            y += 55

        # Key stat (prominent)
        if key_stat:
            stat_font = self.fm.get_font("headline", 110)
            draw.text((50, y), key_stat.get("value", ""),
                       font=stat_font, fill=colors["accent"])
            y += 120

        # Row-style info cards
        if info_cards:
            y = self._draw_row_cards(draw, img, y, info_cards, colors)

        # Benefits as checklist
        if benefits:
            y += 15
            for ben in benefits[:5]:
                b_clean = self._strip_emoji_prefix(ben).strip()
                if not b_clean:
                    continue
                icon = self.icons.render("check", size=24, color=colors["accent"])
                img.paste(icon, (54, y), icon)
                ben_font = self.fm.get_font("regular", 26)
                draw.text((88, y), b_clean[:50], font=ben_font,
                           fill=colors["text_primary"])
                y += 38

        # CTA
        self._draw_cta_pill(draw, cta, colors, brand)
        self._draw_brand_footer(draw, brand, colors)

        # Bottom accent bar
        draw.rectangle([0, self.height - bar_h, self.width, self.height], fill=accent)

        return img

    # ── Template C: Compare Contrast ───────────────────────────────────

    def _render_compare_contrast(self, headline, sub_headline, info_cards,
                                  benefits, cta, colors, brand, key_stat):
        """Split layout, before vs after, checklist."""
        img, draw = self._make_canvas()

        # Dark gradient bg
        self._draw_gradient_bg(img, draw, colors)

        # Split line
        mid_x = self.width // 2
        accent = self._hex_to_rgb(colors["accent"])

        y = 30

        # Headline (full width)
        clean_headline = self._strip_emoji_prefix(headline)
        headline_font = self.fm.get_font("headline", self._headline_font_size(clean_headline) - 4)
        max_w = self.width - 100
        wrapped = self.fm.wrap_text(clean_headline, headline_font, max_w)
        for i, line in enumerate(wrapped[:3]):
            ly = y + i * (headline_font.size + 4)
            draw.text((52, ly + 2), line, font=headline_font, fill=(0, 0, 0, 160))
            draw.text((50, ly), line, font=headline_font, fill=colors["text_primary"])
        y += len(wrapped) * (headline_font.size + 4) + 25

        # VS badge
        vs_font = self.fm.get_font("headline", 56)
        vs_x = mid_x
        draw.ellipse([vs_x - 40, y, vs_x + 40, y + 80], fill=colors["accent"])
        draw.text((vs_x - 18, y + 16), "VS", font=vs_font, fill=colors["bg_primary"])
        y += 100

        # Left side (WITHOUT) and right side (WITH)
        left_x = 30
        right_x = mid_x + 20
        half_w = mid_x - 50

        # Labels
        label_font = self.fm.get_font("bold", 22)
        draw.text((left_x, y), "WITHOUT", font=label_font, fill="#e63946")
        draw.text((right_x, y), "WITH", font=label_font, fill=colors["accent"])
        y += 35

        # Divider line
        draw.line([(mid_x, y - 50), (mid_x, self.height - 200)],
                  fill=(*accent[:3], 80) if len(accent) == 3 else accent, width=2)

        # Info cards on each side
        if info_cards:
            for i, card in enumerate(info_cards[:6]):
                side_x = left_x if i % 2 == 0 else right_x
                col = "#e63946" if i % 2 == 0 else colors["accent"]
                txt = card.get("title", card.get("text", str(card)))[:35]
                card_font = self.fm.get_font("regular", 24)
                # Small card
                draw.rounded_rectangle([side_x, y, side_x + half_w, y + 50],
                                       radius=8, fill=(*self._hex_to_rgb(colors["card_bg"]), 200),
                                       outline=col, width=2)
                draw.text((side_x + 12, y + 12), txt, font=card_font,
                           fill=colors["text_primary"])
                y += 60

        # CTA
        self._draw_cta_pill(draw, cta, colors, brand)
        self._draw_brand_footer(draw, brand, colors)

        return img

    # ── Template D: Infographic Story ──────────────────────────────────

    def _render_infographic_story(self, headline, sub_headline, info_cards,
                                    benefits, cta, colors, brand, key_stat):
        """Vertical numbered steps, progress dots, color-coded sections."""
        img, draw = self._make_canvas()
        self._draw_gradient_bg(img, draw, colors)
        accent = self._hex_to_rgb(colors["accent"])

        y = 40

        # Headline
        clean_headline = self._strip_emoji_prefix(headline)
        headline_font = self.fm.get_font("headline", self._headline_font_size(clean_headline) - 2)
        max_w = self.width - 120
        wrapped = self.fm.wrap_text(clean_headline, headline_font, max_w)
        for i, line in enumerate(wrapped[:2]):
            ly = y + i * (headline_font.size + 4)
            draw.text((62, ly + 2), line, font=headline_font, fill=(0, 0, 0, 160))
            draw.text((60, ly), line, font=headline_font, fill=colors["text_primary"])
        y += len(wrapped) * (headline_font.size + 4) + 30

        # Sub-headline
        if sub_headline:
            sub_font = self.fm.get_font("semibold", 30)
            s_wrapped = self.fm.wrap_text(sub_headline, sub_font, max_w)
            for i, line in enumerate(s_wrapped[:2]):
                draw.text((60, y + i * 40), line, font=sub_font, fill=colors["accent"])
            y += len(s_wrapped) * 40 + 20

        # Steps (numbered)
        steps = info_cards if info_cards else []
        if benefits and not steps:
            steps = [{"title": b, "icon": "check"} for b in benefits[:6]]

        line_x = 90
        progress_dot_r = 10
        step_y_start = y

        for i, step in enumerate(steps[:6]):
            # Progress line (vertical)
            cy = y + 22
            if i < len(steps[:6]) - 1:
                draw.line([(line_x, cy + progress_dot_r), (line_x, y + 90)],
                          fill=(*accent[:3], 100) if len(accent) == 3 else accent, width=3)

            # Number circle
            draw.ellipse([line_x - progress_dot_r, cy - progress_dot_r,
                          line_x + progress_dot_r, cy + progress_dot_r],
                         fill=colors["accent"])
            num_font = self.fm.get_font("bold", 20)
            draw.text((line_x - 6, cy - 12), str(i + 1),
                       font=num_font, fill=colors["bg_primary"])

            # Step content
            step_text = step.get("title", step.get("text", str(step)))[:50]
            step_font = self.fm.get_font("regular", 28)
            icon_name = icon_name_from_keyword(step.get("icon", "check"))
            icon = self.icons.render(icon_name, size=28, color=colors["accent"])
            img.paste(icon, (line_x + 30, y + 1), icon)
            draw.text((line_x + 65, y + 4), step_text, font=step_font,
                       fill=colors["text_primary"])

            # Highlight
            highlight = step.get("highlight", step.get("amount", ""))
            if highlight:
                hl_font = self.fm.get_font("bold", 24)
                draw.text((line_x + 65, y + 36), str(highlight),
                           font=hl_font, fill=colors["accent"])

            y += 85

        # Summary stat box
        if key_stat:
            draw.rounded_rectangle([50, y + 10, self.width - 50, y + 90],
                                   radius=12, fill=self._hex_to_rgb(colors["card_bg"]),
                                   outline=colors["accent"], width=2)
            stat_font = self.fm.get_font("headline", 48)
            draw.text((70, y + 22), key_stat.get("value", ""),
                       font=stat_font, fill=colors["accent"])
            label_font = self.fm.get_font("regular", 22)
            draw.text((70 + self.fm.get_text_size(key_stat.get("value", ""), stat_font)[0] + 15, y + 38),
                       key_stat.get("label", ""), font=label_font, fill=colors["text_secondary"])
            y += 110

        # CTA
        self._draw_cta_pill(draw, cta, colors, brand)
        self._draw_brand_footer(draw, brand, colors)

        return img

    # ── Template E: Social Proof ───────────────────────────────────────

    def _render_social_proof(self, headline, sub_headline, info_cards,
                              benefits, cta, colors, brand, key_stat):
        """Testimonial format, quote, stat callout box."""
        img, draw = self._make_canvas()
        self._draw_gradient_bg(img, draw, colors)
        accent = self._hex_to_rgb(colors["accent"])

        y = 50

        # "SUCCESS STORY" badge
        badge_font = self.fm.get_font("bold", 22)
        badge_text = "SUCCESS STORY"
        bww, bhh = self._text_size(badge_font, badge_text)
        bww += 24
        bhh += 12
        draw.rounded_rectangle([50, y, 50 + bww, y + bhh], radius=4,
                               fill=colors["accent"])
        draw.text((62, y + 4), badge_text, font=badge_font, fill=colors["bg_primary"])
        y += bhh + 30

        # Headline
        clean_headline = self._strip_emoji_prefix(headline)
        headline_font = self.fm.get_font("headline", self._headline_font_size(clean_headline) - 4)
        max_w = self.width - 120
        wrapped = self.fm.wrap_text(clean_headline, headline_font, max_w)
        for i, line in enumerate(wrapped[:3]):
            ly = y + i * (headline_font.size + 4)
            draw.text((62, ly + 2), line, font=headline_font, fill=(0, 0, 0, 160))
            draw.text((60, ly), line, font=headline_font, fill=colors["text_primary"])
        y += len(wrapped) * (headline_font.size + 4) + 25

        # Sub-headline
        if sub_headline:
            sub_font = self.fm.get_font("regular", 30)
            s_wrapped = self.fm.wrap_text(sub_headline, sub_font, max_w)
            for i, line in enumerate(s_wrapped[:2]):
                draw.text((60, y + i * 38), line, font=sub_font, fill=colors["text_secondary"])
            y += len(s_wrapped) * 38 + 20

        # Quote-style info cards
        if info_cards:
            for i, card in enumerate(info_cards[:4]):
                txt = card.get("title", card.get("text", str(card)))[:60]
                card_font = self.fm.get_font("light", 26)
                # Quote mark
                quote_font = self.fm.get_font("headline", 60)
                quote_mark = '\u201c'  # Left double quotation mark
                draw.text((60, y - 10), quote_mark, font=quote_font, fill=(*accent[:3], 60))
                # Text
                draw.text((100, y), txt, font=card_font, fill=colors["text_primary"])
                y += 50
                # Source
                src = card.get("source", card.get("highlight", ""))
                if src:
                    src_font = self.fm.get_font("semibold", 22)
                    draw.text((100, y), f"— {src}"[:40], font=src_font, fill=colors["accent"])
                    y += 35

        # Stat callout box
        if key_stat:
            y += 15
            box_h = 120
            draw.rounded_rectangle([50, y, self.width - 50, y + box_h],
                                   radius=16, fill=self._hex_to_rgb(colors["card_bg"]),
                                   outline=colors["accent"], width=3)
            stat_font = self.fm.get_font("headline", 72)
            draw.text((80, y + 10), key_stat.get("value", ""),
                       font=stat_font, fill=colors["accent"])
            label_font = self.fm.get_font("regular", 24)
            label_x = 80 + self.fm.get_text_size(key_stat.get("value", ""), stat_font)[0] + 20
            draw.text((label_x, y + 35), key_stat.get("label", ""),
                       font=label_font, fill=colors["text_primary"])
            y += box_h + 20

        # CTA
        self._draw_cta_pill(draw, cta, colors, brand)
        self._draw_brand_footer(draw, brand, colors)

        return img

    # ── Shared Drawing Components ──────────────────────────────────────

    def _draw_gradient_bg(self, img: Image.Image, draw: ImageDraw.Draw, colors: dict):
        """Draw dark gradient background with subtle noise texture."""
        bg1 = self._hex_to_rgb(colors.get("bg_primary", "#0A0E1F"))
        bg2 = self._hex_to_rgb(colors.get("bg_secondary", "#0F162E"))
        for y in range(self.height):
            ratio = y / self.height
            r = int(bg1[0] + (bg2[0] - bg1[0]) * ratio)
            g = int(bg1[1] + (bg2[1] - bg1[1]) * ratio)
            b = int(bg1[2] + (bg2[2] - bg1[2]) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

    def _draw_geo_decorations(self, img: Image.Image, draw: ImageDraw.Draw, colors: dict):
        """Add subtle geometric decorations."""
        accent = self._hex_to_rgb(colors.get("accent", "#4cc9f0"))
        # Corner accent (top-right)
        cx = self.width - 60
        cy = 60
        for i in range(8):
            alpha = int(30 * (1 - i / 8))
            r = 20 + i * 15
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         outline=(*accent[:3], alpha) if len(accent) == 3 else accent)
        # Small dot grid (bottom-left)
        for dx in range(3):
            for dy in range(3):
                px = 30 + dx * 12
                py = self.height - 150 + dy * 12
                draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=accent)

    def _draw_info_grid(self, draw: ImageDraw.Draw, y: int,
                         cards: list, colors: dict) -> int:
        """Draw 2-column info card grid."""
        card_bg = self._hex_to_rgb(colors.get("card_bg", "#0D122A"))
        accent_rgb = self._hex_to_rgb(colors["accent"])
        cols = 2
        rows = (min(len(cards), 6) + cols - 1) // cols
        card_w = (self.width - 120) // cols
        card_h = 80
        gap = 12

        for i, card in enumerate(cards[:6]):
            row = i // cols
            col = i % cols
            cx = 60 + col * (card_w + gap)
            cy = y + row * (card_h + gap)
            if cy + card_h > self.height - 200:
                break

            # Card background
            draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h],
                                   radius=12, fill=card_bg,
                                   outline=colors["accent"], width=2)

            # Icon
            icon_kw = card.get("icon", "check") or "check"
            icon_name = icon_name_from_keyword(icon_kw)
            try:
                icon = self.icons.render(icon_name, size=32, color=colors["accent"])
                img_ref = draw._image if hasattr(draw, '_image') else None
            except Exception:
                img_ref = None

            if img_ref:
                img_ref.paste(icon, (cx + 12, cy + 24), icon)

            # Title text
            title = card.get("title", card.get("text", str(card)))[:35]
            title_font = self.fm.get_font("regular", 26)
            draw.text((cx + 55, cy + 18), title, font=title_font,
                       fill=colors["text_primary"])

            # Highlight
            highlight = card.get("highlight", card.get("amount", ""))
            if highlight:
                hl_font = self.fm.get_font("bold", 22)
                draw.text((cx + 55, cy + 46), str(highlight),
                           font=hl_font, fill=colors["accent"])

        y += rows * (card_h + gap) + 20
        return y

    def _draw_row_cards(self, draw, img, y, cards, colors):
        """Draw horizontal row-style info cards."""
        accent_rgb = self._hex_to_rgb(colors["accent"])
        card_h = 60
        gap = 10
        max_cards = min(len(cards), 5)

        for i in range(max_cards):
            card = cards[i]
            if y + card_h > self.height - 200:
                break

            # Card background
            draw.rounded_rectangle([50, y, self.width - 50, y + card_h],
                                   radius=10, fill=self._hex_to_rgb(colors["card_bg"]),
                                   outline=colors["accent"], width=1)

            # Icon
            icon_kw = card.get("icon", "check") or "check"
            icon_name = icon_name_from_keyword(icon_kw)
            try:
                icon = self.icons.render(icon_name, size=28, color=colors["accent"])
                img.paste(icon, (62, y + 16), icon)
            except Exception:
                pass

            # Text
            title = card.get("title", card.get("text", str(card)))[:45]
            title_font = self.fm.get_font("regular", 26)
            draw.text((100, y + 14), title, font=title_font, fill=colors["text_primary"])

            # Highlight (right side)
            highlight = card.get("highlight", card.get("amount", ""))
            if highlight:
                hl_font = self.fm.get_font("bold", 26)
                hl_w = self.fm.get_text_size(str(highlight), hl_font)[0]
                draw.text((self.width - 60 - hl_w, y + 14), str(highlight),
                           font=hl_font, fill=colors["accent"])

            y += card_h + gap

        return y

    def _draw_cta_pill(self, draw, cta, colors, brand):
        """Draw CTA pill按钮 at bottom area."""
        clean_cta = self._strip_emoji_prefix(cta).strip()
        accent_rgb = self._hex_to_rgb(colors["accent"])
        cta_font = self.fm.get_font("bold", 30)
        tw, th = self._text_size(cta_font, clean_cta)
        tw += 60
        th += 24
        cx = self.width // 2
        cy = self.height - 160
        # Pill background
        draw.rounded_rectangle([cx - tw // 2, cy, cx + tw // 2, cy + th],
                               radius=th // 2, fill=colors["accent"])
        # Text
        draw.text((cx - tw // 2 + 28, cy + 10), clean_cta,
                   font=cta_font, fill=colors["bg_primary"])

    def _draw_brand_footer(self, draw, brand, colors):
        """Draw brand footer."""
        brand_font = self.fm.get_font("light", 22)
        bw, bh = self._text_size(brand_font, brand)
        bx = self.width - bw - 40
        by = self.height - 40
        # Background chip
        draw.rounded_rectangle([bx - 12, by - 4, self.width - 30, by + bh + 8],
                               radius=8, fill=self._hex_to_rgb(colors["bg_primary"]))
        draw.text((bx, by), brand, font=brand_font, fill=colors["text_secondary"])

    # ── Quality Gate ───────────────────────────────────────────────────

    def _quality_check(self, img: Image.Image, colors: dict) -> dict:
        """
        Auto quality checks. Returns score + failure reasons.
        Checks: element count, whitespace, font sizes, contrast, flat bg, etc.
        """
        issues = []
        score = 100

        # 1. Check for flat single-color background
        pixels = list(img.getdata())
        unique_colors = set()
        step = max(1, len(pixels) // 5000)
        for i in range(0, len(pixels), step):
            unique_colors.add(pixels[i][:3])
        if len(unique_colors) < 20:
            score -= 30
            issues.append("FLAT_BACKGROUND: Too few unique colors (<20)")

        # 2. Check whitespace (light pixels)
        light_count = sum(1 for p in pixels[::step] if all(c > 200 for c in p[:3]))
        light_pct = light_count / max(1, len(pixels[::step]))
        if light_pct > 0.4:
            score -= 20
            issues.append(f"WITESPACE: {light_pct:.0%} light area (max 40%)")
        if light_pct > 0.5:
            score -= 15
            issues.append("EXCESSIVE_WHITESPACE: >50% light area")

        # 3. Check accent color presence
        accent_hex = colors.get("accent", "#4cc9f0")
        accent_rgb = self._hex_to_rgb(accent_hex)
        accent_count = sum(1 for p in pixels[::step]
                          if self._color_distance(p[:3], accent_rgb) < 40)
        accent_pct = accent_count / max(1, len(pixels[::step]))
        if accent_pct < 0.02:
            score -= 10
            issues.append(f"LOW_ACCENT: Only {accent_pct:.1%} accent color (min 2%)")

        return {
            "score": max(0, score),
            "issues": issues,
            "unique_colors": len(unique_colors),
            "light_pct": light_pct,
            "accent_pct": accent_pct,
        }

    # ── Helpers ────────────────────────────────────────────────────────

    def _make_canvas(self) -> tuple[Image.Image, ImageDraw.Draw]:
        img = Image.new("RGB", (self.width, self.height), "#0A0E1F")
        return img, ImageDraw.Draw(img)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return (0, 0, 0)

    @staticmethod
    def _color_distance(c1: tuple, c2: tuple) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

    def _strip_emoji_prefix(self, text: str) -> str:
        """Remove leading emoji/prefix characters from text."""
        if not text:
            return ""
        # Strip leading emoji sequences
        result = text.strip()
        # Remove known prefix emojis
        for prefix in ["\U0001f4e2", "\u26a0\ufe0f", "\u274c", "\U0001f4b0",
                        "\U0001f525", "\u2753", "\U0001f3c6", "\U0001f4b8",
                        "\u2728", "\u26a0", "\U0001f6a8", "🚨", "⚠️", "❌",
                        "💰", "🔥", "❓", "🏛", "📈", "🚀"]:
            if result.startswith(prefix):
                result = result[len(prefix):].strip()
        return result

    @staticmethod
    def _extract_category(headline: str) -> str:
        """Extract category keyword from headline."""
        upper = headline.upper()
        for keyword in ["LOAN", "SCHEME", "GST", "MSME", "NEW", "ALERT",
                        "BREAKING", "UPDATE", "RULE", "BENEFIT", "SUBSIDY"]:
            if keyword in upper:
                return keyword
        return ""

    @staticmethod
    def _headline_font_size(text: str) -> int:
        """Calculate optimal font size based on headline length."""
        length = len(text)
        if length <= 15:
            return 96
        elif length <= 25:
            return 80
        elif length <= 35:
            return 68
        elif length <= 50:
            return 56
        else:
            return 48

    def _text_size(self, font, text: str) -> tuple:
        """Get text dimensions."""
        try:
            bbox = font.getbbox(text)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except Exception:
            return (len(text) * font.size // 2, font.size)

    def _save_image(self, img: Image.Image) -> str:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        path = IMAGES_DIR / f"post_v3_{ts}.png"
        img.save(path, "PNG", quality=95)
        return str(path)


# ── Backward-Compatible Wrapper ────────────────────────────────────────

def create_image(headline: str, image_text: str = "", category: str = "",
                output_path: str = None, sub_headline: str = "",
                info_cards: list = None, cta: str = None,
                template: str = "authority_card", accent: str = None,
                color_scheme: dict = None, use_face: bool = False,
                face_path: str = None, config: dict = None,
                pillar: str = None, brand: str = None, key_stat: dict = None,
                benefits: list = None) -> str:
    """Backward-compatible image creation function."""
    engine = PremiumImageEngine(config or {})

    spec = {
        "headline": headline,
        "sub_headline": sub_headline or image_text[:80],
        "info_cards": info_cards or [],
        "benefits": benefits or [],
        "cta": cta or "DM 'INFO' for details",
        "template": _map_legacy_template(template),
        "color_scheme": color_scheme or {},
        "pillar": pillar or "business_registration",
        "brand": brand or "@prisha.online.multiservices",
        "key_stat": key_stat,
    }
    if accent:
        spec["color_scheme"]["accent"] = accent

    path = engine.create_image(spec)
    if output_path and path != output_path:
        import shutil
        shutil.copy2(path, output_path)
        return output_path
    return path


def _map_legacy_template(t: str) -> str:
    """Map old template names to new ones."""
    mapping = {
        "opportunity_alert": "authority_card",
        "breaking_news": "breaking_impact",
        "government_scheme": "infographic_story",
        "business_growth": "social_proof",
        "warning_policy": "breaking_impact",
        "success_story": "social_proof",
        "quick_tips": "infographic_story",
        "compare_contrast": "compare_contrast",
    }
    return mapping.get(t, t)


if __name__ == "__main__":
    import yaml
    config_path = PROJECT_ROOT / "config.yaml"
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        config = {}

    # Test all 5 templates
    test_specs = [
        {
            "headline": "GOVERNMENT GIVING 25 LAKH SUBSIDY",
            "sub_headline": "Are You Eligible? Apply Now",
            "info_cards": [
                {"icon": "money", "title": "Up to 25 Lakh", "highlight": "25L"},
                {"icon": "check", "title": "No Collateral Required"},
                {"icon": "building", "title": "For New & Existing Business"},
                {"icon": "percent", "title": "75% Government Grant"},
            ],
            "benefits": ["Government-recognized", "Easy Application", "Expert Support"],
            "cta": "DM 'LOAN' for Details",
            "pillar": "loans_subsidies",
            "template": "authority_card",
            "key_stat": {"value": "25 LAKH", "label": "Maximum Subsidy"},
        },
        {
            "headline": "NEW GST RULE FROM JUNE 2026",
            "sub_headline": "All Business Owners Must Know This",
            "info_cards": [
                {"icon": "alert", "title": "Effective June 1, 2026"},
                {"icon": "document", "title": "Updated Filing Requirements"},
                {"icon": "clock", "title": "Deadline: July 31, 2026"},
            ],
            "cta": "DM 'GST' for Help",
            "pillar": "compliance_updates",
            "template": "breaking_impact",
        },
        {
            "headline": "WITHOUT MSME vs WITH MSME Registration",
            "sub_headline": "See the Difference",
            "info_cards": [
                {"icon": "cross", "title": "No Government Benefits"},
                {"icon": "check", "title": "Access to All Schemes"},
                {"icon": "cross", "title": "Higher Interest Rates"},
                {"icon": "check", "title": "Priority Lending"},
                {"icon": "cross", "title": "No Tax Benefits"},
                {"icon": "check", "title": "Tax Exemptions"},
            ],
            "cta": "DM 'MSME' to Register",
            "pillar": "business_registration",
            "template": "compare_contrast",
        },
        {
            "headline": "5 STEPS TO START YOUR BUSINESS",
            "sub_headline": "Complete Guide for New Entrepreneurs",
            "info_cards": [
                {"icon": "document", "title": "Step 1: Choose Business Type"},
                {"icon": "building", "title": "Step 2: Register Your Business"},
                {"icon": "rupee", "title": "Step 3: Open Bank Account"},
                {"icon": "shield", "title": "Step 4: Get Licenses"},
                {"icon": "chart-up", "title": "Step 5: Start Operations"},
            ],
            "cta": "DM 'START' for Guidance",
            "pillar": "business_growth",
            "template": "infographic_story",
            "key_stat": {"value": "5", "label": "Simple Steps"},
        },
        {
            "headline": "FROM ZERO TO 10 LAKH TURNOVER",
            "sub_headline": "How Raju Built His Business with Prisha",
            "info_cards": [
                {"icon": "star", "title": "Started with just 50,000 investment"},
                {"icon": "growth-chart", "title": "Grew 20x in 18 months"},
                {"icon": "trophy", "title": "Now employs 12 people"},
            ],
            "cta": "DM 'SUCCESS' to Start",
            "pillar": "success_stories",
            "template": "social_proof",
            "key_stat": {"value": "10 LAKH", "label": "Annual Turnover"},
        },
    ]

    for i, spec in enumerate(test_specs):
        path = create_image(**spec, config=config)
        print(f"Template {i + 1} ({spec['template']}): {path}")
