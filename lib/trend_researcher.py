"""
trend_researcher.py — Research trending government topics from real sources.

Priority: 1) Web scraping 2) RSS feeds 3) AI fallback
Sources: PIB, MSME, Startup India, government news sites
"""

import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
import yaml

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
TRENDING_PATH = DATA_DIR / "trending_topics.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class TrendResearcher:
    """Research trending government and business topics from multiple sources."""

    def __init__(self):
        self.config = self._load_config()
        self.sources = {
            "pib": "https://pib.gov.in",
            "msme": "https://msme.gov.in",
            "startup_india": "https://www.startupindia.gov.in",
            "india_gov": "https://www.india.gov.in",
            "maharashtra": "https://www.maharashtra.gov.in",
        }

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def research_all(self) -> list:
        """Run all scrapers and return combined topic list."""
        all_topics = []
        seen_topics = set()

        # Source 1: PIB Press Releases via web scraping
        pib_topics = self._scrape_pib()
        for t in pib_topics:
            key = t["topic"].lower()[:50]
            if key not in seen_topics:
                seen_topics.add(key)
                all_topics.append(t)

        # Source 2: MSME updates
        msme_topics = self._scrape_msme()
        for t in msme_topics:
            key = t["topic"].lower()[:50]
            if key not in seen_topics:
                seen_topics.add(key)
                all_topics.append(t)

        # Source 3: General government news / AI fallback
        if len(all_topics) < 5:
            fallback_topics = self._ai_fallback_topics()
            for t in fallback_topics:
                key = t["topic"].lower()[:50]
                if key not in seen_topics:
                    seen_topics.add(key)
                    all_topics.append(t)

        # Cache results
        self._cache_topics(all_topics)
        return all_topics

    def get_cached(self) -> list:
        """Load from cache if less than 24 hours old."""
        if not TRENDING_PATH.exists():
            return []
        try:
            with open(TRENDING_PATH) as f:
                data = json.load(f)
            cached_at = datetime.fromisoformat(data.get("cached_at", ""))
            age_hours = (datetime.now(IST) - cached_at).total_seconds() / 3600
            if age_hours < 24:
                return data.get("topics", [])
        except Exception:
            pass
        return []

    def get_trending(self, category: str = None, limit: int = 20) -> list:
        """Get trending topics, optionally filtered by category."""
        cached = self.get_cached()
        topics = cached if cached else self.research_all()
        if category:
            topics = [t for t in topics if t.get("category") == category]
        # Sort by estimated impact
        topics.sort(key=lambda x: x.get("estimated_impact", 5), reverse=True)
        return topics[:limit]

    # ── PIB Scraper ──────────────────────────────────────────────────────────

    def _scrape_pib(self) -> list:
        """Scrape latest PIB press releases."""
        topics = []
        try:
            # PIB latest releases page
            url = "https://pib.gov.in/PressReleasePage.aspx?PRID=0"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                # Extract press release titles from the page
                text = resp.text
                # PIB pages have press release links
                links = re.findall(
                    r'href=["\'](/PressReleaseIframePage\.aspx\?PRID=\d+)["\'][^>]*>([^<]+)<',
                    text
                )
                for link, title in links[:15]:
                    title = title.strip()
                    if len(title) > 20 and len(title) < 200:
                        category = self._categorize_topic(title)
                        topics.append({
                            "topic": title,
                            "headline": self._generate_headline(title),
                            "source": "pib",
                            "category": category,
                            "date": datetime.now(IST).isoformat(),
                            "estimated_impact": self._estimate_impact(title, category),
                            "url": f"https://pib.gov.in{link}",
                            "summary": title,
                        })
        except Exception as e:
            pass
        return topics

    # ── MSME Scraper ─────────────────────────────────────────────────────────

    def _scrape_msme(self) -> list:
        """Scrape MSME-related updates."""
        topics = []
        try:
            url = "https://msme.gov.in/"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                text = resp.text
                # Extract news/notifications
                links = re.findall(
                    r'href=["\']([^"\']+)["\'][^>]*>([^<]*(?:MSME|UDYAM|scheme|loan|subsidy|registration)[^<]*)<',
                    text, re.IGNORECASE
                )
                for link, title in links[:10]:
                    title = title.strip()
                    if 15 < len(title) < 150:
                        topics.append({
                            "topic": title,
                            "headline": self._generate_headline(title),
                            "source": "msme",
                            "category": "government_scheme",
                            "date": datetime.now(IST).isoformat(),
                            "estimated_impact": 7,
                            "url": link if link.startswith("http") else f"https://msme.gov.in{link}",
                            "summary": title,
                        })
        except Exception:
            pass
        return topics

    # ── AI Fallback (when scraping doesn't yield enough) ─────────────────────

    def _ai_fallback_topics(self) -> list:
        """Generate trending-style topics based on current date and known schemes."""
        now = datetime.now(IST)
        month = now.month
        year = now.year

        # Seasonal/cyclical topics
        seasonal = []
        # Financial year topics (April-March)
        if month in [1, 2, 3]:
            seasonal.extend([
                {"topic": f"Last chance: ITR filing deadline approaching", "category": "compliance", "impact": 9},
                {"topic": f"New financial year scheme announcements", "category": "government_schemes", "impact": 8},
                {"topic": f"GST annual return deadline reminder", "category": "compliance", "impact": 8},
            ])
        if month in [4, 5]:
            seasonal.extend([
                {"topic": f"New financial year: Registrations surge for startups", "category": "business_registration", "impact": 7},
                {"topic": f"Mudra Loan applications open for new businesses", "category": "loan_subsidy", "impact": 9},
            ])
        if month in [6, 7, 8]:
            seasonal.extend([
                {"topic": f"Monsoon business opportunities for MSMEs", "category": "business_growth", "impact": 6},
                {"topic": f"Scholarship applications open for students", "category": "scholarship", "impact": 8},
                {"topic": f"Mid-year GST compliance checkup for businesses", "category": "compliance", "impact": 7},
            ])
        if month in [9, 10]:
            seasonal.extend([
                {"topic": f"Festive season business registration offers", "category": "business_registration", "impact": 7},
                {"topic": f"Pre-festival GST rate updates for businesses", "category": "tax", "impact": 8},
                {"topic": f"Diwali business loan offers from banks", "category": "loan_subsidy", "impact": 9},
            ])
        if month in [11, 12]:
            seasonal.extend([
                {"topic": f"Year-end compliance deadlines every business must know", "category": "compliance", "impact": 9},
                {"topic": f"New government schemes announced in winter session", "category": "government_schemes", "impact": 8},
                {"topic": f"GST audit preparation tips for businesses", "category": "tax", "impact": 7},
            ])

        # Evergreen high-impact topics (always relevant)
        evergreen = [
            {"topic": "PMEGP loan: Government gives up to Rs 25 lakh subsidy", "category": "loan_subsidy", "impact": 10},
            {"topic": "Mudra Loan: Get up to Rs 10 lakh without collateral", "category": "loan_subsidy", "impact": 10},
            {"topic": "PM Vishwakarma Scheme: Free registration and toolkit for artisans", "category": "government_schemes", "impact": 9},
            {"topic": "Udyam Registration: Free government recognition for MSMEs", "category": "business_registration", "impact": 9},
            {"topic": "GST Registration mandatory requirements changed", "category": "compliance", "impact": 8},
            {"topic": "Startup India tax benefits you didn't know about", "category": "business_growth", "impact": 8},
            {"topic": "FSSAI license required for home-based food businesses", "category": "compliance", "impact": 7},
            {"topic": "Shop Act license online process and penalties", "category": "compliance", "impact": 7},
            {"topic": "Maharashtra government schemes for small businesses", "category": "government_schemes", "impact": 9},
            {"topic": "PAN card now mandatory for business above Rs 5 lakh turnover", "category": "registration", "impact": 6},
            {"topic": "Caste certificate online application process simplified", "category": "certificates", "impact": 7},
            {"topic": "Income certificate required for scholarship applications", "category": "certificates", "impact": 7},
            {"topic": "Scholarship deadline approaching for SC/ST/OBC students", "category": "scholarship", "impact": 8},
            {"topic": "Aadhaar linking deadline for bank accounts and PAN", "category": "compliance", "impact": 7},
            {"topic": "Passport application new rules and fast-track process", "category": "certificates", "impact": 6},
        ]

        # Combine seasonal + evergreen, prioritize seasonal
        all_fallback = seasonal + evergreen
        topics = []
        for item in all_fallback:
            topics.append({
                "topic": item["topic"],
                "headline": self._generate_headline(item["topic"]),
                "source": "ai_fallback",
                "category": item["category"],
                "date": now.isoformat(),
                "estimated_impact": item["impact"],
                "url": "",
                "summary": item["topic"],
            })
        return topics

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _categorize_topic(self, title: str) -> str:
        """Categorize a topic based on keywords."""
        title_lower = title.lower()
        if any(w in title_lower for w in ["loan", "mudra", "pmegp", "credit", "fund", "subsidy", "financial assistance"]):
            return "loan_subsidy"
        if any(w in title_lower for w in ["gst", "tax", "income tax", "itr", "tds"]):
            return "tax"
        if any(w in title_lower for w in ["register", "registration", "udyam", "msme", "startup", "company", "fssai", "shop act"]):
            return "registration"
        if any(w in title_lower for w in ["compliance", "deadline", "penalty", "rule", "regulation", "mandatory"]):
            return "compliance"
        if any(w in title_lower for w in ["scheme", "yojana", "government", "ministry", "pm", "launch"]):
            return "government_schemes"
        if any(w in title_lower for w in ["scholarship", "student", "education", "exam"]):
            return "scholarship"
        return "announcement"

    def _generate_headline(self, topic: str) -> str:
        """Convert a topic into a viral-style headline."""
        # Extract key elements
        topic_lower = topic.lower()

        # Money-related
        amounts = re.findall(r'rs\.?\s*[\d,]+(?:\s*(?:lakh|crore|thousand))?', topic_lower)
        if amounts:
            return f"💰 Government Giving {amounts[0].upper()} Support — Are You Eligible?"

        # Deadline-related
        if any(w in topic_lower for w in ["deadline", "last date", "due", "expiry"]):
            return f"⚠️ Deadline Alert: {topic[:60]}"

        # New scheme
        if any(w in topic_lower for w in ["launch", "new", "announce", "scheme"]):
            return f"🏛 New Government Scheme: {topic[:60]}"

        # Compliance
        if any(w in topic_lower for w in ["mandatory", "required", "must", "penalty"]):
            return f"🚨 Important Update: {topic[:60]}"

        # Default
        return f"📢 {topic[:70]}"

    def _estimate_impact(self, title: str, category: str) -> int:
        """Estimate public impact of a topic (1-10)."""
        title_lower = title.lower()
        score = 5  # baseline

        # Money = high impact
        if any(w in title_lower for w in ["lakh", "crore", "rs", "loan", "subsidy", "fund"]):
            score += 3
        # Urgency = high impact
        if any(w in title_lower for w in ["deadline", "last date", "urgent", "alert", "warning"]):
            score += 2
        # New = medium impact
        if any(w in title_lower for w in ["new", "launch", "announce", "update"]):
            score += 1
        # Government scheme = medium impact
        if category == "government_schemes":
            score += 1
        # Loan/subsidy = high impact
        if category == "loan_subsidy":
            score += 2
        # Compliance = medium-high
        if category == "compliance":
            score += 1

        return min(score, 10)

    def _cache_topics(self, topics: list):
        """Cache trending topics to disk."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "cached_at": datetime.now(IST).isoformat(),
            "count": len(topics),
            "topics": topics,
        }
        with open(TRENDING_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """Test trend researcher."""
    researcher = TrendResearcher()
    print("Researching trending topics...")
    topics = researcher.research_all()
    print(f"Found {len(topics)} topics:")
    for t in topics[:5]:
        print(f"  [{t['category']}] {t['headline']}")
        print(f"    Impact: {t['estimated_impact']}/10 | Source: {t['source']}")
        print()


if __name__ == "__main__":
    main()
