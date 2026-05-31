"""
image_providers/provider_manager.py — Config-driven provider switching.
Set IMAGE_PROVIDER in config.yaml to switch: gemini, flux, dalle, stability, pil
"""

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
PROVIDERS_DIR = Path(__file__).resolve().parent


class ProviderManager:
    """Load and manage image generation providers."""

    def __init__(self):
        self.config = self._load_config()
        self.provider_name = self.config.get("image", {}).get("provider", "pil")
        self._provider = None

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def get_provider(self):
        """Get the configured image provider."""
        if self._provider is not None:
            return self._provider

        if self.provider_name == "gemini":
            from lib.image_providers.gemini_imagen import GeminiImagenProvider
            self._provider = GeminiImagenProvider()
        elif self.provider_name == "flux":
            from lib.image_providers.flux import FluxProvider
            self._provider = FluxProvider()
        elif self.provider_name == "dalle":
            from lib.image_providers.dalle import DalleProvider
            self._provider = DalleProvider()
        elif self.provider_name == "stability":
            from lib.image_providers.stability import StabilityProvider
            self._provider = StabilityProvider()
        elif self.provider_name == "pil":
            from lib.image_engine import HybridImageEngine
            self._provider = HybridImageEngine()
        else:
            # Default to PIL
            from lib.image_engine import HybridImageEngine
            self._provider = HybridImageEngine()

        return self._provider

    def generate_image(self, prompt: str, width: int = 1080, height: int = 1080) -> str:
        """Generate an image using the configured provider."""
        provider = self.get_provider()
        if not provider.is_available():
            raise RuntimeError(f"Image provider '{self.provider_name}' is not available. Check API keys.")
        return provider.generate_image(prompt, width, height)
