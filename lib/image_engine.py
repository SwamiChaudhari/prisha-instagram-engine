"""
image_engine.py — Hybrid News Card Engine v2.0

Generates Instagram images using layered composition:
1. Background (gradient or AI-generated scene)
2. Face/subject (user photo or placeholder)
3. Visual elements (icons, decorative elements)
4. Headline (rendered with precise typography)
5. Info cards (structured data blocks)
6. CTA (call to action)
7. Branding (logo, watermark, handle)

This engine works WITHOUT AI image generation.
When AI provider is available, layer 1 (background) and layer 2 (face)
can be replaced with AI-generated content.
"""

import os
import re
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"
IMAGES_DIR = PROJECT_ROOT / "images"

# Fallback font paths (system fonts)
FONT_PATHS = {
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ],
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ],
}


def _find_font(style: str = "bold", size: int = 48) -> ImageFont.FreeTypeFont:
    """Find an available font."""
    for path in FONT_PATHS.get(style, FONT_PATHS["bold"]):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


class HybridImageEngine:
    """Generate professional news-style Instagram images."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.width = self.config.get("image", {}).get("width", 1080)
        self.height = self.config.get("image", {}).get("height", 1080)
        self.colors = self.config.get("style", {}).get("colors", {})

    def create_image(self, spec: dict) -> str:
        """
        Create a complete Instagram image from a specification.

        spec keys:
            - headline: str
            - sub_headline: str (optional)
            - info_cards: list of dicts with {icon, title, text, highlight}
            - cta: str
            - template: str (breaking_news, opportunity_alert, etc.)
            - color_scheme: dict with color overrides
            - face_path: str (optional, path to face image)
            - accent: str (hex color for accents)

        Returns: path to saved image
        """
        # Extract spec
        headline = spec.get("headline", "")
        sub_headline = spec.get("sub_headline", "")
        info_cards = spec.get("info_cards", [])
        cta = spec.get("cta", "📩 DM 'INFO'")
        template = spec.get("template", "opportunity_alert")
        color_scheme = spec.get("color_scheme", {})
        accent = spec.get("accent", "#4A90D9")
        face_path = spec.get("face_path", None)

        # ── Layer 1: Background ─────────────────────────────────────────────
        img = self._create_background(color_scheme, template)

        # ── Layer 2: Face/Subject (optional) ────────────────────────────────
        if face_path and os.path.exists(face_path):
            img = self._overlay_face(img, face_path, template)
        elif spec.get("use_face") and not face_path:
            # Use a stylized face placeholder (geometric avatar)
            img = self._create_face_placeholder(img, template, accent)

        # ── Layer 3: Visual elements (decorative) ──────────────────────────
        img = self._add_visual_elements(img, template, accent)

        # ── Layer 4: Headline ───────────────────────────────────────────────
        img = self._render_headline(img, headline, sub_headline, color_scheme, accent, template)

        # ── Layer 5: Info cards ─────────────────────────────────────────────
        if info_cards:
            img = self._render_info_cards(img, info_cards, color_scheme, accent, template)

        # ── Layer 6: CTA ────────────────────────────────────────────────────
        img = self._render_cta(img, cta, color_scheme, accent, template)

        # ── Layer 7: Branding ───────────────────────────────────────────────
        img = self._render_branding(img, color_scheme)

        # Save
        return self._save_image(img)

    # ── Layer 1: Background ─────────────────────────────────────────────────

    def _create_background(self, colors: dict, template: str) -> Image.Image:
        """Create dark gradient background."""
        img = Image.new("RGB", (self.width, self.height), colors.get("background_primary", "#0A0E11"))
        draw = ImageDraw.Draw(img)

        # Create gradient effect
        bg_primary = self._hex_to_rgb(colors.get("background_primary", "#0A0E11"))
        bg_secondary = self._hex_to_rgb(colors.get("background_secondary", "#1A1A2E"))

        for y in range(self.height):
            ratio = y / self.height
            r = int(bg_primary[0] + (bg_secondary[0] - bg_primary[0]) * ratio)
            g = int(bg_primary[1] + (bg_secondary[1] - bg_primary[1]) * ratio)
            b = int(bg_primary[2] + (bg_secondary[2] - bg_primary[2]) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Add subtle vignette
        self._add_vignette(img)

        # Add subtle accent glow at top
        accent = colors.get("accent", "#4A90D9")
        accent_rgb = self._hex_to_rgb(accent)
        for y in range(200):
            alpha = int(30 * (1 - y / 200))
            overlay = Image.new("RGB", (self.width, 1), (
                min(255, accent_rgb[0] + bg_primary[0]) // 2,
                min(255, accent_rgb[1] + bg_primary[1]) // 2,
                min(255, accent_rgb[2] + bg_primary[2]) // 2,
            ))
            img.paste(overlay, (0, y))

        return img

    def _add_vignette(self, img: Image.Image):
        """Add subtle dark vignette around edges."""
        vignette = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(vignette)
        for i in range(min(img.width, img.height) // 2, 0, -1):
            alpha = int(255 * (i / (min(img.width, img.height) // 2)))
            draw.ellipse(
                [img.width // 2 - i, img.height // 2 - i,
                 img.width // 2 + i, img.height // 2 + i],
                fill=alpha,
            )
        # Blend vignette subtly
        pass  # Vignette is complex; skip for v1, gradient is enough

    # ── Layer 2: Face/Subject ───────────────────────────────────────────────

    def _overlay_face(self, img: Image.Image, face_path: str, template: str) -> Image.Image:
        """Overlay user's photo on the image."""
        try:
            face = Image.open(face_path).convert("RGBA")
            # Resize face to ~30% of image width
            face_w = int(self.width * 0.30)
            face_h = int(face.height * (face_w / face.width))
            face = face.resize((face_w, face_h), Image.Resampling.LANCZOS)

            # Position: right side, vertically centered in top 60%
            x = self.width - face_w - 40
            y = int(self.height * 0.15)

            # Create circular mask
            mask = Image.new("L", (face_w, face_h), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse([0, 0, face_w, face_h], fill=255)

            # Apply circular crop
            face_cropped = Image.new("RGBA", (face_w, face_h), (0, 0, 0, 0))
            face_cropped.paste(face, (0, 0), mask)

            # Paste onto main image
            img.paste(face_cropped, (x, y), face_cropped)
        except Exception:
            pass
        return img

    def _create_face_placeholder(self, img: Image.Image, template: str, accent: str) -> Image.Image:
        """Create a stylized face placeholder (geometric avatar) when no photo available."""
        draw = ImageDraw.Draw(img)
        accent_rgb = self._hex_to_rgb(accent)

        # Draw a circle placeholder on the right side
        cx = self.width - 180
        cy = 280
        radius = 120

        # Glow effect
        for i in range(10, 0, -1):
            glow_alpha = int(20 * (10 - i))
            glow_color = (
                min(255, accent_rgb[0] + 50),
                min(255, accent_rgb[1] + 50),
                min(255, accent_rgb[2] + 50),
            )
            draw.ellipse(
                [cx - radius - i, cy - radius - i, cx + radius + i, cy + radius + i],
                fill=glow_color,
            )

        # Main circle
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(40, 40, 50),
            outline=accent_rgb,
            width=4,
        )

        # Simple face icon (geometric)
        eye_y = cy - 20
        draw.ellipse([cx - 40, eye_y - 8, cx - 20, eye_y + 8], fill=accent_rgb)
        draw.ellipse([cx + 20, eye_y - 8, cx + 40, eye_y + 8], fill=accent_rgb)
        draw.arc([cx - 30, cy + 10, cx + 30, cy + 40], start=0, end=180, fill=accent_rgb, width=3)

        return img

    # ── Layer 3: Visual Elements ────────────────────────────────────────────

    def _add_visual_elements(self, img: Image.Image, template: str, accent: str) -> Image.Image:
        """Add decorative visual elements."""
        draw = ImageDraw.Draw(img)
        accent_rgb = self._hex_to_rgb(accent)

        # Top accent bar
        draw.rectangle([0, 0, self.width, 6], fill=accent_rgb)

        # Bottom accent bar
        draw.rectangle([0, self.height - 4, self.width, self.height], fill=accent_rgb)

        # Side accent lines
        draw.rectangle([0, 100, 4, 400], fill=accent_rgb)
        draw.rectangle([self.width - 4, 100, self.width, 400], fill=accent_rgb)

        # Template-specific decorative elements
        if template == "opportunity_alert":
            # Money scatter (small circles)
            for pos in [(80, 500), (150, 700), (950, 450), (1000, 650)]:
                draw.ellipse([pos[0] - 8, pos[1] - 8, pos[0] + 8, pos[1] + 8],
                           fill=(*accent_rgb, 100))

        return img

    # ── Layer 4: Headline ───────────────────────────────────────────────────

    def _render_headline(self, img: Image.Image, headline: str, sub_headline: str,
                        colors: dict, accent: str, template: str) -> Image.Image:
        """Render the headline with precise typography."""
        draw = ImageDraw.Draw(img)
        text_color = colors.get("text_primary", "#FFFFFF")
        accent_rgb = self._hex_to_rgb(accent)

        # Main headline — large, bold, top 20% of image
        # Strip emoji prefix for sizing, then render with emoji
        clean_headline = re.sub(r'[^\w\s\?\:\-\,\.\(\)]', '', headline).strip()
        emoji = ""
        for ch in headline:
            if ord(ch) > 127:
                emoji = ch + " "
                break

        # Calculate font size based on headline length
        headline_len = len(clean_headline)
        if headline_len <= 20:
            font_size = 80
        elif headline_len <= 35:
            font_size = 64
        elif headline_len <= 50:
            font_size = 52
        else:
            font_size = 44

        headline_font = _find_font("bold", font_size)

        # Word wrap the headline
        max_width = self.width - 120  # 60px padding each side
        wrapped = self._wrap_text(clean_headline, headline_font, max_width)

        # Render headline lines
        y_start = 60
        line_spacing = int(font_size * 1.1)

        for i, line in enumerate(wrapped[:3]):  # Max 3 lines
            y = y_start + i * line_spacing

            # Draw text shadow
            draw.text((62, y + 2), line, font=headline_font, fill=(0, 0, 0))
            # Draw main text
            x_offset = 60 if i == 0 and emoji else 60
            full_line = (emoji + line) if i == 0 and emoji else line
            draw.text((x_offset, y), full_line, font=headline_font, fill=text_color)

        # Sub-headline (smaller, accent color)
        if sub_headline:
            sub_font = _find_font("regular", 32)
            y_sub = y_start + len(wrapped) * line_spacing + 20
            draw.text((60, y_sub), sub_headline, font=sub_font, fill=accent_rgb)

        return img

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            try:
                bbox = font.getbbox(test_line)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w = len(test_line) * (font.size // 2)

            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" " .join(current_line))

        return lines if lines else [text]

    # ── Layer 5: Info Cards ─────────────────────────────────────────────────

    def _render_info_cards(self, img: Image.Image, cards: list, colors: dict,
                          accent: str, template: str) -> Image.Image:
        """Render information cards with icons."""
        draw = ImageDraw.Draw(img)
        accent_rgb = self._hex_to_rgb(accent)
        text_color = colors.get("text_primary", "#FFFFFF")
        text_secondary = colors.get("text_secondary", "#B0B0B0")

        # Position: bottom 35% of image
        card_area_top = int(self.height * 0.60)
        card_area_bottom = int(self.height * 0.88)
        available_height = card_area_bottom - card_area_top

        # Calculate card layout
        num_cards = min(len(cards), 6)
        if num_cards == 0:
            return img

        # Cards per row (2 columns for 4+ cards, 1 column for 3- cards)
        cols = 2 if num_cards >= 4 else 1
        rows = (num_cards + cols - 1) // cols

        card_width = (self.width - 120) // cols
        card_height = min(80, (available_height - 20) // max(rows, 1))
        card_spacing = 12

        # Icon mapping
        icon_map = {
            "money": "💰", "loan": "🏦", "subsidy": "💰", "amount": "₹",
            "check": "✓", "tick": "✓", "yes": "✅", "done": "✅",
            "document": "📄", "paper": "📄", "certificate": "📜",
            "time": "⏰", "deadline": "⏰", "date": "📅",
            "person": "👤", "people": "👥", "business": "🏢", "office": "🏛",
            "growth": "📈", "increase": "📈", "up": "⬆",
            "warning": "⚠️", "alert": "🚨", "danger": "⬇",
            "call": "📞", "dm": "📩", "contact": "📞",
            "default": "✓",
        }

        for i, card in enumerate(cards[:num_cards]):
            row = i // cols
            col = i % cols

            x = 60 + col * (card_width + card_spacing)
            y = card_area_top + row * (card_height + card_spacing)

            # Card background (dark, semi-transparent)
            card_bg = (30, 30, 40)
            draw.rounded_rectangle(
                [x, y, x + card_width, y + card_height],
                radius=12,
                fill=card_bg,
                outline=accent_rgb,
                width=2,
            )

            # Icon
            card_text = card.get("text", card.get("benefit", str(card)))
            icon = card.get("icon", "check")
            icon_char = icon_map.get(icon.lower() if isinstance(icon, str) else "check", "✓")
            if isinstance(icon, str) and len(icon) <= 2:
                icon_char = icon

            icon_font = _find_font("bold", 36)
            draw.text((x + 15, y + 18), icon_char, font=icon_font, fill=accent_rgb)

            # Card text
            title = card.get("title", card_text[:30])
            card_font = _find_font("regular", 26)
            # Truncate if needed
            display_text = title[:40] + "..." if len(title) > 40 else title
            text_x = x + 60
            try:
                bbox = card_font.getbbox(display_text)
                text_w = bbox[2] - bbox[0]
            except AttributeError:
                text_w = len(display_text) * 14

            if text_x + text_w > x + card_width - 10:
                # Truncate
                while len(display_text) > 10 and text_x + text_w > x + card_width - 10:
                    display_text = display_text[:-4] + "..."
                    try:
                        bbox = card_font.getbbox(display_text)
                        text_w = bbox[2] - bbox[0]
                    except AttributeError:
                        text_w = len(display_text) * 14

            # Draw shadow + text
            draw.text((text_x + 1, y + 28), display_text, font=card_font, fill=(0, 0, 0))
            draw.text((text_x, y + 27), display_text, font=card_font, fill=text_color)

            # Highlight (amount/amount in green)
            highlight = card.get("highlight", card.get("amount", ""))
            if highlight:
                highlight_font = _find_font("bold", 24)
                green = colors.get("accent_green", "#00FF88")
                hx = x + card_width - 100
                draw.text((hx, y + 28), str(highlight), font=highlight_font, fill=green)

        return img

    # ── Layer 6: CTA ────────────────────────────────────────────────────────

    def _render_cta(self, img: Image.Image, cta: str, colors: dict,
                   accent: str, template: str) -> Image.Image:
        """Render call-to-action block."""
        draw = ImageDraw.Draw(img)
        accent_rgb = self._hex_to_rgb(accent)

        # CTA position: above branding area
        cta_y = int(self.height * 0.90)
        cta_height = 60

        # CTA background pill
        cta_x1 = 60
        cta_x2 = self.width - 60

        # Draw pill background
        draw.rounded_rectangle(
            [cta_x1, cta_y, cta_x2, cta_y + cta_height],
            radius=30,
            fill=accent_rgb,
        )

        # CTA text
        cta_font = _find_font("bold", 32)
        try:
            bbox = cta_font.getbbox(cta)
            text_w = bbox[2] - bbox[0]
        except AttributeError:
            text_w = len(cta) * 18

        text_x = (self.width - text_w) // 2
        draw.text((text_x + 1, cta_y + 13), cta, font=cta_font, fill=(0, 0, 0, 128))
        draw.text((text_x, cta_y + 12), cta, font=cta_font, fill="#FFFFFF")

        return img

    # ── Layer 7: Branding ──────────────────────────────────────────────────

    def _render_branding(self, img: Image.Image, colors: dict) -> Image.Image:
        """Render brand watermark."""
        draw = ImageDraw.Draw(img)
        text_color = colors.get("text_secondary", "#B0B0B0")

        # Brand text at bottom-right
        brand = "@prishaonlinedocumentation"
        brand_font = _find_font("regular", 22)

        try:
            bbox = brand_font.getbbox(brand)
            text_w = bbox[2] - bbox[0]
        except AttributeError:
            text_w = len(brand) * 12

        x = self.width - text_w - 40
        y = self.height - 40

        # Semi-transparent background
        draw.rounded_rectangle(
            [x - 10, y - 5, self.width - 30, y + 30],
            radius=8,
            fill=(10, 10, 15),
        )

        draw.text((x, y), brand, font=brand_font, fill=text_color)

        return img

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return (255, 255, 255)

    def _save_image(self, img: Image.Image) -> str:
        """Save image to disk and return path."""
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        path = IMAGES_DIR / f"post_{timestamp}.png"
        img.save(path, "PNG", quality=95)
        return str(path)


# Backward-compatible method
def create_image(headline: str, image_text: str = "", category: str = "",
                output_path: str = None, sub_headline: str = "",
                info_cards: list = None, cta: str = None,
                template: str = "opportunity_alert", accent: str = None,
                color_scheme: dict = None, use_face: bool = False,
                face_path: str = None, config: dict = None) -> str:
    """
    Backward-compatible image creation.
    Old signature: create_image(headline, image_text, category, output_path)
    New: keyword arguments for full spec.
    """
    engine = HybridImageEngine(config or {})

    spec = {
        "headline": headline,
        "sub_headline": sub_headline or image_text[:80],
        "info_cards": info_cards or [],
        "cta": cta or "📩 DM 'INFO'",
        "template": template,
        "color_scheme": color_scheme or {},
        "accent": accent or "#4A90D9",
        "use_face": use_face,
        "face_path": face_path,
    }

    path = engine.create_image(spec)

    if output_path and path != output_path:
        import shutil
        shutil.copy2(path, output_path)
        return output_path

    return path


if __name__ == "__main__":
    import yaml
    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        config = {}

    path = create_image(
        headline="💰 GOVERNMENT GIVING ₹25 LAKH SUBSIDY",
        sub_headline="Are You Eligible? Read This.",
        info_cards=[
            {"icon": "💰", "title": "Up to ₹25 Lakh", "highlight": "₹25L"},
            {"icon": "✓", "title": "No Collateral Required"},
            {"icon": "🏢", "title": "For New & Existing Business"},
            {"icon": "📱", "title": "Easy Online Application"},
            {"icon": "🏛", "title": "PMEGP Government Scheme"},
        ],
        cta="📩 DM 'INFO'",
        template="opportunity_alert",
        accent="#00FF88",
        config=config,
    )
    print(f"Image saved: {path}")
