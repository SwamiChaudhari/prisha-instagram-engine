"""
tests/test_pipeline.py — Validation tests for the Instagram Engine.

Run with: python -m pytest tests/ -v
Or simply: python tests/test_pipeline.py
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


def test_imports():
    """Test that all modules can be imported."""
    from lib import utils
    from lib.logger import EngineLogger
    from lib.content_engine import ContentEngine
    from lib.image_engine import ImageEngine
    from lib.dedup_engine import DedupEngine
    from lib.instagram_publisher import InstagramPublisher
    print("[PASS] All modules imported successfully")


def test_config_load():
    """Test that config.yaml loads correctly."""
    config = utils.load_config()
    assert "business" in config
    assert "services" in config
    assert "content_categories" in config
    assert len(config["content_categories"]) > 0
    print(f"[PASS] Config loaded: {len(config['content_categories'])} categories")


def test_dedup_engine():
    """Test duplicate detection."""
    from lib.dedup_engine import DedupEngine

    history = [
        {"topic": "GST Registration benefits", "headline": "Why GST Matters", "category": "GST"},
        {"topic": "Udyam Registration guide", "headline": "Get Udyam Today", "category": "Udyam"},
    ]
    dedup = DedupEngine(history)

    # Exact duplicate
    assert dedup.is_duplicate("GST Registration benefits", "Why GST Matters") is True

    # New topic
    assert dedup.is_duplicate("FSSAI License process", "Food License Guide") is False

    # Category distribution
    cat = dedup.pick_category()
    assert cat in config["content_categories"]
    print("[PASS] Dedup engine working correctly")


def test_content_validation():
    """Test content output validation."""
    from lib.content_engine import ContentEngine

    engine = ContentEngine()
    result = engine._validate_output({}, "GST")

    assert "topic" in result
    assert "headline" in result
    assert "caption" in result
    assert "hashtags" in result
    assert isinstance(result["hashtags"], list)
    print("[PASS] Content validation working correctly")


def test_image_generation():
    """Test image generation without API keys."""
    from lib.image_engine import ImageEngine

    config = utils.load_config()
    engine = ImageEngine(config)

    test_path = str(PROJECT_ROOT / "images" / "test_output.png")
    result = engine.create_image(
        image_text="GST Registration made simple.\nContact us today!",
        headline="Get GST Registration Done Right",
        category="GST",
        output_path=test_path,
    )

    assert Path(result).exists()
    assert Path(result).stat().st_size > 0
    print(f"[PASS] Image generated: {result} ({Path(result).stat().st_size} bytes)")


def test_posts_history_io():
    """Test reading/writing post history."""
    test_data = [
        {
            "date": "2025-06-01",
            "topic": "Test topic",
            "headline": "Test headline",
            "caption": "Test caption",
            "hashtags": "#test",
            "category": "GST",
        }
    ]

    # Save
    utils.save_posts_history(test_data)

    # Load
    loaded = utils.load_posts_history()
    assert len(loaded) >= 1
    assert loaded[-1]["topic"] == "Test topic"
    print(f"[PASS] Posts history I/O working ({len(loaded)} posts)")


def test_caption_builder():
    """Test caption assembly."""
    from main import InstagramEngine

    content = {
        "hook": "Did you know 70% of small businesses miss GST benefits?",
        "caption": "Last month a shop owner came to us confused about GST.",
        "cta": "DM us to get started today!",
        "hashtags": ["GST", "Business", "India"],
    }

    caption = InstagramEngine._build_caption(content)
    assert "Did you know" in caption
    assert "#GST" in caption or "GST" in caption
    assert "DM us" in caption
    print("[PASS] Caption builder working correctly")


if __name__ == "__main__":
    from lib import utils
    config = utils.load_config()
    utils.ensure_dirs()

    print("=" * 50)
    print("  Instagram Engine — Test Suite")
    print("=" * 50)

    tests = [
        test_imports,
        test_config_load,
        test_dedup_engine,
        test_content_validation,
        test_image_generation,
        test_posts_history_io,
        test_caption_builder,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_fn.__name__}: {e}")
            failed += 1

    print("=" * 50)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 50)

    if failed > 0:
        sys.exit(1)
