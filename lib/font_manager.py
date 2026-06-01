"""
lib/font_manager.py — Premium Font Manager.

Font fallback chain:
  1. Premium fonts (Bebas Neue, Montserrat)
  2. Google/system fonts (DejaVu, Liberation)
  3. PIL default (graceful degradation)

Usage:
    fm = FontManager()
    font = fm.get_font("headline", size=80)
    bold_font = fm.get_font("bold", size=42)
"""

import os
from pathlib import Path
from PIL import ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"

# Font file registry
FONT_FILES = {
    # Premium fonts
    "headline": FONTS_DIR / "BebasNeue-Regular.ttf",
    "bebas": FONTS_DIR / "BebasNeue-Regular.ttf",
    "montserrat_bold": FONTS_DIR / "Montserrat-Bold.ttf",
    "montserrat_semibold": FONTS_DIR / "Montserrat-SemiBold.ttf",
    "montserrat_regular": FONTS_DIR / "Montserrat-Regular.ttf",
    "montserrat_light": FONTS_DIR / "Montserrat-Light.ttf",
    # System fallbacks
    "bold_system": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "regular_system": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}

# Style to font file mapping
STYLE_MAP = {
    "headline": "bebas",
    "display": "bebas",
    "title": "montserrat_bold",
    "bold": "montserrat_bold",
    "semibold": "montserrat_semibold",
    "regular": "montserrat_regular",
    "body": "montserrat_regular",
    "light": "montserrat_light",
    "caption": "montserrat_light",
}


class FontManager:
    """Manages font loading with caching and fallback chain."""

    def __init__(self, fonts_dir: str = None):
        self.fonts_dir = Path(fonts_dir) if fonts_dir else FONTS_DIR
        self._cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
        self._available_fonts: dict[str, str] = {}
        self._scan_fonts()

    def _scan_fonts(self):
        """Scan fonts directory and register all available .ttf/.otf files."""
        if not self.fonts_dir.exists():
            return
        for f in sorted(self.fonts_dir.iterdir()):
            if f.suffix.lower() in (".ttf", ".otf", ".woff2", ".woff"):
                key = f.stem.lower().replace("-", "_").replace(" ", "_")
                self._available_fonts[key] = str(f)
        # Also register by filename
        for name, path in FONT_FILES.items():
            if isinstance(path, Path) and path.exists():
                self._available_fonts[name] = str(path)

    def get_font(self, style: str = "regular", size: int = 32) -> ImageFont.FreeTypeFont:
        """
        Get a font by style name and size.
        Caches loaded fonts for performance.

        Styles: headline, display, title, bold, semibold, regular, body, light, caption
        """
        cache_key = (style, size)
        if cache_key in self._cache:
            return self._cache[cache_key]

        font = self._load_font(style, size)
        self._cache[cache_key] = font
        return font

    def _load_font(self, style: str, size: int) -> ImageFont.FreeTypeFont:
        """Try to load font with fallback chain."""
        # 1. Check style map
        font_key = STYLE_MAP.get(style, style)

        # 2. Try premium font
        if font_key in self._available_fonts:
            try:
                return ImageFont.truetype(self._available_fonts[font_key], size)
            except Exception:
                pass

        # 3. Try direct style name in available fonts
        if style in self._available_fonts:
            try:
                return ImageFont.truetype(self._available_fonts[style], size)
            except Exception:
                pass

        # 4. System fallbacks
        is_bold = style in ("headline", "display", "title", "bold")
        sys_paths = FONT_FILES.get("bold_system" if is_bold else "regular_system", [])
        for path in sys_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue

        # 5. Default
        return ImageFont.load_default()

    def get_text_size(self, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
        """Get text bounding box size (width, height)."""
        try:
            bbox = font.getbbox(text)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except Exception:
            return (len(text) * (font.size // 2), font.size)

    def wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        if not words:
            return []

        lines = []
        current_line: list[str] = []

        for word in words:
            test = " ".join(current_line + [word])
            w, _ = self.get_text_size(test, font)
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                # Single word too long — force-break
                w, _ = self.get_text_size(word, font)
                if w > max_width:
                    chars = []
                    for ch in word:
                        test_chars = "".join(chars + [ch])
                        w, _ = self.get_text_size(test_chars, font)
                        if w <= max_width:
                            chars.append(ch)
                        else:
                            if chars:
                                lines.append("".join(chars))
                            chars = [ch]
                    if chars:
                        current_line = ["".join(chars)]
                    else:
                        current_line = []

        if current_line:
            lines.append(" ".join(current_line))

        return lines if lines else [text]

    @property
    def available(self) -> list[str]:
        """List available font keys."""
        return sorted(self._available_fonts.keys())
