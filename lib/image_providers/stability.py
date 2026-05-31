"""
image_providers/stability.py — Stability AI (Stable Diffusion) provider.
"""

import base64
import os
import time
from pathlib import Path

import requests

from lib.image_providers.base import ImageProvider

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class StabilityProvider(ImageProvider):
    """Generate images using Stability AI Stable Diffusion."""

    def __init__(self):
        self.api_key = os.environ.get("STABILITY_API_KEY", "")
        self.api_url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    @property
    def name(self) -> str:
        return "stability"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_image(self, prompt: str, width: int = 1080, height: int = 1080) -> str:
        if not self.api_key:
            raise RuntimeError("STABILITY_API_KEY not set")

        # Map to Stability-supported sizes
        aspect_ratio = self._get_aspect_ratio(width, height)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*",
        }

        data = {
            "prompt": prompt,
            "output_format": "png",
            "aspect_ratio": aspect_ratio,
        }

        resp = requests.post(self.api_url, headers=headers, data=data, timeout=120)
        resp.raise_for_status()

        # Save response content directly
        output_dir = PROJECT_ROOT / "images"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        output_path = output_dir / f"ai_generated_{timestamp}.png"

        with open(output_path, "wb") as f:
            f.write(resp.content)

        # Resize if needed
        from PIL import Image
        img = Image.open(output_path)
        if img.size != (width, height):
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            img.save(output_path, "PNG")

        return str(output_path)

    def _get_aspect_ratio(self, width: int, height: int) -> str:
        ratio = width / height
        if ratio > 1.1:
            return "16:9"
        elif ratio < 0.9:
            return "9:16"
        return "1:1"
