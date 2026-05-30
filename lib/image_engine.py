"""
lib/image_engine.py — Instagram post image generation using Pillow.

Generates professional 1080x1080 business graphics without any external API.

Features:
- Branded color scheme from config
- Gradient backgrounds
- Text wrapping and centering
- Business branding (name, contact, website)
- Icon/decorative elements

Usage:
    engine = ImageEngine(config)
    path = engine.create_image(
        image_text="GST Registration...",
        headline="Get GST Done Right",
        category="GST",
        output_path="images/post_2025-06-01.png"
    )
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from lib.utils import PROJECT_ROOT, IMAGES_DIR, ensure_dirs
from lib.logger import EngineLogger

log = EngineLogger("image_engine")


class ImageEngine:
    """Generates branded Instagram post images."""

    # ── Init ────────────────────────────────────────────────────────────────────

    def __init__(self, config: dict):
        self.config = config
        self.img_cfg = config.get("image", {})
        self.biz_cfg = config.get("business", {})

        self.width = self.img_cfg.get("width", 1080)
        self.height = self.img_cfg.get("height", 1080)

        # Brand colors
        self.colors = {
            "primary": self._hex_to_rgb(self.img_cfg.get("brand_color_primary", "#1A3A5C")),
            "secondary": self._hex_to_rgb(self.img_cfg.get("brand_color_secondary", "#2E86AB")),
            "accent": self._hex_to_rgb(self.img_cfg.get("brand_color_accent", "#F6A21E")),
            "white": self._hex_to_rgb(self.img_cfg.get("brand_color_white", "#FFFFFF")),
            "light_bg": self._hex_to_rgb(self.img_cfg.get("brand_color_light_bg", "#F0F4F8")),
            "dark_text": self._hex_to_rgb(self.img_cfg.get("brand_color_dark_text", "#1A1A2E")),
            "gray_text": self._hex_to_rgb(self.img_cfg.get("brand_color_gray_text", "#5A6A7A")),
        }

        # Business info
        self.business_name = self.biz_cfg.get("name", "Prisha Online Documentation")
        self.website = self.biz_cfg.get("website", "")
        self.contact = self.biz_cfg.get("contact", "")

        # Load fonts
        self.fonts = self._load_fonts()

    # ── Public API ──────────────────────────────────────────────────────────────

    def create_image(
        self,
        image_text: str,
        headline: str,
        category: str,
        output_path: str | None = None,
    ) -> str:
        """
        Generate a branded Instagram post image.

        Layout:
            ┌──────────────────────────┐
            │  Category badge          │
            │                          │
            │  HEADLINE (large)        │
            │                          │
            │  Image text / key point  │
            │                          │
            │  ──  decorative  ──      │
            │                          │
            │  Business name           │
            │  Contact / Website       │
            └──────────────────────────┘

        Args:
            image_text: Main text to display on image (short, from content engine)
            headline: Post headline
            category: Content category (used for badge color)
            output_path: Where to save. Defaults to images/post_YYYY-MM-DD.png

        Returns:
            Absolute path to the saved image file
        """
        ensure_dirs()

        if output_path is None:
            from lib.utils import today_ist
            date_str = today_ist()
            output_path = str(IMAGES_DIR / f"post_{date_str}.png")

        # Create base image with gradient background
        img = Image.new("RGB", (self.width, self.height), self.colors["primary"])
        draw = ImageDraw.Draw(img)

        # Draw gradient background
        self._draw_gradient(img, draw)

        # Draw decorative elements
        self._draw_decorations(draw)

        y_cursor = 0

        # ── Category Badge ──────────────────────────────────────────────────
        y_cursor = 80
        badge_text = f"  {category.upper()}  "
        badge_font = self.fonts.get("badge", self.fonts["body"])

        # Badge background
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = bbox[2] - bbox[0] + 40
        badge_h = bbox[3] - bbox[1] + 20
        badge_x = (self.width - badge_w) // 2
        badge_y = y_cursor

        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=20,
            fill=self.colors["accent"],
        )
        draw.text(
            (badge_x + 20, badge_y + 10),
            badge_text.replace("  ", "").strip(),
            font=badge_font,
            fill=self.colors["dark_text"],
        )
        y_cursor = badge_y + badge_h + 60

        # ── Headline ────────────────────────────────────────────────────────
        headline_font = self.fonts.get("headline", self.fonts["title"])
        headline_wrapped = self._wrap_text(headline, headline_font, self.width - 120)

        for line in headline_wrapped:
            bbox = draw.textbbox((0, 0), line, font=headline_font)
            line_w = bbox[2] - bbox[0]
            x = (self.width - line_w) // 2
            # Draw text shadow for readability
            draw.text((x + 2, y_cursor + 2), line, font=headline_font, fill=(0, 0, 0, 80))
            draw.text((x, y_cursor), line, font=headline_font, fill=self.colors["white"])
            y_cursor += (bbox[3] - bbox[1]) + 10

        y_cursor += 40

        # ── Decorative Divider ───────────────────────────────────────────────
        divider_y = y_cursor
        div_margin = 200
        draw.line(
            [(div_margin, divider_y), (self.width - div_margin, divider_y)],
            fill=self.colors["accent"],
            width=3,
        )
        # Diamond in center
        cx, cy = self.width // 2, divider_y
        diamond_size = 8
        draw.polygon(
            [(cx, cy - diamond_size), (cx + diamond_size, cy),
             (cx, cy + diamond_size), (cx - diamond_size, cy)],
            fill=self.colors["accent"],
        )
        y_cursor += 50

        # ── Image Text / Key Message ─────────────────────────────────────────
        body_font = self.fonts.get("body_large", self.fonts["body"])
        text_wrapped = self._wrap_text(image_text, body_font, self.width - 160)

        for line in text_wrapped:
            bbox = draw.textbbox((0, 0), line, font=body_font)
            line_w = bbox[2] - bbox[0]
            x = (self.width - line_w) // 2
            draw.text((x, y_cursor), line, font=body_font, fill=self.colors["light_bg"])
            y_cursor += (bbox[3] - bbox[1]) + 8

        y_cursor += 60

        # ── Bottom Section ───────────────────────────────────────────────────
        # Push bottom content toward the bottom of the image
        bottom_start = self.height - 220

        # Horizontal line
        line_margin = 100
        draw.line(
            [(line_margin, bottom_start), (self.width - line_margin, bottom_start)],
            fill=self.colors["secondary"],
            width=2,
        )

        # Business name
        biz_font = self.fonts.get("title", self.fonts["body"])
        bbox = draw.textbbox((0, 0), self.business_name, font=biz_font)
        biz_w = bbox[2] - bbox[0]
        draw.text(
            ((self.width - biz_w) // 2, bottom_start + 25),
            self.business_name,
            font=biz_font,
            fill=self.colors["accent"],
        )

        # Contact + Website
        contact_info = "  •  ".join(
            filter(None, [self.contact, self.website])
        )
        if contact_info:
            small_font = self.fonts.get("caption", self.fonts["body"])
            bbox = draw.textbbox((0, 0), contact_info, font=small_font)
            info_w = bbox[2] - bbox[0]
            draw.text(
                ((self.width - info_w) // 2, bottom_start + 75),
                contact_info,
                font=small_font,
                fill=self.colors["gray_text"],
            )

        # Save
        img.save(output_path, "PNG", quality=95)
        log.info(f"Image saved: {output_path}")
        return str(Path(output_path).resolve())

    # ── Drawing Helpers ─────────────────────────────────────────────────────────

    def _draw_gradient(self, img: Image.Image, draw: ImageDraw.Draw) -> None:
        """Draw a subtle gradient background from primary to secondary."""
        primary = self.colors["primary"]
        secondary = self.colors["secondary"]

        for y in range(self.height):
            ratio = y / self.height
            r = int(primary[0] + (secondary[0] - primary[0]) * ratio * 0.4)
            g = int(primary[1] + (secondary[1] - primary[1]) * ratio * 0.4)
            b = int(primary[2] + (secondary[2] - primary[2]) * ratio * 0.4)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

    def _draw_decorations(self, draw: ImageDraw.Draw) -> None:
        """Draw subtle decorative shapes."""
        # Top-right circle
        draw.ellipse(
            [self.width - 200, -50, self.width + 50, 200],
            fill=(255, 255, 255, 20),
            outline=None,
        )
        # Bottom-left circle
        draw.ellipse(
            [-80, self.height - 200, 150, self.height + 50],
            fill=(255, 255, 255, 15),
            outline=None,
        )
        # Small accent circle top-left
        draw.ellipse([30, 30, 80, 80], fill=self.colors["accent"])

    # ── Text Helpers ────────────────────────────────────────────────────────────

    def _wrap_text(
        self, text: str, font: ImageFont.FreeTypeFont, max_width: int
    ) -> list[str]:
        """
        Wrap text to fit within max_width pixels.

        Returns list of lines.
        """
        words = text.split()
        if not words:
            return [text]

        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                (0, 0), test_line, font=font
            )
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

                # Handle single words that are too wide
                bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox(
                    (0, 0), word, font=font
                )
                if bbox[2] - bbox[0] > max_width:
                    lines.append(word[-len(word)//2:])
                    current_line = [word[:len(word)//2]]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    # ── Fonts ───────────────────────────────────────────────────────────────────

    def _load_fonts(self) -> dict[str, ImageFont.FreeTypeFont]:
        """
        Load TTF fonts from fonts/ directory.
        Falls back to default font if TTF files not found.
        """
        fonts_dir = PROJECT_ROOT / "fonts"
        font_paths = {
            "DejaSans": [
                fonts_dir / "DejaVuSans.ttf",
                fonts_dir / "DejaVuSans-Bold.ttf",
            ],
        }

        loaded = {}

        # Try common system font paths
        system_font_candidates = [
            # DejaVu
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            # Liberation
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            # Noto
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            # FreeFont
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            # WSL Windows fallback
            "/mnt/c/Windows/Fonts/arial.ttf",
            "/mnt/c/Windows/Fonts/ARIALBD.TTF",
            "/mnt/c/Windows/Fonts/segoeui.ttf",
            "/mnt/c/Windows/Fonts/segoeuib.ttf",
        ]

        regular_path = None
        bold_path = None

        for candidate in system_font_candidates:
            p = Path(candidate)
            if p.exists():
                if "bold" in candidate.lower() or "Bold" in p.name or "BD" in p.name.upper():
                    if bold_path is None:
                        bold_path = p
                else:
                    if regular_path is None:
                        regular_path = p

        try:
            loaded["title"] = ImageFont.truetype(str(bold_path), 52) if bold_path else ImageFont.load_default()
            loaded["headline"] = ImageFont.truetype(str(bold_path), 58) if bold_path else ImageFont.load_default()
            loaded["body"] = ImageFont.truetype(str(regular_path), 34) if regular_path else ImageFont.load_default()
            loaded["body_large"] = ImageFont.truetype(str(regular_path), 40) if regular_path else ImageFont.load_default()
            loaded["caption"] = ImageFont.truetype(str(regular_path), 28) if regular_path else ImageFont.load_default()
            loaded["badge"] = ImageFont.truetype(str(bold_path), 28) if bold_path else ImageFont.load_default()
        except Exception as e:
            log.warn(f"Could not load TTF fonts, using default: {e}")
            default = ImageFont.load_default()
            loaded = {
                "title": default,
                "headline": default,
                "body": default,
                "body_large": default,
                "caption": default,
                "badge": default,
            }

        log.debug(f"Fonts loaded: regular={regular_path}, bold={bold_path}")
        return loaded

    # ── Color ───────────────────────────────────────────────────────────────────

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert hex color string to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
