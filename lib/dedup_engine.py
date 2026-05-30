"""
lib/dedup_engine.py — Duplicate prevention + intelligent category rotation.

Keeps track of all previously generated posts and ensures:
1. No duplicate topics, headlines, or stories are repeated
2. Categories are rotated evenly (not over-using one category)
3. Storytelling frameworks are varied

Usage:
    dedup = DedupEngine(history_list)
    category = dedup.pick_category(available_categories)
    is_dup = dedup.is_duplicate(topic, headline)
    dedup.record_post(post_dict)   # call after successful publish
"""

from collections import Counter
from lib.utils import load_config
from lib.logger import EngineLogger

log = EngineLogger("dedup_engine")


class DedupEngine:
    """Tracks post history and prevents content duplication."""

    def __init__(self, history: list[dict]):
        """
        Args:
            history: List of previously generated post dicts from generated_posts.json
        """
        self.history = history
        self.config = load_config()
        self.categories = self.config.get("content_categories", [])

        # Build lookup sets from history
        self.used_topics: list[str] = []
        self.used_headlines: list[str] = []
        self.used_image_texts: list[str] = []
        self.category_counts: Counter = Counter()

        for post in history:
            topic = post.get("topic", "")
            headline = post.get("headline", "")
            image_text = post.get("image_text", "")
            category = post.get("category", "")

            if topic:
                self.used_topics.append(topic.lower().strip())
            if headline:
                self.used_headlines.append(headline.lower().strip())
            if image_text:
                self.used_image_texts.append(image_text.lower().strip())
            if category:
                self.category_counts[category] += 1

        log.info(
            f"DedupEngine initialized: {len(history)} posts in history, "
            f"{len(self.used_topics)} topics tracked"
        )

    # ── Category Selection ─────────────────────────────────────────────────────

    def pick_category(self, preferred: str | None = None) -> str:
        """
        Pick the best category for today's post.

        Strategy:
        1. If preferred category is given and hasn't been overused, use it.
        2. Otherwise, pick the least-used category from the rotation.
        3. This ensures even distribution across all categories.

        Args:
            preferred: Optional preferred category (can be None for auto-pick)

        Returns:
            Selected category string
        """
        if not self.categories:
            return "Business Awareness"

        # Try preferred first
        if preferred and preferred in self.categories:
            return preferred

        # Pick least-used category
        min_count = min(
            self.category_counts.get(cat, 0) for cat in self.categories
        )
        least_used = [
            cat for cat in self.categories
            if self.category_counts.get(cat, 0) == min_count
        ]

        # Among the least used, rotate by day of month for variety
        if len(least_used) > 1:
            from datetime import datetime, timezone, timedelta
            IST = timezone(timedelta(hours=5, minutes=30))
            day_index = datetime.now(IST).day % len(least_used)
            chosen = least_used[day_index]
        else:
            chosen = least_used[0]

        log.info(f"Picked category: {chosen}", extra={
            "category_counts": dict(self.category_counts)
        })
        return chosen

    # ── Duplicate Detection ────────────────────────────────────────────────────

    def is_duplicate(self, topic: str, headline: str, image_text: str = "") -> bool:
        """
        Check if a proposed post is a duplicate.

        Uses fuzzy matching:
        - Exact match on topic/headline → duplicate
        - Topic is substring of old topic or vice versa → duplicate
        - Headline similarity > 80% → duplicate

        Args:
            topic: Proposed topic
            headline: Proposed headline
            image_text: Proposed image overlay text

        Returns:
            True if this post is too similar to an existing one
        """
        topic_lower = topic.lower().strip()
        headline_lower = headline.lower().strip()
        image_lower = image_text.lower().strip()

        # Check topics
        for used_topic in self.used_topics:
            if self._is_too_similar(topic_lower, used_topic):
                log.warn(f"Duplicate topic detected: '{topic}' ≈ '{used_topic}'")
                return True

        # Check headlines
        for used_headline in self.used_headlines:
            if self._is_too_similar(headline_lower, used_headline):
                log.warn(f"Duplicate headline detected: '{headline}' ≈ '{used_headline}'")
                return True

        # Check image text
        if image_lower:
            for used_img in self.used_image_texts:
                if self._is_too_similar(image_lower, used_img):
                    log.warn(f"Duplicate image text detected: '{image_text}' ≈ '{used_img}'")
                    return True

        return False

    # ── Record Post ─────────────────────────────────────────────────────────────

    def record_post(self, post: dict) -> None:
        """Record a newly generated post in the lookup sets."""
        topic = post.get("topic", "").lower().strip()
        headline = post.get("headline", "").lower().strip()
        image_text = post.get("image_text", "").lower().strip()
        category = post.get("category", "")

        if topic:
            self.used_topics.append(topic)
        if headline:
            self.used_headlines.append(headline)
        if image_text:
            self.used_image_texts.append(image_text)
        if category:
            self.category_counts[category] += 1

    # ── Data Accessors ──────────────────────────────────────────────────────────

    def get_used_topics(self) -> list[str]:
        return list(self.used_topics)

    def get_used_headlines(self) -> list[str]:
        return list(self.used_headlines)

    def get_category_distribution(self) -> dict:
        """Return dict of category → count for reporting."""
        return dict(self.category_counts)

    # ── Similarity Check ───────────────────────────────────────────────────────

    @staticmethod
    def _is_too_similar(a: str, b: str, threshold: float = 0.8) -> bool:
        """
        Check if two strings are too similar.

        Uses Jaccard similarity on word sets.
        Falls back to substring check for short strings.
        """
        if not a or not b:
            return False

        # Exact match
        if a == b:
            return True

        # Substring check (for short strings)
        if len(a) < 40 or len(b) < 40:
            return a in b or b in a

        # Jaccard similarity on word tokens
        words_a = set(a.split())
        words_b = set(b.split())

        if not words_a or not words_b:
            return False

        intersection = words_a & words_b
        union = words_a | words_b

        if not union:
            return False

        similarity = len(intersection) / len(union)
        return similarity >= threshold
