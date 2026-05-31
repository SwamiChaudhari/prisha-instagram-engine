"""
performance_memory.py — Store and analyze post performance data.
Future: feed engagement data back into topic selection and headline scoring.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERFORMANCE_PATH = PROJECT_ROOT / "data" / "performance_memory.json"


class PerformanceMemory:
    """Store and retrieve post performance data."""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        try:
            if PERFORMANCE_PATH.exists():
                with open(PERFORMANCE_PATH) as f:
                    return json.load(f)
        except Exception:
            pass
        return {"posts": [], "summary": {}}

    def _save(self):
        PROJECT_ROOT.joinpath("data").mkdir(parents=True, exist_ok=True)
        with open(PERFORMANCE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def record_post(self, post_data: dict, engagement: dict = None):
        """
        Record a published post.
        post_data: headline, topic, template, pillar, category, virality_scores, cta
        engagement: (filled later via Instagram API or manual input)
            reach, likes, saves, shares, comments, profile_visits, dms
        """
        record = {
            "id": f"post_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}",
            "date": datetime.now(IST).isoformat(),
            "headline": post_data.get("headline", ""),
            "topic": post_data.get("topic", ""),
            "template": post_data.get("template", ""),
            "pillar": post_data.get("pillar", ""),
            "category": post_data.get("category", ""),
            "virality_scores": post_data.get("virality_scores", {}),
            "overall_virality": post_data.get("overall_virality", 0),
            "reference_similarity": post_data.get("reference_similarity", 0),
            "cta": post_data.get("cta", ""),
            "use_face": post_data.get("use_face", False),
            "engagement": engagement or {
                "reach": 0,
                "likes": 0,
                "saves": 0,
                "shares": 0,
                "comments": 0,
                "profile_visits": 0,
                "dms": 0,
            },
        }
        self.data["posts"].append(record)
        self._update_summary()
        self._save()

    def update_engagement(self, post_id: str, engagement: dict):
        """Update engagement data for a published post."""
        for post in self.data["posts"]:
            if post["id"] == post_id:
                post["engagement"].update(engagement)
                break
        self._update_summary()
        self._save()

    def get_best_performing(self, metric: str = "likes", limit: int = 10) -> list:
        """Get top performing posts by metric."""
        posts_with_data = [p for p in self.data["posts"] if p["engagement"].get("likes", 0) > 0]
        posts_with_data.sort(key=lambda x: x["engagement"].get(metric, 0), reverse=True)
        return posts_with_data[:limit]

    def get_template_performance(self) -> dict:
        """Get average performance by template type."""
        template_data = {}
        for post in self.data["posts"]:
            t = post.get("template", "unknown")
            if t not in template_data:
                template_data[t] = {"count": 0, "total_likes": 0, "total_saves": 0, "total_shares": 0}
            template_data[t]["count"] += 1
            template_data[t]["total_likes"] += post["engagement"].get("likes", 0)
            template_data[t]["total_saves"] += post["engagement"].get("saves", 0)
            template_data[t]["total_shares"] += post["engagement"].get("shares", 0)

        # Calculate averages
        for t in template_data:
            c = template_data[t]["count"]
            template_data[t]["avg_likes"] = round(template_data[t]["total_likes"] / c, 1)
            template_data[t]["avg_saves"] = round(template_data[t]["total_saves"] / c, 1)
            template_data[t]["avg_shares"] = round(template_data[t]["total_shares"] / c, 1)

        return template_data

    def get_pillar_performance(self) -> dict:
        """Get average performance by pillar."""
        pillar_data = {}
        for post in self.data["posts"]:
            p = post.get("pillar", "unknown")
            if p not in pillar_data:
                pillar_data[p] = {"count": 0, "total_likes": 0, "total_saves": 0}
            pillar_data[p]["count"] += 1
            pillar_data[p]["total_likes"] += post["engagement"].get("likes", 0)
            pillar_data[p]["total_saves"] += post["engagement"].get("saves", 0)

        for p in pillar_data:
            c = pillar_data[p]["count"]
            pillar_data[p]["avg_likes"] = round(pillar_data[p]["total_likes"] / c, 1)
            pillar_data[p]["avg_saves"] = round(pillar_data[p]["total_saves"] / c, 1)

        return pillar_data

    def get_insights(self) -> dict:
        """Generate insights for content optimization."""
        total = len(self.data["posts"])
        if total == 0:
            return {"message": "No posts yet. Publish first!"}

        best = self.get_best_performing("likes", 5)
        template_perf = self.get_template_performance()
        pillar_perf = self.get_pillar_performance()

        # Find best template
        best_template = max(template_perf.items(), key=lambda x: x[1].get("avg_likes", 0)) if template_perf else None
        best_pillar = max(pillar_perf.items(), key=lambda x: x[1].get("avg_likes", 0)) if pillar_perf else None

        # Face vs no-face comparison
        face_posts = [p for p in self.data["posts"] if p.get("use_face")]
        no_face_posts = [p for p in self.data["posts"] if not p.get("use_face")]
        face_avg_likes = sum(p["engagement"].get("likes", 0) for p in face_posts) / max(len(face_posts), 1)
        no_face_avg_likes = sum(p["engagement"].get("likes", 0) for p in no_face_posts) / max(len(no_face_posts), 1)

        return {
            "total_posts": total,
            "best_template": best_template[0] if best_template else None,
            "best_pillar": best_pillar[0] if best_pillar else None,
            "face_avg_likes": round(face_avg_likes, 1),
            "no_face_avg_likes": round(no_face_avg_likes, 1),
            "face_better": face_avg_likes > no_face_avg_likes,
            "template_performance": template_perf,
            "pillar_performance": pillar_perf,
            "top_5_posts": [{"headline": p["headline"], "likes": p["engagement"].get("likes", 0)} for p in best],
        }

    def _update_summary(self):
        """Update summary statistics."""
        posts = self.data["posts"]
        self.data["summary"] = {
            "total_posts": len(posts),
            "last_updated": datetime.now(IST).isoformat(),
            "posts_with_engagement": sum(1 for p in posts if p["engagement"].get("likes", 0) > 0),
        }


if __name__ == "__main__":
    mem = PerformanceMemory()
    mem.record_post(
        {
            "headline": "💰 Government Giving Rs 25 Lakh — Are You Eligible?",
            "topic": "PMEGP loan scheme",
            "template": "opportunity_alert",
            "pillar": "loans_subsidies",
            "category": "loan_subsidy",
            "overall_virality": 85.5,
            "use_face": True,
            "cta": "📩 DM 'INFO'",
        },
        {"reach": 1200, "likes": 85, "saves": 42, "shares": 15, "comments": 8, "profile_visits": 23, "dms": 5}
    )
    print("Recorded post")
    print(json.dumps(mem.get_insights(), indent=2))
