"""
image_providers/base.py — Abstract base class for all image providers.
"""

from abc import ABC, abstractmethod


class ImageProvider(ABC):
    """Abstract interface for AI image generation providers."""

    @abstractmethod
    def generate_image(self, prompt: str, width: int = 1080, height: int = 1080) -> str:
        """
        Generate an image from a text prompt.
        Returns: URL of the generated image (or local path).
        Raises: Exception on failure.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is properly configured and available."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
