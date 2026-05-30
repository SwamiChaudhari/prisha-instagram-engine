"""
utils.py — Shared helpers for the Instagram Engine.

Provides:
  - Environment variable loading
  - Path resolution
  - Date/time helpers
  - Config loading
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
IMAGES_DIR = PROJECT_ROOT / "images"
OUTPUT_DIR = PROJECT_ROOT / "output"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
POSTS_HISTORY_PATH = DATA_DIR / "generated_posts.json"

IST = timezone(timedelta(hours=5, minutes=30))


def ensure_dirs() -> None:
    """Create all required directories if they don't exist."""
    for d in [DATA_DIR, LOGS_DIR, IMAGES_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load and return config.yaml as a dict."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_posts_history() -> list:
    """Load generated_posts.json. Returns list of post dicts."""
    if not POSTS_HISTORY_PATH.exists():
        return []
    with open(POSTS_HISTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("posts", [])


def save_posts_history(posts: list) -> None:
    """Save list of post dicts to generated_posts.json."""
    ensure_dirs()
    with open(POSTS_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def today_ist() -> str:
    """Return today's date as YYYY-MM-DD in IST."""
    return datetime.now(IST).strftime("%Y-%m-%d")


def now_ist() -> str:
    """Return current timestamp as ISO-8601 in IST."""
    return datetime.now(IST).isoformat()


def get_env(key: str, default: str = "") -> str:
    """Read an environment variable, stripping whitespace."""
    return os.environ.get(key, default).strip()
