#!/usr/bin/env python3
"""publish_now.py — Publish a high-impact Instagram post right now."""
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from lib.image_engine import create_image
from lib.caption_generator import CaptionGenerator
from lib.cta_engine import CTAEngine
from lib.headline_engine import HeadlineEngine
from lib.style_analyzer import StyleAnalyzer
from lib.virality_scorer import ViralityScorer
from lib.instagram_publisher import InstagramPublisher
from lib.utils import load_config, load_posts_history, save_posts_history

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).parent

config = load_config()

# ── Topic ──────────────────────────────────────────────────────────────────
topic_data = {
    "topic": "PMEGP loan scheme gives Rs 25 lakh subsidy to small businesses without collateral",
    "category": "loan_subsidy",
    "pillar": "loans_subsidies",
    "source": "pib",
}

# ── Headline ───────────────────────────────────────────────────────────────
he = HeadlineEngine()
hr = he.generate_best_headline(
    topic_data["topic"], topic_data["category"],
    target="Small Business Owners", scheme="PMEGP", amount="Rs 25 Lakh"
)
headline = hr["headline"]
print(f"Headline: {headline}")

# ── Info blocks ────────────────────────────────────────────────────────────
info_blocks = [
    {"icon": "💰", "text": "Up to ₹25 Lakh Subsidy", "highlight": "₹25L"},
    {"icon": "✓", "text": "No Collateral Required", "highlight": ""},
    {"icon": "🏢", "text": "For New & Existing Businesses", "highlight": ""},
    {"icon": "📱", "text": "Easy Online Application", "highlight": ""},
    {"icon": "🏛", "text": "PMEGP Government Scheme", "highlight": ""},
]

# ── Captions ───────────────────────────────────────────────────────────────
cg = CaptionGenerator()
caps = cg.generate_captions(headline, topic_data["topic"], topic_data["category"], info_blocks)
cta_engine = CTAEngine()
daily_cta = cta_engine.get_cta(template="opportunity_alert", pillar="loans_subsidies")
print(f"CTA: {daily_cta}")

# ── Image ──────────────────────────────────────────────────────────────────
sa = StyleAnalyzer()
colors = sa.get_color_scheme("opportunity_alert")

img_path = PROJECT_ROOT / "images" / f"post_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.png"
create_image(
    headline=headline, sub_headline="Are You Eligible? Apply Now.",
    info_cards=info_blocks, cta=daily_cta, template="opportunity_alert",
    accent="#00FF88", color_scheme=colors, config=config, output_path=str(img_path),
)
print(f"Image: {img_path}")

# ── Score ──────────────────────────────────────────────────────────────────
scorer = ViralityScorer()
virality = scorer.score_post({
    "headline": headline, "caption": caps["english"], "topic": topic_data["topic"],
    "category": topic_data["category"], "pillar": topic_data["pillar"],
    "hashtags": caps["hashtags"], "info_blocks": info_blocks,
    "template": "opportunity_alert", "use_face": False, "source": "pib", "cta": daily_cta,
})
print(f"Virality: {virality['overall_score']}%")

# ── Commit image to GitHub ────────────────────────────────────────────────
print("\nCommitting image to GitHub...")
img_name = img_path.name
subprocess.run(["git", "add", f"images/{img_name}"], cwd=PROJECT_ROOT, capture_output=True)
subprocess.run(["git", "commit", "-m", f"Post image {img_name}"], cwd=PROJECT_ROOT, capture_output=True)
push_result = subprocess.run(["git", "push"], cwd=PROJECT_ROOT, capture_output=True, text=True)
print(f"Push: {push_result.stdout[:100]}")

print("Waiting 15s for GitHub CDN propagation...")
time.sleep(15)

image_url = f"https://raw.githubusercontent.com/SwamiChaudhari/prisha-instagram-engine/main/images/{img_name}"
print(f"Image URL: {image_url}")

# ── Assemble caption ───────────────────────────────────────────────────────
full_caption = caps["english"] + "\n\n—\n\n" + caps["hinglish"] + f"\n\n{daily_cta}\n\n"
full_caption += " ".join(f"#{h}" for h in caps["hashtags"])

# ── Publish ────────────────────────────────────────────────────────────────
print("\nPublishing to Instagram...")
import os
os.environ["IMAGE_URL_OVERRIDE"] = image_url

pub = InstagramPublisher()
result = pub.publish(image_path=image_url, caption=full_caption)

if result.get("success"):
    print(f"✅ POSTED! Media ID: {result.get('media_id', 'N/A')}")
    history = load_posts_history()
    history.append({
        "date": datetime.now(IST).strftime("%Y-%m-%d"),
        "headline": headline, "topic": topic_data["topic"],
        "category": topic_data["category"], "pillar": topic_data["pillar"],
        "template": "opportunity_alert", "cta": daily_cta,
        "image_path": str(img_path), "image_url": image_url,
        "published": True, "media_id": result.get("media_id", ""),
        "virality_score": virality["overall_score"],
    })
    save_posts_history(history)
    print("History saved. Check Instagram!")
else:
    print(f"❌ FAILED: {result.get('error', 'unknown')}")
    sys.exit(1)
