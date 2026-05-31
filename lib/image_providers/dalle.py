"""
image_providers/dalle.py — OpenAI DALL-E 3 provider.
"""

import os
import time
from pathlib import Path

import requests

from lib.image_providers.base import ImageProvider

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class DalleProvider(ImageProvider):
    """Generate images using OpenAI DALL-E 3."""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = "dall-e-3"
        self.api_url = "https://api.openai.com/v1/images/generations"

    @property
    def name(self) -> str:
        return "dalle"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_image(self, prompt: str, width: int = 1080, height: int = 1080) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        # DALL-E 3 size mapping
        size = self._get_size(width, height)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": "hd",
        }

        resp = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        image_url = data.get("data", [{}])[0].get("url", "")
        if not image_url:
            raise RuntimeError("No image URL from DALL-E 3")

        return self._download_image(image_url, width, height)

    def _download_image(self, url: str, width: int, height: int) -> str:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        from PIL import Image
        from io import BytesIO

        img = Image.open(BytesIO(resp.content))
        img = img.resize((width, height), Image.Resampling.LANCZOS)

        output_dir = PROJECT_ROOT / "images"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        output_path = output_dir / f"ai_generated_{timestamp}.png"
        img.save(output_path, "PNG")

        return str(output_path)

    def _get_size(self, width: int, height: int) -> str:
        ratio = width / height
        if ratio > 1.1:
            return "1792x1024"  # DALL-E 3 wide
        elif ratio < 0.9:
            return "1024x1792"  # DALL-E 3 tall
        return "1024x1024"
