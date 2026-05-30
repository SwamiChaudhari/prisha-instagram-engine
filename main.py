#!/usr/bin/env python3
"""
main.py — Instagram Engine Pipeline Orchestrator.

Runs the complete pipeline:
  1. Load config + post history
  2. Pick a diverse category
  3. Generate content via AI
  4. Check for duplicates
  5. Generate branded image
  6. Publish to Instagram
  7. Save post to history
  8. Log everything

Usage:
    python main.py                  # Full pipeline (generate + publish)
    python main.py --dry-run        # Generate only, skip publishing
    python main.py --test-content   # Test content generation only
    python main.py --test-image     # Test image generation only
    python main.py --verify         # Verify Instagram credentials only

Environment:
    Reads .env file in project root.
    Requires: GEMINI_API_KEY or OPENAI_API_KEY
    For publishing: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Bootstrap ──────────────────────────────────────────────────────────────────
# Ensure project root is on sys.path so imports work from any cwd
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from lib.utils import (
    ensure_dirs,
    load_config,
    load_posts_history,
    save_posts_history,
    today_ist,
    now_ist,
    get_env,
    IMAGES_DIR,
    OUTPUT_DIR,
    POSTS_HISTORY_PATH,
)
from lib.logger import EngineLogger
from lib.dedup_engine import DedupEngine
from lib.content_engine import ContentEngine
from lib.image_engine import ImageEngine
from lib.instagram_publisher import InstagramPublisher

log = EngineLogger("main")
IST = timezone(timedelta(hours=5, minutes=30))


class InstagramEngine:
    """Main orchestrator for the Instagram content pipeline."""

    def __init__(self, dry_run: bool = False):
        ensure_dirs()
        self.config = load_config()
        self.dry_run = dry_run

        # Load history
        history = load_posts_history()
        log.info(f"Loaded {len(history)} posts from history")

        # Initialize modules
        self.dedup = DedupEngine(history)
        self.content = ContentEngine()
        self.image = ImageEngine(self.config)
        self.publisher = InstagramPublisher()

    def run(self) -> dict:
        """
        Execute the full pipeline.

        Returns:
            Pipeline result dict with all post details and status.
        """
        log.section("PRISHA ONLINE DOCUMENTATION — Instagram Engine Starting")

        result = {
            "date": today_ist(),
            "timestamp": now_ist(),
            "success": False,
            "category": "",
            "topic": "",
            "headline": "",
            "skipped": False,
            "skip_reason": "",
            "error": "",
        }

        try:
            # ── Step 1: Pick Category ─────────────────────────────────────
            log.section("Step 1: Picking Category")
            category = self.dedup.pick_category()
            result["category"] = category
            log.info(f"Selected category: {category}")

            # ── Step 2: Generate Content ──────────────────────────────────
            log.section("Step 2: Generating Content")
            used_topics = self.dedup.get_used_topics()
            used_headlines = self.dedup.get_used_headlines()

            post_content = self.content.generate_post(
                category=category,
                used_topics=used_topics,
                used_headlines=used_headlines,
            )
            result["topic"] = post_content.get("topic", "")
            result["headline"] = post_content.get("headline", "")

            log.info(f"Topic: {post_content.get('topic', '')}")
            log.info(f"Headline: {post_content.get('headline', '')}")

            # ── Step 3: Duplicate Check ───────────────────────────────────
            log.section("Step 3: Duplicate Check")
            is_dup = self.dedup.is_duplicate(
                topic=post_content["topic"],
                headline=post_content["headline"],
                image_text=post_content.get("image_text", ""),
            )

            if is_dup:
                log.warn("Duplicate detected! Retrying with new content...")
                # Retry once with forced new topic
                post_content = self.content.generate_post(
                    category=category,
                    used_topics=used_topics + [post_content["topic"]],
                    used_headlines=used_headlines + [post_content["headline"]],
                )
                is_dup = self.dedup.is_duplicate(
                    topic=post_content["topic"],
                    headline=post_content["headline"],
                    image_text=post_content.get("image_text", ""),
                )
                if is_dup:
                    log.error("Still duplicate after retry. Aborting.")
                    result["skipped"] = True
                    result["skip_reason"] = "Duplicate content detected after retry"
                    return result

            # ── Step 4: Build Caption ─────────────────────────────────────
            log.section("Step 4: Building Caption")
            caption = self._build_caption(post_content)
            log.info(f"Caption built ({len(caption)} chars)")

            # ── Step 5: Generate Image ────────────────────────────────────
            log.section("Step 5: Generating Image")
            image_filename = f"post_{today_ist()}.png"
            image_path = str(IMAGES_DIR / image_filename)

            image_full_path = self.image.create_image(
                image_text=post_content.get("image_text", post_content["headline"]),
                headline=post_content["headline"],
                category=category,
                output_path=image_path,
            )
            result["image_path"] = image_full_path
            log.info(f"Image generated: {image_full_path}")

            # ── Step 6: Publish to Instagram ──────────────────────────────
            if self.dry_run:
                log.section("Step 6: DRY RUN — Skipping Instagram publish")
                result["success"] = True
                result["dry_run"] = True
                log.info("Dry run: post would be published with caption:")
                log.info(caption[:200] + "...")
            else:
                log.section("Step 6: Publishing to Instagram")
                publish_result = self.publisher.publish(
                    image_path=image_full_path,
                    caption=caption,
                )

                result["success"] = publish_result.get("success", False)
                result["media_id"] = publish_result.get("media_id", "")
                result["creation_id"] = publish_result.get("creation_id", "")

                if not result["success"]:
                    result["error"] = publish_result.get("error", "Unknown publish error")
                    log.error(f"Publish failed: {result['error']}")
                else:
                    log.info(f"Published! Media ID: {result.get('media_id', 'N/A')}")

            # ── Step 7: Save to History ───────────────────────────────────
            log.section("Step 7: Saving to History")
            history_entry = {
                "date": today_ist(),
                "timestamp": now_ist(),
                "topic": post_content.get("topic", ""),
                "headline": post_content.get("headline", ""),
                "caption": caption,
                "hashtags": " ".join(post_content.get("hashtags", [])),
                "category": category,
                "image_text": post_content.get("image_text", ""),
                "image_path": result.get("image_path", ""),
                "published": result.get("success", False) and not self.dry_run,
                "media_id": result.get("media_id", ""),
            }

            # Update dedup + save
            history = load_posts_history()
            history.append(history_entry)
            save_posts_history(history)
            self.dedup.record_post(history_entry)

            log.info(f"History saved. Total posts: {len(history)}")

            # ── Step 8: Save Result ───────────────────────────────────────
            result_path = OUTPUT_DIR / f"result_{today_ist()}.json"
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            log.info(f"Result saved: {result_path}")

        except Exception as e:
            log.error(f"Pipeline failed with exception: {e}", extra={
                "exception_type": type(e).__name__
            })
            result["error"] = str(e)
            import traceback
            log.debug(traceback.format_exc())

        # ── Summary ──────────────────────────────────────────────────────────
        log.section("PIPELINE SUMMARY")
        log.info(f"Date:      {result['date']}")
        log.info(f"Category:  {result.get('category', 'N/A')}")
        log.info(f"Topic:     {result.get('topic', 'N/A')}")
        log.info(f"Headline:  {result.get('headline', 'N/A')}")
        log.info(f"Success:   {result['success']}")
        log.info(f"Skipped:   {result.get('skipped', False)}")
        if result.get("error"):
            log.info(f"Error:     {result['error']}")

        return result

    # ── Helpers ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_caption(content: dict) -> str:
        """Assemble the full Instagram caption from generated content."""
        hook = content.get("hook", "")
        caption_body = content.get("caption", "")
        cta = content.get("cta", "")
        hashtags = content.get("hashtags", [])

        parts = []
        if hook:
            parts.append(hook)
        if caption_body:
            parts.append("")
            parts.append(caption_body)
        if cta:
            parts.append("")
            parts.append(cta)
        if hashtags:
            parts.append("")
            parts.append(" ".join(f"#{h}" if not h.startswith("#") else h for h in hashtags))

        return "\n".join(parts).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prisha Online Documentation — Instagram Engine"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate content and image but skip publishing",
    )
    parser.add_argument(
        "--test-content",
        action="store_true",
        help="Test content generation only, then exit",
    )
    parser.add_argument(
        "--test-image",
        action="store_true",
        help="Test image generation only, then exit",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify Instagram API credentials only, then exit",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_dirs()

    # ── Test Content ─────────────────────────────────────────────────────────
    if args.test_content:
        log.section("TEST: Content Generation")
        config = load_config()
        history = load_posts_history()
        dedup = DedupEngine(history)
        engine = ContentEngine()
        category = dedup.pick_category()
        used_topics = dedup.get_used_topics()
        used_headlines = dedup.get_used_headlines()

        try:
            post = engine.generate_post(category, used_topics, used_headlines)
            print("\n--- Generated Content ---")
            print(json.dumps(post, ensure_ascii=False, indent=2))
            print("--- End ---\n")
        except RuntimeError as e:
            log.error(str(e))
            sys.exit(1)
        return

    # ── Test Image ───────────────────────────────────────────────────────────
    if args.test_image:
        log.section("TEST: Image Generation")
        config = load_config()
        engine = ImageEngine(config)
        path = engine.create_image(
            image_text="GST Registration made simple.\nGet started today!",
            headline="Get GST Registration Done Right",
            category="GST",
        )
        log.info(f"Test image saved: {path}")
        return

    # ── Verify Credentials ───────────────────────────────────────────────────
    if args.verify:
        log.section("TEST: Verify Instagram Credentials")
        pub = InstagramPublisher()
        ok = pub.verify_credentials()
        if ok:
            log.info("Credentials are VALID.")
        else:
            log.error("Credentials are INVALID or misconfigured.")
            sys.exit(1)
        return

    # ── Full Pipeline ────────────────────────────────────────────────────────
    engine = InstagramEngine(dry_run=args.dry_run)
    result = engine.run()

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
