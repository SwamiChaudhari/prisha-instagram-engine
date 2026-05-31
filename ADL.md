# Architecture Decision Log (ADL) — Instagram Engine v2.0
# Created: May 31, 2026
# Lead: Owl (Autonomous architect)
# Status: Active construction

---

## ADL-001: Hybrid Image Architecture (AI Scene + Text Overlay)

**Date:** May 31, 2026
**Problem:** Reference images show magazine-quality, news-style posts with complex typography, info blocks, and layered composition. AI image generators (DALL-E, FLUX, Imagen) are good at photorealistic scenes but BAD at precise text rendering and complex layouts.

**Alternatives considered:**
1. *Pure AI generation* — Let AI generate the entire image including text. Rejected because AI can't reliably render Hindi/English text, specific amounts (₹25 Lakh), or consistent branding.
2. *Pure PIL/programmatic* — Build everything with code. Rejected because PIL can't produce photorealistic human faces or magazine-quality backgrounds.
3. *Hybrid approach* — AI generates the visual scene (background, face, mood), then code composites all text/typography/branding layers on top. **Selected.**

**Decision:** Hybrid 7-layer composition system:
- Layer 1: Background scene (AI-generated or gradient)
- Layer 2: Face/subject (AI-generated or user photo)
- Layer 3: Visual elements (icons, charts — composited)
- Layer 4: Headline (rendered with PIL, precise typography)
- Layer 5: Info cards (rendered with PIL)
- Layer 6: CTA (rendered with PIL)
- Layer 7: Branding (logo, watermark — composited)

**Why:** This gives AI quality where it excels (realism) + code precision where it's needed (text, layout, branding). Instagram's API requires a public image URL, so we can compose the final image server-side.

**Future risks:** When AI video generation matures (for Reels), the same hybrid principle applies — AI generates motion scene, code composites text overlays.

---

## ADL-002: Pluggable Image Provider Architecture

**Date:** May 31, 2026
**Problem:** Need to support multiple AI image providers (Gemini, DALL-E, FLUX, Stability) without rewriting code each time.

**Alternatives considered:**
1. *Single provider hardcode* — Quick but locks us into one vendor. Rejected.
2. *If/elif chains in image_engine* — Works but violates open/close principle. Rejected.
3. *Abstract base class + provider manager* — New provider = new class + config change. **Selected.**

Decision: `ImageProvider` ABC with `generate_image(prompt) -> url` interface. ProviderManager loads based on `IMAGE_PROVIDER=flux` config.

**Why:** Zero code changes to switch providers. Adding a new provider = create one file + add one line to ProviderManager.

---

## ADL-003: 10-Metric Virality Scoring

**Date:** May 31, 2026
**Problem:** Need objective quality gate that ensures every post meets the "looks like business news page" standard.

**Alternatives considered:**
1. *Single overall score* — Too vague, can't give targeted feedback. Rejected.
2. *AI-based scoring (LLM rates the post)* — Slow, costs API calls, rate-limited. Rejected.
3. *Rule-based 10-metric scoring* — Fast, free, specific feedback for regeneration. **Selected.**

**Metrics:** curiosity, financial_opportunity, urgency, trust, visual_appeal, shareability, engagement_potential, local_relevance, lead_generation, humanization.

**Why:** Rule-based is instant and free. Each metric has specific, codifiable criteria. Failed metrics generate targeted feedback for regeneration loop.

---

## ADL-004: Template System (5 Templates)

**Date:** May 31, 2026
**Problem:** Need different visual layouts for different content types (breaking news vs. opportunity vs. warning).

**Decision:** 5 templates — opportunity_alert, breaking_news, government_scheme, business_growth, warning_policy. Each defines layout, colors, icon style, info card count.

**Why:** Matching template to content type is how real media companies work. A breaking news post looks different from an opportunity alert.

---

## ADL-005: Roman Hinglish (Not Devanagari)

**Date:** May 31, 2026
**Problem:** Target audience (Indian business owners) responds better to conversational Hindi written in English script.

**Decision:** Generate Roman Hinglish captions (e.g., "Aapke business ke liye yeh important hai"). Do NOT generate Devanagari script.

**Why:** Roman Hinglish performs better on Instagram for the target demographic. Devanagari feels more formal/less engaging.

---

## ADL-006: Weekly Content Mix + Pillar Rotation

**Date:** May 31, 2026
**Problem:** Feed becomes repetitive if same type of post appears daily.

**Decision:** 7-day rotation (Mon=Opportunity, Tue=GovScheme, etc.) + 8 content pillars with weighted random selection avoiding yesterday's pillar.

**Why:** Real media companies balance their content mix. Users unfollow repetitive pages.

---

## ADL-007: Face Usage at 65%

**Date:** May 31, 2026
**Problem:** Human faces increase engagement by 38% (social media research). But overuse dilutes impact.

**Decision:** 65% of posts include a human face. Stored as deterministic tracking — if below target, bias toward face posts.

**Why:** Reference analysis shows 60-70% face usage. This is the sweet spot between credibility and variety.

---

## ADL-008: Performance Memory Database

**Date:** May 31, 2026
**Problem:** Need to learn what actually performs vs. what the AI scores say.

**Decision:** Store every post's topic, template, pillar, virality scores + engagement data (likes, saves, shares, DMs). Future topic selection weights toward historically high-performing patterns.

**Why:** The ultimate feedback loop. AI scores predict virality, but REAL engagement data is the ground truth. Over time, the system gets smarter.

