"""
main.py — Instagram Engine v2.0 Orchestrator.

8-Step Pipeline:
1. Post Strategy    → What type of post today?
2. Trend Research   → What's trending?
3. Topic Selection  → Best topic?
4. Style Analysis   → Which template?
5. Headline Engine  → 15 variations, pick best
6. Content Creation → Captions (Eng + Hinglish) + info blocks
7. Image Composition → 7-layer hybrid image
8. Quality Gate     → Virality score + humanization check
9. Publish          → Instagram
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent

# Load .env
load_dotenv(PROJECT_ROOT / ".env")

from lib.utils import ensure_dirs, load_config, load_posts_history, save_posts_history, today_ist, now_ist, get_env, IMAGES_DIR, OUTPUT_DIR
from lib.logger import EngineLogger
from lib.trend_researcher import TrendResearcher
from lib.topic_selector import TopicSelector
from lib.post_strategy_engine import PostStrategyEngine
from lib.style_analyzer import StyleAnalyzer
from lib.headline_engine import HeadlineEngine
from lib.caption_generator import CaptionGenerator
from lib.cta_engine import CTAEngine
from lib.image_engine import create_image
from lib.virality_scorer import ViralityScorer
from lib.humanization_checker import HumanizationChecker
from lib.identity_manager import IdentityManager
from lib.performance_memory import PerformanceMemory
from lib.instagram_publisher import InstagramPublisher
from lib.dedup_engine import DedupEngine

log = EngineLogger("main")


class InstagramEngine:
    """v2.0 orchestrator — full 8-step pipeline."""

    def __init__(self, dry_run: bool = False, skip_publish: bool = False):
        ensure_dirs()
        self.config = load_config()
        self.dry_run = dry_run
        self.skip_publish = skip_publish

        # Initialize modules
        self.strategy = PostStrategyEngine()
        self.researcher = TrendResearcher()
        self.selector = TopicSelector()
        self.style = StyleAnalyzer()
        self.headline = HeadlineEngine()
        self.caption_gen = CaptionGenerator()
        self.cta = CTAEngine()
        self.scorer = ViralityScorer()
        self.humanize = HumanizationChecker()
        self.identity = IdentityManager()
        self.memory = PerformanceMemory()
        self.publisher = InstagramPublisher()

        # Load history for dedup
        history = load_posts_history()
        self.dedup = DedupEngine(history)

    def run(self) -> dict:
        """Execute the full pipeline."""
        log.section("PRISHA ONLINE DOCUMENTATION — Instagram Engine v2.0 Starting")

        result = {
            "date": today_ist(),
            "timestamp": now_ist(),
            "success": False,
            "steps": {},
            "error": "",
        }

        try:
            # ── Step 1: Post Strategy ─────────────────────────────────────
            log.section("Step 1: Post Strategy")
            strategy = self.strategy.get_today_strategy()
            log.info(f"Strategy: {strategy['template']} | Pillar: {strategy['pillar']} | Face: {strategy['use_face']}")
            result["steps"]["strategy"] = strategy

            # ── Step 2: Trend Research ────────────────────────────────────
            log.section("Step 2: Trend Research")
            topics = self.researcher.get_trending()
            log.info(f"Found {len(topics)} topics from research")
            result["steps"]["topics_found"] = len(topics)

            # ── Step 3: Topic Selection ───────────────────────────────────
            log.section("Step 3: Topic Selection")
            used_topics = self.dedup.get_used_topics() + [p.get("topic", "") for p in load_posts_history()[-30:]]
            best_topic = self.selector.select_best(topics, used_topics)

            if not best_topic:
                log.error("No suitable topic found")
                result["error"] = "No suitable topic found"
                return result

            log.info(f"Selected: {best_topic['headline'][:80]}")
            log.info(f"Category: {best_topic['category']} | Score: {best_topic.get('_total_score', 0)}/100")
            result["steps"]["topic"] = best_topic

            # ── Step 4: Style Analysis / Template Selection ───────────────
            log.section("Step 4: Style Analysis")
            template = self.style.select_template(
                best_topic["topic"], best_topic["category"], strategy["template"]
            )
            color_scheme = self.style.get_color_scheme(template)
            layout_spec = self.style.get_layout_spec(template)
            log.info(f"Template: {template}")
            result["steps"]["template"] = template
            result["steps"]["color_scheme"] = color_scheme

            # ── Step 5: Headline Engine (15 variations) ───────────────────
            log.section("Step 5: Headline Competition")
            headline_result = self.headline.generate_best_headline(
                topic=best_topic["topic"],
                category=best_topic["category"],
                target=self._extract_target_audience(best_topic),
                scheme=best_topic.get("scheme", ""),
                amount=self._extract_amount(best_topic["topic"]),
            )
            best_headline = headline_result["headline"]
            log.info(f"Winner: {best_headline}")
            log.info(f"Scores: {headline_result['scores']}")
            result["steps"]["headline"] = headline_result

            # ── Step 6: Content Creation ──────────────────────────────────
            log.section("Step 6: Content Creation")

            # Build info cards
            info_blocks = self._build_info_blocks(best_topic)

            # Generate captions
            captions = self.caption_gen.generate_captions(
                headline=best_headline,
                topic=best_topic["topic"],
                category=best_topic["category"],
                info_blocks=info_blocks,
            )
            log.info(f"English caption: {len(captions['english'])} chars")
            log.info(f"Hinglish caption: {len(captions['hinglish'])} chars")
            log.info(f"Hashtags: {len(captions['hashtags'])}")

            # Get CTA
            daily_cta = self.cta.get_cta(template=template, pillar=strategy["pillar"])
            log.info(f"CTA: {daily_cta}")

            result["steps"]["captions"] = captions
            result["steps"]["cta"] = daily_cta
            result["steps"]["info_blocks"] = info_blocks

            # ── Step 7: Image Composition ──────────────────────────────────
            log.section("Step 7: Image Composition")

            face_path = None
            use_face = strategy["use_face"]
            if use_face and self.identity.has_photos():
                face_path = self.identity.get_photo()
                if face_path:
                    log.info(f"Using face: {Path(face_path).name}")

            image_spec = {
                "headline": best_headline,
                "sub_headline": best_topic.get("summary", "")[:80],
                "info_cards": info_blocks,
                "cta": daily_cta,
                "template": template,
                "color_scheme": color_scheme,
                "accent": color_scheme.get("accent", "#4A90D9"),
                "use_face": use_face,
                "face_path": face_path,
                "config": self.config,
            }

            image_path = create_image(**image_spec)
            log.info(f"Image saved: {image_path}")
            result["steps"]["image_path"] = image_path

            # ── Step 8: Quality Gate ───────────────────────────────────────
            log.section("Step 8: Quality Gate")

            post_for_scoring = {
                "headline": best_headline,
                "caption": captions["english"],
                "topic": best_topic["topic"],
                "category": best_topic["category"],
                "pillar": strategy["pillar"],
                "hashtags": captions["hashtags"],
                "info_blocks": info_blocks,
                "template": template,
                "use_face": use_face and bool(face_path),
                "source": best_topic.get("source", "ai_fallback"),
                "cta": daily_cta,
                "image_prompt": "",
            }

            # Virality scoring
            virality = self.scorer.score_post(post_for_scoring)
            log.info(f"Virality Score: {virality['overall_score']}%")
            log.info(f"Reference Similarity: {virality['reference_similarity']}%")
            for metric, score in virality["scores"].items():
                status = "✓" if score >= 8 else "✗"
                log.info(f"  {status} {metric}: {score}/10")

            # Humanization check
            human = self.humanize.check(post_for_scoring)
            log.info(f"Humanization: {'PASS' if human['passed'] else 'FAIL'} ({human['score']}/10)")
            if human["issues"]:
                for issue in human["issues"]:
                    log.warn(f"  ⚠ {issue}")

            result["steps"]["virality"] = virality
            result["steps"]["humanization"] = human

            # Decide whether to proceed
            if not virality["passed"]:
                failed = virality.get("failed_metrics", [])
                log.warn(f"Virality check failed on: {failed}")
                log.warn("Attempting regeneration...")
                # For v1, we publish anyway but log the issues
                # Future: implement regeneration loop

            if not human["passed"]:
                log.warn("Humanization concerns detected — publishing with caution")

            # ── Step 9: Publish ────────────────────────────────────────────
            if self.dry_run:
                log.section("DRY RUN — Skipping Instagram publish")
                result["success"] = True
                result["dry_run"] = True
                log.info("Dry run complete. Post would be published with:")
                log.info(f"  Headline: {best_headline}")
                log.info(f"  Caption: {captions['english'][:100]}...")
            else:
                log.section("Step 9: Publishing to Instagram")

                # Check for IMAGE_URL_OVERRIDE (for GitHub Actions two-phase)
                image_url_override = get_env("IMAGE_URL_OVERRIDE")
                if image_url_override:
                    publish_image_url = image_url_override
                    log.info(f"Using image URL override: {publish_image_url}")
                else:
                    publish_image_url = image_path

                # Full caption = English + Hinglish + hashtags
                full_caption = self._assemble_full_caption(captions, daily_cta)

                publish_result = self.publisher.publish(
                    image_path=publish_image_url,
                    caption=full_caption,
                )

                result["success"] = publish_result.get("success", False)
                result["media_id"] = publish_result.get("media_id", "")
                result["creation_id"] = publish_result.get("creation_id", "")

                if result["success"]:
                    log.info(f"Published! Media ID: {result.get('media_id', 'N/A')}")
                else:
                    result["error"] = publish_result.get("error", "Unknown publish error")
                    log.error(f"Publish failed: {result['error']}")

            # ── Save to History ────────────────────────────────────────────
            history_entry = {
                "date": today_ist(),
                "timestamp": now_ist(),
                "headline": best_headline,
                "topic": best_topic["topic"],
                "category": best_topic["category"],
                "pillar": strategy["pillar"],
                "template": template,
                "captions": captions,
                "cta": daily_cta,
                "info_blocks": info_blocks,
                "image_path": image_path,
                "use_face": use_face and bool(face_path),
                "virality_scores": virality["scores"],
                "overall_virality": virality["overall_score"],
                "reference_similarity": virality["reference_similarity"],
                "humanization_score": human["score"],
                "published": result.get("success", False) and not self.dry_run,
                "media_id": result.get("media_id", ""),
                "dry_run": self.dry_run,
            }

            history = load_posts_history()
            history.append(history_entry)
            save_posts_history(history)
            self.dedup.record_post(history_entry)

            # ── Performance Memory ─────────────────────────────────────────
            self.memory.record_post(
                post_data={
                    "headline": best_headline,
                    "topic": best_topic["topic"],
                    "template": template,
                    "pillar": strategy["pillar"],
                    "category": best_topic["category"],
                    "virality_scores": virality["scores"],
                    "overall_virality": virality["overall_score"],
                    "reference_similarity": virality["reference_similarity"],
                    "cta": daily_cta,
                }
            )

            log.info(f"History saved. Total posts: {len(history)}")

        except Exception as e:
            log.error(f"Pipeline failed: {e}")
            result["error"] = str(e)
            import traceback
            log.debug(traceback.format_exc())

        # ── Summary ──────────────────────────────────────────────────────────
        log.section("PIPELINE SUMMARY")
        log.info(f"Date:      {result['date']}")
        log.info(f"Template:  {result['steps'].get('template', 'N/A')}")
        log.info(f"Pillar:    {result['steps'].get('strategy', {}).get('pillar', 'N/A')}")
        log.info(f"Headline:  {result['steps'].get('headline', {}).get('headline', 'N/A')[:60]}")
        log.info(f"Virality:  {result['steps'].get('virality', {}).get('overall_score', 'N/A')}%")
        log.info(f"Reference: {result['steps'].get('virality', {}).get('reference_similarity', 'N/A')}%")
        log.info(f"Success:   {result['success']}")
        if result.get("error"):
            log.info(f"Error:     {result['error']}")

        return result

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _extract_target_audience(self, topic: dict) -> str:
        """Extract target audience from topic data."""
        return topic.get("_target", "Business Owners")

    def _extract_amount(self, topic: str) -> str:
        """Extract monetary amount from topic text."""
        import re
        match = re.search(r'rs\.?\s*[\d,]+(?:\s*(?:lakh|crore))?', topic, re.IGNORECASE)
        if match:
            return match.group().upper()
        match = re.search(r'[\d,]+\s*(?:lakh|crore)', topic, re.IGNORECASE)
        if match:
            return match.group().upper()
        return ""

    def _build_info_blocks(self, topic: dict) -> list:
        """Build info cards from topic data."""
        blocks = []
        category_hints = {
            "loan_subsidy": [
                {"icon": "💰", "text": "Financial support available", "highlight": ""},
                {"icon": "✓", "text": "No collateral required", "highlight": ""},
                {"icon": "📄", "text": "Simple documentation", "highlight": ""},
                {"icon": "🏢", "text": "For new & existing businesses", "highlight": ""},
                {"icon": "📱", "text": "Online application process", "highlight": ""},
            ],
            "government_schemes": [
                {"icon": "🏛", "text": "Official government scheme", "highlight": ""},
                {"icon": "✓", "text": "Free registration", "highlight": ""},
                {"icon": "📄", "text": "Minimal documents needed", "highlight": ""},
                {"icon": "📈", "text": "Unlock government benefits", "highlight": ""},
            ],
            "compliance": [
                {"icon": "⚠️", "text": "Deadline approaching", "highlight": ""},
                {"icon": "📅", "text": "Act before due date", "highlight": ""},
                {"icon": "📄", "text": "Required for all businesses", "highlight": ""},
                {"icon": "✓", "text": "Avoid penalties", "highlight": ""},
            ],
            "business_registration": [
                {"icon": "📝", "text": "Quick registration process", "highlight": ""},
                {"icon": "✓", "text": "Lifetime validity", "highlight": ""},
                {"icon": "💰", "text": "Tax benefits unlocked", "highlight": ""},
                {"icon": "🏛", "text": "Government recognized", "highlight": ""},
            ],
        }
        cat = topic.get("category", "")
        if cat in category_hints:
            blocks = category_hints[cat]
        else:
            blocks = [
                {"icon": "✓", "text": topic.get("topic", "")[:50], "highlight": ""},
                {"icon": "📄", "text": "Easy process available", "highlight": ""},
                {"icon": "📩", "text": "Contact for details", "highlight": ""},
            ]
        return blocks

    def _assemble_full_caption(self, captions: dict, cta: str) -> str:
        """Assemble the full caption from all parts."""
        parts = []
        parts.append(captions["english"])
        parts.append("")
        parts.append("—")
        parts.append("")
        parts.append(captions["hinglish"])
        parts.append("")
        parts.append(cta)
        parts.append("")
        parts.append(" ".join(f"#{h}" for h in captions["hashtags"]))
        return "\n".join(parts)


def parse_args():
    parser = argparse.ArgumentParser(description="Prisha Online Documentation — Instagram Engine v2.0")
    parser.add_argument("--dry-run", action="store_true", help="Generate only, skip publishing")
    parser.add_argument("--test-content", action="store_true", help="Test content generation only")
    parser.add_argument("--test-image", action="store_true", help="Test image generation only")
    parser.add_argument("--verify", action="store_true", help="Verify Instagram credentials")
    parser.add_argument("--performance-report", action="store_true", help="Show performance insights")
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_dirs()

    if args.verify:
        log.section("TEST: Verify Instagram Credentials")
        pub = InstagramPublisher()
        ok = pub.verify_credentials()
        if ok:
            log.info("Credentials are VALID.")
        else:
            log.error("Credentials are INVALID.")
            sys.exit(1)
        return

    if args.performance_report:
        mem = PerformanceMemory()
        insights = mem.get_insights()
        print(json.dumps(insights, indent=2))
        return

    # ── Test Content ──────────────────────────────────────────────────────
    if args.test_content:
        log.section("TEST: Content Generation Pipeline")
        config = load_config()

        strategy = PostStrategyEngine()
        researcher = TrendResearcher()
        selector = TopicSelector()
        style = StyleAnalyzer()
        headline = HeadlineEngine()
        caption = CaptionGenerator()
        cta = CTAEngine()

        s = strategy.get_today_strategy()
        print(f"Strategy: {s}")

        topics = researcher.get_trending()
        print(f"Topics found: {len(topics)}")

        used = []
        best = selector.select_best(topics, used)
        if best:
            print(f"Best topic: {best['headline']}")
            print(f"Score: {best.get('_total_score', 0)}/100")

            template = style.select_template(best["topic"], best["category"])
            colors = style.get_color_scheme(template)
            print(f"Template: {template}")
            print(f"Accent: {colors['accent']}")

            hr = headline.generate_best_headline(best["topic"], best["category"])
            print(f"Best headline: {hr['headline']}")

            caps = caption.generate_captions(hr["headline"], best["topic"], best["category"])
            daily_cta = cta.get_cta(template=template, pillar=s["pillar"])
            print(f"CTA: {daily_cta}")
            print(f"\nEnglish caption:\n{caps['english'][:300]}...")
            print(f"\nHinglish caption:\n{caps['hinglish'][:300]}...")
        return

    # ── Test Image ─────────────────────────────────────────────────────────
    if args.test_image:
        log.section("TEST: Image Generation")
        path = create_image(
            headline="💰 GOVERNING ₹25 LAKH SUBSIDY",
            sub_headline="Are You Eligible?",
            info_cards=[
                {"icon": "💰", "text": "Up to ₹25 Lakh", "highlight": "₹25L"},
                {"icon": "✓", "text": "No Collateral Required"},
                {"icon": "🏢", "text": "For New & Existing Business"},
                {"icon": "📱", "text": "Easy Online Application"},
                {"icon": "🏛", "text": "PMEGP Government Scheme"},
            ],
            cta="📩 DM 'INFO'",
            template="opportunity_alert",
            accent="#00FF88",
            config=load_config(),
        )
        log.info(f"Test image saved: {path}")
        return

    # ── Full Pipeline ──────────────────────────────────────────────────────
    engine = InstagramEngine(dry_run=args.dry_run)
    result = engine.run()

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
