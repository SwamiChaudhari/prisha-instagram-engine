"""
image_providers/flux.py — FLUX image generation provider (via Replicate or direct API).
"""

import base64
import os
import time
from pathlib import Path

import requests

from lib.image_providers.base import ImageProvider

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class FluxProvider(ImageProvider):
    """Generate images using FLUX model via Replicate API."""

    def __init__(self):
        self.api_token = os.environ.get("REPLICATE_API_TOKEN", "")
        self.model = "black-forest-labs/flux-1.1-pro"

    @property
    def name(self) -> str:
        return "flux"

    def is_available(self) -> bool:
        return bool(self.api_token)

    def generate_image(self, prompt: str, width: int = 1080, height: int = 1080) -> str:
        if not self.api_token:
            raise RuntimeError("REPLICATE_API_TOKEN not set")

        # Replicate API
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        # Start prediction
        create_url = "https://api.replicate.com/v1/predictions"
        payload = {
            "version": "a1e18a2e54ae01a6f8e6c9e6c9e6c9e6c9e6c9e6c9e6c9e6c9e6c9e6c9e6c9e6",
            "input": {
                "prompt": prompt,
                "aspect_ratio": self._get_aspect_ratio(width, height),
                "output_format": "png",
                "output_quality": 90,
            },
        }

        resp = requests.post(create_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        prediction = resp.json()

        # Poll for result
        result_url = prediction.get("urls", {}).get("get", "")
        if not result_url:
            raise RuntimeError("No result URL from Replicate")

        for _ in range(60):  # Max 60 attempts (5 min)
            time.sleep(5)
            resp = requests.get(result_url, headers=headers, timeout=30)
            resp.raise_for_status()
            result = resp.json()

            if result.get("status") == "succeeded":
                image_url = result.get("output", [""])[0] if isinstance(result.get("output"), list) else result.get("output", "")
                if image_url:
                    return self._download_image(image_url, width, height)
            elif result.get("status") == "failed":
                raise RuntimeError(f"FLUX generation failed: {result.get('error', 'unknown')}")

        raise RuntimeError("FLUX generation timed out")

    def _download_image(self, url: str, width: int, height: int) -> str:
        """Download image from URL and save locally."""
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        from PIL import Image
        from io import BytesIO

        img = Image.open(BytesIO(resp.content))
        img = img.resize((width, height), Image.LANCZOS)

        output_dir = PROJECT_ROOT / "images"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        output_path = output_dir / f"ai_generated_{timestamp}.png"
        img.save(output_path, "PNG")

        return str(output_path)

    def _get_aspect_ratio(self, width: int, height: int) -> str:
        ratio = width / height
        if ratio > 1.1:
            return "16:9"
        elif ratio < 0.9:
            return "9:16"
        return "1:1"