---

## ADL-009: Hybrid Trend Research

**Date:** May 31, 2026
**Problem:** AI-only trend generation produces generic content. Web scraping alone is fragile.

**Decision:** 3-tier approach — (1) Scrape PIB/MSME/Startup India, (2) RSS feeds, (3) AI fallback with seasonal/evergreen topics.

**Why:** Real sources = freshness and credibility. AI fallback ensures the pipeline never stalls. Seasonal topics (tax season, scholarship deadlines) are predictable and valuable.

---

## ADL-010: Free-Only Architecture

**Date:** May 31, 2026
**Problem:** Budget constraint — no paid services.

**Decision:** All core functionality uses free tools — PIL (image composition), Gemini free tier (text), web scraping (trends), rule-based scoring (quality). AI image generation is architected but not activated until free provider confirmed.

**Why:** The system must work $0/month. PIL-based hybrid images + template system can produce professional-looking content without AI image generation.

---

## ADL-011: Headline Competition (15 Variations)

**Date:** May 31, 2026
**Problem:** First-generated headline is rarely the best. AI tends toward generic openings.

**Decision:** Generate 15+ headline variations using different emotional patterns (money, warning, curiosity, urgency, breaking, growth, official). Score all, pick the best.

**Why:** Headlines determine 80% of scroll-stop performance. Competition ensures quality.

---

## ADL-012: Layered Image Composition (Never Flat)

**Date:** May 31, 2026
**Problem:** Flat AI-generated images look obviously AI-made. Layered composition looks designed.

**Decision:** Always composite in 7 layers. Never generate a single flat graphic with text baked into AI output.

**Why:** Professional media companies layer their graphics. Text overlays from code are crisp and readable. AI-generated text is often garbled.

---

## ADL-013: Humanization Checker (Rejection Gate)

**Date:** May 31, 2026
**Problem:** LLM-generated content can sound robotic, brochure-like, or like a cyber cafe ad.

**Decision:** Rule-based rejection gate that checks against known bad patterns — robotic phrases ("it is important to note"), brochure style ("visit our center"), cyber cafe style ("all types of work"), keyword stuffing.

**Why:** The #1 reason AI content fails is it sounds like AI. This gate catches the most common failure modes.

---

## ADL-014: Regeneration Loop (Max 3 Attempts)

**Date:** May 31, 2026
**Problem:** What if a post fails virality scoring?

**Decision:** Auto-regenerate up to 3 times with feedback from failed metrics. If all 3 fail, publish the best version with a warning log.

**Why:** Perfectionism kills automation. 3 attempts balances quality with reliability. The best-of-3 is usually good enough.

---

## ADL-015: Config-Driven Everything

**Date:** May 31, 2026
**Problem:** Hardcoded values make changes require code edits.

**Decision:** All tunable parameters in config.yaml — face percentage, virality thresholds, CTA pool, headline patterns, color palette, template definitions.

**Why:** Non-technical users (you) can tune the system by editing YAML, not Python.

---

## ADL-016: Future Reels Support (Architectural)

**Date:** May 31, 2026
**Problem:** Instagram is shifting to Reels. Static posts alone won't be enough long-term.

**Decision:** Architecture supports video output (future/reels section in config). Same content pipeline (trend → topic → headline → caption) but output is video instead of image. Provider abstraction (Runway, Pika, Kling) mirrors image provider pattern.

**Why:** Building the architecture now prevents a rewrite later. The content intelligence layer is format-agnostic.

---

## ADL-017: No External Database (JSON Files)

**Date:** May 31, 2026
**Problem:** Need to store post history, performance data, trending topics.

**Alternatives considered:**
1. *SQLite* — Requires schema migrations, more complex. Overkill for this scale.
2. *PostgreSQL* — Requires server, not free self-hosted. Rejected.
3. *JSON files* — Simple, human-readable, no dependencies. **Selected.**

**Decision:** All data stored as JSON files in data/ directory. Post history, performance memory, trending topics, competitor DNA.

**Why:** Zero setup, zero cost, human-readable for debugging. At <1000 posts/year, JSON is more than fast enough. Can migrate to SQLite later if needed.

---

## ADL-018: Identity Manager (Deferred Photo Integration)

**Date:** May 31, 2026
**Problem:** User photos increase trust but photos aren't available yet.

**Decision:** Build identity_manager.py now with full architecture (photo loading, role selection, face percentage tracking, image prompt generation). System works without photos (uses AI-generated faces or no-face templates). When photos are provided, drop them in assets/identity/ and enable.

**Why:** The system shouldn't block on an external dependency. Architecture is ready, activation is a file copy.

---

## ADL-019: GitHub Actions for CI/CD

**Date:** May 31, 2026
**Problem:** Automated daily posting needs to run reliably.

**Decision:** GitHub Actions cron (already working) with PAT-based push auth. Workflow checks out code, runs pipeline, commits image, publishes to Instagram.

**Why:** Free, reliable, already working. No server to maintain.

---

## ADL-020: Content Pillars (8 Categories)

**Date:** May 31, 2026
**Problem:** Need diverse content that covers all Prisha services without being repetitive.

**Decision:** 8 content pillars — government_schemes, business_registration, loans_subsidies, compliance_updates, business_growth, student_services, success_stories, myth_vs_reality. Weighted rotation.

**Why:** Covers all 24 services naturally. Prevents the "only loan posts" problem. Matches how real media companies categorize content.
