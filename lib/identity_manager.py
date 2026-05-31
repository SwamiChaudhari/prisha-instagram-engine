"""
identity_manager.py — Manage user photo integration for Instagram posts.

Rules:
- Use photo in ~30% of posts (configurable, default 30%)
- Preserve: face, beard, hairstyle, skin tone, body structure
- Never: beautify, change identity, alter facial structure
- Roles: business_consultant, government_scheme_advisor, registration_expert, msme_expert
"""

import hashlib
import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
IDENTITY_DIR = PROJECT_ROOT / "assets" / "identity"
HISTORY_PATH = PROJECT_ROOT / "data" / "generated_posts.json"

ROLES = {
    "business_consultant": {
        "description": "Professional business consultant explaining benefits",
        "pose": "confident, pointing at information, professional attire",
        "context": "standing in modern office or business setting",
    },
    "government_scheme_advisor": {
        "description": "Government scheme advisor explaining new schemes",
        "pose": "explaining with hand gestures, holding documents",
        "context": "near government office or with government building background",
    },
    "registration_expert": {
        "description": "Registration expert helping with documentation",
        "pose": "sitting at desk with laptop, helping client",
        "context": "modern documentation center or office",
    },
    "msme_expert": {
        "description": "MSME expert advising small business owners",
        "pose": "meeting with business owner, discussing growth",
        "context": "small business setting or meeting room",
    },
    "startup_mentor": {
        "description": "Startup mentor guiding new entrepreneurs",
        "pose": "mentoring, whiteboard discussion, energetic",
        "context": "startup office or co-working space",
    },
    "documentation_specialist": {
        "description": "Documentation specialist handling government forms",
        "pose": "reviewing documents, professional setting",
        "context": "documentation center with certificates visible",
    },
}


class IdentityManager:
    """Manage user photo integration."""

    def __init__(self):
        self.config = self._load_config()
        self.target_percentage = self.config.get("face_usage", {}).get("percentage", 0.30)
        self.photos = self._load_photos()

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _load_photos(self) -> list:
        """Load user photos from assets/identity/."""
        photos = []
        if IDENTITY_DIR.exists():
            for f in IDENTITY_DIR.iterdir():
                if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    photos.append(str(f))
        return photos

    def has_photos(self) -> bool:
        """Check if user photos are available."""
        return len(self.photos) > 0

    def should_use_face(self, force: bool = None) -> bool:
        """
        Determine if today's post should use the user's face.
        Maintains target percentage over time.
        """
        if not self.has_photos():
            return False

        if force is not None:
            return force

        # Check recent face usage
        recent = self._get_recent_posts_with_face(n=30)
        if not recent:
            return True  # First posts, use face

        face_count = sum(1 for p in recent if p.get("use_face", False))
        current_pct = face_count / len(recent)

        # If below target, strongly favor
        if current_pct < self.target_percentage:
            return random.random() < 0.75
        else:
            return random.random() < 0.35

    def get_photo(self) -> str:
        """Get a random user photo path."""
        if not self.photos:
            return None
        return random.choice(self.photos)

    def get_role(self, template: str = None, pillar: str = None) -> dict:
        """
        Get the best role for today's post type.
        Returns: {role_name, description, pose, context}
        """
        role_mapping = {
            "opportunity_alert": ["business_consultant", "msme_expert", "startup_mentor"],
            "government_scheme": ["government_scheme_advisor", "registration_expert", "documentation_specialist"],
            "breaking_news": ["business_consultant", "government_scheme_advisor"],
            "business_growth": ["startup_mentor", "msme_expert", "business_consultant"],
            "warning_policy": ["government_scheme_advisor", "registration_expert"],
            "success_story": ["startup_mentor", "business_consultant"],
            "quick_tips": ["registration_expert", "documentation_specialist"],
        }

        candidates = role_mapping.get(template, list(ROLES.keys()))
        role_name = random.choice(candidates)
        return {"role": role_name, **ROLES[role_name]}

    def get_image_prompt_addition(self, role_info: dict) -> str:
        """
        Generate image prompt text describing how to include the user's photo.
        This gets appended to the main image prompt.
        """
        if not role_info:
            return ""

        return (
            f"Include a professional Indian man as {role_info['description']}. "
            f"He should be {role_info['pose']}. "
            f"Setting: {role_info['context']}. "
            f"Preserve natural appearance — no beautification, no facial alteration. "
            f"Professional attire, confident expression, trustworthy appearance."
        )

    def _get_recent_posts_with_face(self, n: int = 30) -> list:
        """Get recent posts to check face usage."""
        try:
            if HISTORY_PATH.exists():
                with open(HISTORY_PATH) as f:
                    data = json.load(f)
                posts = data if isinstance(data, list) else data.get("posts", [])
                return posts[-n:]
        except Exception:
            pass
        return []


if __name__ == "__main__":
    mgr = IdentityManager()
    print(f"Has photos: {mgr.has_photos()}")
    print(f"Should use face: {mgr.should_use_face()}")
    role = mgr.get_role(template="opportunity_alert")
    print(f"Role: {role['role']}")
    print(f"Prompt addition: {mgr.get_image_prompt_addition(role)[:100]}...")
