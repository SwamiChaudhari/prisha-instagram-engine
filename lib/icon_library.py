"""
lib/icon_library.py — Premium SVG-Style Icon Renderer.

Renders crisp icons directly using Pillow drawing primitives.
No external SVG dependencies needed. All icons are drawn programmatically.

Categories: business, finance, government, compliance, growth, communication,
            education, warning, success, contact, document, legal

Usage:
    icons = IconLibrary()
    icon_img = icons.render("rupee", size=64, color="#FFD700")
    img.paste(icon_img, (x, y), icon_img)
"""

from PIL import Image, ImageDraw, ImageFont
import math
from pathlib import Path
from typing import Optional


class IconLibrary:
    """Renders premium icons using PIL drawing primitives."""

    def __init__(self, size: int = 64):
        self.size = size
        self._cache: dict[tuple[str, int, str], Image.Image] = {}

    def render(self, icon_name: str, size: Optional[int] = None,
               color: str = "#FFFFFF") -> Image.Image:
        """Render an icon by name. Returns RGBA image."""
        sz = size or self.size
        rgb = self._hex_to_rgb(color)
        cache_key = (icon_name, sz, color)
        if cache_key in self._cache:
            return self._cache[cache_key]

        method = getattr(self, f"_icon_{icon_name.replace('-', '_')}", None)
        if method:
            img = method(sz, rgb)
        else:
            img = self._icon_default(sz, rgb)

        self._cache[cache_key] = img
        return img

    def render_pil(self, draw: ImageDraw.Draw, icon_name: str,
                   x: int, y: int, size: int = 48, color: str = "#FFFFFF"):
        """Render directly to a draw context (faster, no image allocation)."""
        method = getattr(self, f"_draw_{icon_name.replace('-', '_')}", None)
        if method:
            method(draw, x, y, size, self._hex_to_rgb(color))

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _make_canvas(self, size: int) -> tuple[Image.Image, ImageDraw.Draw]:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        return img, ImageDraw.Draw(img)

    # ── Icon Draw Methods (direct to canvas, faster) ──────────────────────

    def _draw_rupee(self, draw, x, y, size, color):
        """Indian Rupee symbol."""
        cx, cy = x + size // 2, y + size // 2
        s3 = size // 3
        s6 = size // 6
        s2 = size // 2
        # Vertical line
        draw.line([(cx - s6, y + s6), (cx - s6, y + size - s6)], fill=color, width=max(2, size // 12))
        # Top horizontal
        draw.line([(cx - s6, y + s6), (cx + s3, y + s6)], fill=color, width=max(2, size // 12))
        # Middle horizontal
        draw.line([(cx - s6, cy - s6 // 2), (cx + s3, cy - s6 // 2)], fill=color, width=max(2, size // 16))
        # Diagonal
        draw.line([(cx + s3, y + s6), (cx - s6, cy + s6)], fill=color, width=max(2, size // 16))
        # Bottom
        draw.line([(cx - s6, cy + s6), (cx + s3, y + size - s6)], fill=color, width=max(2, size // 16))
        # Upper line
        draw.line([(cx - s6 - s6 // 2, y + s6), (cx + s3 + s6 // 2, y + s6)], fill=color, width=max(2, size // 12))

    def _draw_percent(self, draw, x, y, size, color):
        """Percentage symbol."""
        cx, cy = x + size // 2, y + size // 2
        r = size // 3
        # Circle top-left
        draw.ellipse([x + size // 8, y + size // 8, x + size // 8 + r, y + size // 8 + r],
                     outline=color, width=max(2, size // 16))
        # Circle bottom-right
        draw.ellipse([x + size - size // 8 - r, y + size - size // 8 - r,
                      x + size - size // 8, y + size - size // 8],
                     outline=color, width=max(2, size // 16))
        # Diagonal line
        draw.line([(x + size // 4, y + size * 3 // 4), (x + size * 3 // 4, y + size // 4)],
                  fill=color, width=max(2, size // 16))

    def _draw_chart_up(self, draw, x, y, size, color):
        """Upward trending chart."""
        s6 = size // 6
        pad = s6
        # Axes
        draw.line([(x + pad, y + pad), (x + pad, y + size - pad)], fill=color, width=max(2, size // 20))
        draw.line([(x + pad, y + size - pad), (x + size - pad, y + size - pad)], fill=color, width=max(2, size // 20))
        # Bars going up
        bars = 4
        bar_w = (size - 2 * pad) // (bars * 2)
        for i in range(bars):
            bh = int((size - 2 * pad) * (i + 1) / bars * 0.8)
            bx = x + pad + i * (bar_w * 2) + bar_w // 2
            by = y + size - pad - bh
            draw.rectangle([bx, by, bx + bar_w, y + size - pad], fill=color)

    def _draw_check(self, draw, x, y, size, color):
        """Checkmark / tick."""
        s3 = size // 3
        w = max(2, size // 12)
        draw.line([(x + s3, y + size // 2), (x + size // 2, y + size - s3)], fill=color, width=w)
        draw.line([(x + size // 2, y + size - s3), (x + size - s3, y + s3)], fill=color, width=w)

    def _draw_cross(self, draw, x, y, size, color):
        """Cross / X mark."""
        s4 = size // 4
        w = max(2, size // 12)
        draw.line([(x + s4, y + s4), (x + size - s4, y + size - s4)], fill=color, width=w)
        draw.line([(x + size - s4, y + s4), (x + s4, y + size - s4)], fill=color, width=w)

    def _draw_shield(self, draw, x, y, size, color):
        """Shield icon."""
        cx, cy = x + size // 2, y + size // 2
        s4 = size // 4
        s3 = size // 3
        # Shield shape
        points = [
            (cx, y + s4),          # top
            (x + size - s4, y + s3),  # right-top
            (x + size - s4, y + size // 2),  # right-mid
            (cx, y + size - s4),   # bottom
            (x + s4, y + size // 2),  # left-mid
            (x + s4, y + s3),      # left-top
        ]
        draw.polygon(points, outline=color, fill=(*color, 30))
        draw.line([(p[0], p[1]) for p in [points[0], points[1], points[2], points[3], points[4], points[5], points[0]]],
                  fill=color, width=max(2, size // 20))

    def _draw_document(self, draw, x, y, size, color):
        """Document / file."""
        s6 = size // 6
        # Page body
        draw.rectangle([x + s6, y + s6, x + size - s6, y + size - s6],
                       outline=color, width=max(2, size // 20))
        # Lines inside
        lines = 3
        gap = (size - 2 * s6) // (lines + 2)
        for i in range(lines):
            ly = y + s6 + gap * (i + 1)
            draw.line([(x + s6 + s6 // 2, ly), (x + size - s6 - s6 // 2, ly)],
                      fill=color, width=max(1, size // 32))
        # Corner fold
        draw.polygon([
            (x + size - s6 - s6, y + s6),
            (x + size - s6, y + s6),
            (x + size - s6, y + s6 + s6),
        ], fill=color)

    def _draw_building(self, draw, x, y, size, color):
        """Government building."""
        s6 = size // 6
        # Building body
        draw.rectangle([x + s6 * 2, y + s6 * 2, x + size - s6 * 2, y + size - s6],
                       outline=color, width=max(2, size // 20))
        # Columns
        for cx in [x + s6 * 3, x + size // 2, x + size - s6 * 3]:
            draw.line([(cx, y + s6 * 2), (cx, y + size - s6)], fill=color, width=max(2, size // 24))
        # Roof
        cx = x + size // 2
        draw.polygon([
            (cx, y + s6),
            (x + s6 * 2, y + s6 * 2),
            (x + size - s6 * 2, y + s6 * 2),
        ], outline=color, fill=(*color, 40))
        # Flag on top
        draw.line([(cx, y + s6), (cx, y + s6 // 2)], fill=color, width=max(2, size // 24))
        draw.rectangle([cx, y + s6 // 2, cx + s6, y + s6 // 2 + s6 // 2], fill=color)

    def _draw_clock(self, draw, x, y, size, color):
        """Clock / time."""
        cx, cy = x + size // 2, y + size // 2
        r = size // 2 - size // 8
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(2, size // 20))
        # Hour hand
        draw.line([(cx, cy), (cx, cy - r // 2)], fill=color, width=max(2, size // 16))
        # Minute hand
        draw.line([(cx, cy), (cx + r // 2, cy)], fill=color, width=max(2, size // 20))
        # Center dot
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=color)

    def _draw_star(self, draw, x, y, size, color):
        """Star icon."""
        cx, cy = x + size // 2, y + size // 2
        r_outer = size // 2 - size // 8
        r_inner = r_outer // 2
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = r_outer if i % 2 == 0 else r_inner
            px = cx + r * math.cos(angle)
            py = cy - r * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, fill=color)

    def _draw_lightning(self, draw, x, y, size, color):
        """Lightning bolt."""
        s6 = size // 6
        cx = x + size // 2
        points = [
            (cx + s6, y + s6),         # top-right
            (cx - s6 // 2, y + s6),    # top-left indent
            (cx + s6 // 2, y + cy),    # middle-right
            (cx - s6, y + cy + s6),    # bottom-left
            (cx + s6 // 2, y + size - s6),  # bottom-right
            (cx - s6 // 2, y + cy),    # middle-left
        ]
        draw.polygon(points, fill=color)

    def _draw_handshake(self, draw, x, y, size, color):
        """Handshake icon."""
        s6 = size // 6
        # Left hand
        draw.ellipse([x + s6, y + s6 * 2, x + s6 * 3, y + s6 * 4], outline=color, width=max(2, size // 20))
        # Right hand
        draw.ellipse([x + size - s6 * 3, y + s6 * 2, x + size - s6, y + s6 * 4],
                     outline=color, width=max(2, size // 20))
        # Connected center
        draw.rectangle([x + s6 * 3, y + s6 * 2 + s6 // 2, x + size - s6 * 3, y + s6 * 4 - s6 // 2],
                       fill=color)
        # Upward lines (arms)
        draw.line([(x + s6 * 2, y + s6 * 2), (x + s6 * 3, y + s6)], fill=color, width=max(2, size // 20))
        draw.line([(x + size - s6 * 2, y + s6 * 2), (x + size - s6 * 3, y + s6)],
                  fill=color, width=max(2, size // 20))

    def _draw_phone(self, draw, x, y, size, color):
        """Phone icon."""
        s6 = size // 6
        cx = x + size // 2
        # Phone body
        draw.rounded_rectangle(
            [cx - s6, y + s6, cx + s6, y + size - s6],
            radius=s6 // 2, outline=color, width=max(2, size // 20))
        # Screen
        draw.rectangle([cx - s6 + s6 // 2, y + s6 * 2, cx + s6 - s6 // 2, y + size - s6 * 2],
                       fill=color)

    def _draw_arrow_right(self, draw, x, y, size, color):
        """Right arrow."""
        s6 = size // 6
        cy = y + size // 2
        # Shaft
        draw.line([(x + s6, cy), (x + size - s6 * 2, cy)], fill=color, width=max(2, size // 16))
        # Head
        draw.polygon([
            (x + size - s6 * 2, cy - s6),
            (x + size - s6, cy),
            (x + size - s6 * 2, cy + s6),
        ], fill=color)

    def _draw_graduation(self, draw, x, y, size, color):
        """Graduation cap."""
        s6 = size // 6
        cx = x + size // 2
        # Cap top
        draw.polygon([
            (x + s6, y + s6 * 2),
            (x + size - s6, y + s6 * 2),
            (cx, y + s6),
        ], outline=color, fill=(*color, 50))
        # Band
        draw.line([(cx, y + s6), (cx, y + s6 * 3)], fill=color, width=max(2, size // 20))
        # Tassel
        draw.line([(cx, y + s6 * 3), (cx + s6, y + s6 * 4)], fill=color, width=max(2, size // 24))
        draw.ellipse([cx + s6 - s6 // 4, y + s6 * 4, cx + s6 + s6 // 4, y + s6 * 4 + s6 // 2], fill=color)

    def _draw_gear(self, draw, x, y, size, color):
        """Gear / settings."""
        cx, cy = x + size // 2, y + size // 2
        r = size // 2 - size // 6
        # Simple gear: circle with teeth
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(2, size // 20))
        # Inner hole
        draw.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3], fill=color)

    def _draw_people(self, draw, x, y, size, color):
        """People / group."""
        s6 = size // 6
        # Left person
        lcx = x + s6 * 2
        draw.ellipse([lcx - s6 // 2, y + s6, lcx + s6 // 2, y + s6 * 2], fill=color)
        draw.ellipse([lcx - s6, y + s6 * 2, lcx + s6, y + size - s6], outline=color, width=max(2, size // 20))
        # Right person
        rcx = x + size - s6 * 2
        draw.ellipse([rcx - s6 // 2, y + s6, rcx + s6 // 2, y + s6 * 2], fill=color)
        draw.ellipse([rcx - s6, y + s6 * 2, rcx + s6, y + size - s6], outline=color, width=max(2, size // 20))
        # Center person (slightly larger, in front)
        cx = x + size // 2
        draw.ellipse([cx - s6 // 2, y + s6 // 2, cx + s6 // 2, y + s6 * 2], fill=color)
        draw.ellipse([cx - s6, y + s6 * 2, cx + s6, y + size - s6 // 2],
                     outline=color, width=max(2, size // 16))

    def _draw_trophy(self, draw, x, y, size, color):
        """Trophy / success."""
        s6 = size // 6
        cx = x + size // 2
        # Cup
        draw.rounded_rectangle([cx - s6, y + s6, cx + s6, y + s6 * 4],
                               radius=s6 // 2, outline=color, width=max(2, size // 20))
        # Stems going out
        draw.arc([cx - s6 * 2, y + s6, cx, y + s6 * 3], start=180, end=0, fill=color, width=max(2, size // 20))
        draw.arc([cx, y + s6, cx + s6 * 2, y + s6 * 3], start=180, end=0, fill=color, width=max(2, size // 20))
        # Base
        draw.rectangle([cx - s6, y + s6 * 4, cx + s6, y + size - s6], fill=color)

    def _draw_rupee_coin(self, draw, x, y, size, color):
        """Coin with rupee."""
        cx, cy = x + size // 2, y + size // 2
        r = size // 2 - size // 8
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(2, size // 16))
        # Inner circle
        draw.ellipse([cx - r + r // 3, cy - r + r // 3, cx + r - r // 3, cy + r - r // 3],
                     outline=color, width=max(1, size // 24))

    def _draw_growth_chart(self, draw, x, y, size, color):
        """Growth chart with arrow."""
        s6 = size // 6
        pad = s6
        # Line going up-right
        pts = [
            (x + pad, y + size - pad),
            (x + pad + (size - 2 * pad) // 4, y + size - pad - (size - 2 * pad) // 3),
            (x + pad + (size - 2 * pad) // 2, y + size - pad - (size - 2 * pad) // 2),
            (x + size - pad, y + pad),
        ]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=color, width=max(2, size // 14))
        # Arrow head
        draw.polygon([
            (x + size - pad, y + pad),
            (x + size - pad - s6, y + pad + s6),
            (x + size - pad - s6, y + pad - s6),
        ], fill=color)

    def _draw_passport(self, draw, x, y, size, color):
        """Passport / identity document."""
        s6 = size // 6
        cx = x + size // 2
        # Book shape
        draw.rectangle([x + s6 * 2, y + s6, x + size - s6, y + size - s6],
                       outline=color, width=max(2, size // 20))
        # Spine line
        draw.line([(cx, y + s6), (cx, y + size - s6)], fill=color, width=max(2, size // 24))
        # Emblem on left
        draw.ellipse([x + s6 * 3, y + s6 * 2, cx - s6, y + s6 * 4],
                     outline=color, width=max(2, size // 24))

    def _draw_alert(self, draw, x, y, size, color):
        """Alert triangle."""
        s6 = size // 6
        cx = x + size // 2
        # Triangle
        draw.polygon([
            (cx, y + s6),
            (x + size - s6, y + size - s6),
            (x + s6, y + size - s6),
        ], outline=color, width=max(2, size // 16))
        # Exclamation
        draw.rectangle([cx - s6 // 3, y + s6 * 2, cx + s6 // 3, y + s6 * 4], fill=color)
        draw.ellipse([cx - s6 // 3, y + s6 * 4 + s6 // 2, cx + s6 // 3, y + s6 * 5 + s6 // 2], fill=color)

    def _draw_qr(self, draw, x, y, size, color):
        """QR code icon."""
        s6 = size // 6
        cell = (size - 2 * s6) // 7
        # 7x7 grid pattern
        pattern = [
            [1,1,1,0,1,1,1],
            [1,0,1,0,1,0,1],
            [1,1,1,0,1,1,1],
            [0,0,0,0,0,0,0],
            [1,0,1,1,1,0,1],
            [1,1,0,0,1,1,0],
            [1,0,1,0,1,1,1],
        ]
        for r, row in enumerate(pattern):
            for c, val in enumerate(row):
                if val:
                    bx = x + s6 + c * cell
                    by = y + s6 + r * cell
                    draw.rectangle([bx, by, bx + cell - 1, by + cell - 1], fill=color)

    def _draw_whatsapp(self, draw, x, y, size, color):
        """WhatsApp-style icon."""
        cx, cy = x + size // 2, y + size // 2
        r = size // 2 - size // 6
        # Phone in bubble
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(2, size // 16))
        # Phone inside
        s6 = size // 6
        draw.rounded_rectangle([cx - s6 // 2, cy - s6, cx + s6 // 2, cy + s6],
                               radius=s6 // 4, fill=color)
        # Tail
        draw.polygon([
            (cx - s6, cy + s6),
            (cx - s6 * 2, cy + s6 * 2),
            (cx, cy + s6),
        ], fill=color)

    def _draw_location(self, draw, x, y, size, color):
        """Location pin."""
        cx = x + size // 2
        r = size // 3
        # Pin shape
        cy_pin = y + size // 2 - size // 8
        points = [
            (cx, y + size - size // 6),  # bottom point
            (cx - r, cy_pin),
            (cx - r, cy_pin - r // 2),
            (cx, cy_pin - r),
            (cx + r, cy_pin - r // 2),
            (cx + r, cy_pin),
        ]
        draw.polygon(points, fill=color)
        # Inner circle
        draw.ellipse([cx - r // 3, cy_pin - r // 3, cx + r // 3, cy_pin + r // 3],
                     fill=(0, 0, 0, 0) if isinstance(color, tuple) and len(color) == 4 else None,
                     outline=color, width=2)

    def _draw_money_bag(self, draw, x, y, size, color):
        """Money bag."""
        s6 = size // 6
        cx = x + size // 2
        # Bag body
        draw.ellipse([x + s6 * 2, y + s6 * 2, x + size - s6 * 2, y + size - s6],
                     outline=color, width=max(2, size // 20))
        # Tie at top
        draw.rectangle([cx - s6 // 2, y + s6, cx + s6 // 2, y + s6 * 2], fill=color)
        # Rupee sign in center
        s = max(2, size // 12)
        draw.line([(cx - s // 2, y + s6 * 3), (cx - s // 2, y + s6 * 4)], fill=color, width=s)
        draw.line([(cx - s // 2, y + s6 * 3), (cx + s, y + s6 * 3)], fill=color, width=s)
        draw.line([(cx - s // 2, y + s6 * 3 + s), (cx + s, y + s6 * 3 + s)], fill=color, width=s)

    def _draw_gavel(self, draw, x, y, size, color):
        """Gavel / legal."""
        s6 = size // 6
        # Handle
        draw.line([(x + s6, y + s6 * 3), (x + size - s6, y + s6 * 4)],
                  fill=color, width=max(3, size // 10))
        # Head
        draw.rectangle([x + s6, y + s6 * 2, x + s6 * 3, y + s6 * 4],
                       fill=color)
        # Base
        draw.rectangle([x + s6, y + s6 * 4, x + s6 * 4, y + s6 * 5], fill=color)

    def _draw_file_check(self, draw, x, y, size, color):
        """File with checkmark."""
        s6 = size // 6
        # File
        draw.rectangle([x + s6, y + s6, x + size - s6 * 2, y + size - s6],
                       outline=color, width=max(2, size // 20))
        # Checkmark
        cx = x + size - s6 * 2
        cy = y + size - s6 * 2
        s = size // 8
        draw.line([(cx - s, cy), (cx - s // 2, cy + s // 2)], fill=color, width=max(2, size // 20))
        draw.line([(cx - s // 2, cy + s // 2), (cx + s, cy - s // 2)], fill=color, width=max(2, size // 20))

    def _draw_default(self, draw, x, y, size, color):
        """Default: circle."""
        s6 = size // 6
        draw.ellipse([x + s6, y + s6, x + size - s6, y + size - s6],
                     outline=color, width=max(2, size // 16))

    # ── Image-based icon methods (renders to RGBA image for compositing) ───

    def _icon_default(self, size: int, color: str) -> Image.Image:
        img, draw = self._make_canvas(size)
        self._draw_default(draw, 0, 0, size, color)
        return img

    # Quick render for common icons
    def _icon_rupee(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_rupee(draw, 0, 0, size, color)
        return img

    def _icon_chart_up(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_chart_up(draw, 0, 0, size, color)
        return img

    def _icon_check(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_check(draw, 0, 0, size, color)
        return img

    def _icon_document(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_document(draw, 0, 0, size, color)
        return img

    def _icon_building(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_building(draw, 0, 0, size, color)
        return img

    def _icon_clock(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_clock(draw, 0, 0, size, color)
        return img

    def _icon_star(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_star(draw, 0, 0, size, color)
        return img

    def _icon_lightning(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_lightning(draw, 0, 0, size, color)
        return img

    def _icon_shield(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_shield(draw, 0, 0, size, color)
        return img

    def _icon_phone(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_phone(draw, 0, 0, size, color)
        return img

    def _icon_people(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_people(draw, 0, 0, size, color)
        return img

    def _icon_trophy(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_trophy(draw, 0, 0, size, color)
        return img

    def _icon_alert(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_alert(draw, 0, 0, size, color)
        return img

    def _icon_percent(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_percent(draw, 0, 0, size, color)
        return img

    def _icon_handshake(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_handshake(draw, 0, 0, size, color)
        return img

    def _icon_graduation(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_graduation(draw, 0, 0, size, color)
        return img

    def _icon_qr(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_qr(draw, 0, 0, size, color)
        return img

    def _icon_location(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_location(draw, 0, 0, size, color)
        return img

    def _icon_money_bag(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_money_bag(draw, 0, 0, size, color)
        return img

    def _icon_growth_chart(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_growth_chart(draw, 0, 0, size, color)
        return img

    def _icon_gear(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_gear(draw, 0, 0, size, color)
        return img

    def _icon_passport(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_passport(draw, 0, 0, size, color)
        return img

    def _icon_whatsapp(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_whatsapp(draw, 0, 0, size, color)
        return img

    def _icon_cross(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_cross(draw, 0, 0, size, color)
        return img

    def _icon_gavel(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_gavel(draw, 0, 0, size, color)
        return img

    def _icon_file_check(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_file_check(draw, 0, 0, size, color)
        return img

    def _icon_arrow_right(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_arrow_right(draw, 0, 0, size, color)
        return img

    def _icon_rupee_coin(self, size, color):
        img, draw = self._make_canvas(size)
        self._draw_rupee_coin(draw, 0, 0, size, color)
        return img

    @classmethod
    def list_icons(cls) -> list[str]:
        """List all available icon names."""
        prefixes = ('_icon_', '_draw_')
        names = set()
        for attr in dir(cls):
            for prefix in prefixes:
                if attr.startswith(prefix):
                    name = attr[len(prefix):].replace('_', '-')
                    names.add(name)
        return sorted(names)


# Map common icon keywords to icon names
ICON_KEYWORD_MAP = {
    "money": "rupee", "loan": "rupee-coin", "subsidy": "money-bag",
    "amount": "rupee", "rupee": "rupee", "coin": "rupee-coin",
    "check": "check", "tick": "check", "yes": "check", "done": "file-check",
    "document": "document", "paper": "document", "certificate": "passport",
    "file": "document", "id": "passport", "time": "clock", "deadline": "clock",
    "date": "clock", "business": "building", "office": "building", "gov": "building",
    "government": "building", "growth": "growth-chart", "increase": "chart-up",
    "up": "arrow-right", "warning": "alert", "alert": "alert", "danger": "cross",
    "call": "phone", "dm": "whatsapp", "contact": "phone", "whatsapp": "whatsapp",
    "address": "location", "place": "location", "location": "location",
    "growth": "growth-chart", "chart": "chart-up", "trending": "chart-up",
    "star": "star", "success": "trophy", "win": "trophy", "award": "trophy",
    "lightning": "lightning", "fast": "lightning", "quick": "lightning",
    "people": "people", "group": "people", "team": "people", "community": "people",
    "shield": "shield", "protect": "shield", "safe": "shield", "secure": "shield",
    "graduation": "graduation", "education": "graduation", "student": "graduation",
    "scholarship": "graduation", "qr": "qr", "scan": "qr", "percent": "percent",
    "discount": "percent", "offer": "percent", "handshake": "handshake",
    "partner": "handshake", "trust": "handshake", "legal": "gavel",
    "compliance": "shield", "rule": "gavel", "settings": "gear",
    "config": "gear", "arrow": "arrow-right", "next": "arrow-right",
    "pass": "file-check", "approved": "file-check",
}


def icon_name_from_keyword(keyword: str) -> str:
    """Map a keyword to an icon name."""
    k = keyword.lower().strip()
    return ICON_KEYWORD_MAP.get(k, k)
