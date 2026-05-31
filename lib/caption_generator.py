"""
caption_generator.py — Generate dual-language captions (English + Roman Hinglish).

Structure: Hook → Benefit → Eligibility → Details → CTA → SEO → Hashtags
"""

import json
import random
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

IST = timezone(timedelta(hours=5, minutes=30))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

# Hinglish translation mappings (common phrases)
HINGLISH_MAP = {
    "is": "hai",
    "are": "hain",
    "the": "",
    "your": "aapka",
    "you": "aap",
    "this": "yeh",
    "that": "woh",
    "for": "ke liye",
    "with": "ke saath",
    "and": "aur",
    "or": "ya",
    "in": "mein",
    "on": "par",
    "from": "se",
    "to": "ko",
    "of": "ka",
    "we": "hum",
    "our": "hamara",
    "have": "hai",
    "has": "hai",
    "can": "sakte hain",
    "should": "chahiye",
    "must": "zaroori hai",
    "will": "karenge",
    "need": "chahiye",
    "know": "jaano",
    "apply": "apply karo",
    "register": "register karo",
    "benefit": "fayda",
    "government": "sarkar",
    "business": "business",
    "money": "paisa",
    "free": "muft",
    "easy": "aasan",
    "important": "zaroori",
    "new": "naya",
    "old": "purana",
    "time": "waqt",
    "year": "saal",
    "month": "maheena",
    "day": "din",
    "people": "log",
    "everyone": "sab log",
    "don't miss": "miss mat karo",
    "don't ignore": "ignore mat karo",
    "here's": "yaha hai",
    "how to": "kaise",
    "what": "kya",
    "why": "kyun",
    "when": " kab",
    "where": "kahan",
}


class CaptionGenerator:
    """Generate Instagram captions in English and Roman Hinglish."""

    def __init__(self):
        self.config = self._load_config()
        self.hashtag_pool = self._build_hashtag_pool()

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def generate_captions(self, headline: str, topic: str, category: str, info_blocks: list = None) -> dict:
        """
        Generate English and Hinglish captions.
        Returns: {"english": str, "hinglish": str, "seo_keywords": list, "hashtags": list}
        """
        info_blocks = info_blocks or []

        eng = self._generate_english(headline, topic, category, info_blocks)
        hing = self._generate_hinglish(headline, topic, category, info_blocks)
        seo = self._extract_seo_keywords(topic, category)
        hashtags = self._generate_hashtags(category, topic)

        return {
            "english": eng,
            "hinglish": hing,
            "seo_keywords": seo,
            "hashtags": hashtags,
        }

    def _generate_english(self, headline: str, topic: str, category: str, info_blocks: list) -> str:
        """Generate English caption with proper structure."""
        parts = []

        # HOOK (first line — must grab attention)
        hook = self._generate_hook(topic, category)
        parts.append(hook)

        # BODY (2-3 short paragraphs)
        body = self._generate_body(topic, category, info_blocks)
        parts.append("")
        parts.append(body)

        # BULLET POINTS (from info blocks)
        if info_blocks:
            parts.append("")
            for block in info_blocks[:5]:
                if isinstance(block, dict):
                    text = block.get("text", block.get("benefit", str(block)))
                    icon = block.get("icon", "✓")
                    parts.append(f"{icon} {text}")
                else:
                    parts.append(f"✓ {block}")

        # ENGAGEMENT PROMPT
        parts.append("")
        parts.append(self._random_engagement_prompt())

        # SEO KEYWORDS (natural inclusion)
        seo_line = self._seo_line(topic, category)
        if seo_line:
            parts.append("")
            parts.append(seo_line)

        return "\n".join(parts)

    def _generate_hinglish(self, headline: str, topic: str, category: str, info_blocks: list) -> str:
        """Generate Roman Hinglish caption."""
        parts = []

        # HOOK in Hinglish
        hook = self._generate_hinglish_hook(topic, category)
        parts.append(hook)

        # BODY in Hinglish
        body = self._generate_hinglish_body(topic, category)
        parts.append("")
        parts.append(body)

        # BULLETS in Hinglish
        if info_blocks:
            parts.append("")
            for block in info_blocks[:5]:
                if isinstance(block, dict):
                    text = block.get("text", block.get("benefit", str(block)))
                    icon = block.get("icon", "✓")
                    hing_text = self._to_hinglish(text)
                    parts.append(f"{icon} {hing_text}")
                else:
                    parts.append(f"✓ {self._to_hinglish(str(block))}")

        # ENGAGEMENT PROMPT in Hinglish
        parts.append("")
        parts.append(self._random_hinglish_engagement())

        return "\n".join(parts)

    def _generate_hook(self, topic: str, category: str) -> str:
        """Generate attention-grabbing first line."""
        hooks = [
            f"Did you know? {topic}",
            f"If you run a business, this is important.",
            f"Thousands of business owners are doing this. Are you?",
            f"Stop scrolling. This could save you lakhs.",
            f"Most business owners miss this. Don't be one of them.",
            f"This changes everything for small businesses.",
            f"Government just made this easier for you.",
            f"If you haven't done this yet, read carefully.",
            f"The one document every business needs.",
            f"Why smart business owners are applying for this.",
        ]
        return random.choice(hooks)

    def _generate_hinglish_hook(self, topic: str, category: str) -> str:
        """Generate Hinglish hook."""
        hooks = [
            f"Kya aapke business ke liye yeh zaroori hai?",
            f"Business owners, yeh padhiye — aapke liye important hai.",
            f"Hazaron logon ne yeh kiya. Aapne abhi tak nahi?",
            f"Scrolling band kariye. Yeh aapke liye valuable hai.",
            f"Zyada tar business owners yeh miss karte hain. Aap na hona.",
            f"Yeh small businesses ke liye game-changer hai.",
            f"Sarkar ne yeh aasan bana diya hai.",
            f"Agar aapne yeh abhi tak nahi kiya, toh dhyan se padhiye.",
            f"Woh document jo har business ko chahiye.",
            f"Smart business owners isliye apply kar rahe hain.",
        ]
        return random.choice(hooks)

    def _generate_body(self, topic: str, category: str, info_blocks: list) -> str:
        """Generate 2-3 paragraph body text."""
        bodies = {
            "loan_subsidy": "The government is offering financial support to help you grow your business. Whether you're starting fresh or expanding, this scheme can provide the funding you need without heavy collateral requirements. Many small business owners have already benefited — now it's your turn.",
            "government_schemes": "A new government scheme has been launched that directly benefits small business owners, entrepreneurs, and self-employed professionals. The application process is simple and can be completed online. Don't miss this opportunity to get official government recognition and benefits.",
            "business_registration": "Registering your business isn't just about legality — it's about unlocking benefits. From tax advantages to government tenders, a registered business has access to opportunities that unregistered ones don't. The process is simpler than you think.",
            "compliance": "Missing compliance deadlines can lead to heavy penalties and legal trouble. Stay updated with the latest rules and ensure your business is fully compliant. A small effort now can save you from big problems later.",
            "tax": "Tax season can be stressful, but knowing the right information can save you money. Here's what every business owner needs to know about the latest tax updates and how to stay on the right side of the law.",
            "certificates": "Government certificates are essential for accessing benefits, applying for loans, and proving your identity. The application process has been simplified — here's how you can get yours quickly.",
            "scholarship": "Education is expensive, but scholarships can make it affordable. If you or someone you know is eligible, don't miss this opportunity. The application deadline is approaching fast.",
        }
        return bodies.get(category, "This is an important update for every business owner and entrepreneur. Stay informed and take action before it's too late.")

    def _generate_hinglish_body(self, topic: str, category: str) -> str:
        """Generate Hinglish body."""
        bodies = {
            "loan_subsidy": "Sarkar business owners ko financial support de rahi hai. Chahe aap naya business start kar rahe ho ya expand kar rahe ho, yeh scheme aapko funding deti hai bina heavy collateral ke. Bahut se small business owners ne fayda uthaya hai — ab aapki baari hai.",
            "government_schemes": "Ek naya government scheme launch hua hai jo directly small business owners, entrepreneurs, aur self-employed professionals ko benefit karta hai. Application process simple hai aur online complete ho sakta hai. Yeh opportunity miss mat karo.",
            "business_registration": "Business register karna sirf legality ke baare mein nahi hai — yeh benefits unlock karna hai. Tax advantages se lekar government tenders tak, registered business ko milti hai aap opportunities jo unregistered ko nahi milti.",
            "compliance": "Compliance deadlines miss karna heavy penalties aur legal trouble la sakta hai. Latest rules se updated rahiye aur ensure kariye ki aapka business fully compliant hai. Ab thoda effort bahut bada problem bacha sakta hai.",
            "tax": "Tax season stressful ho sakta hai, lekin sahi information aapke paisa bacha sakti hai. Yahi har business owner ko latest tax updates ke baare mein jaanna chahiye.",
            "certificates": "Government certificates benefits access karne, loans apply karne, aur identity prove karne ke liye zaroori hain. Application process simplify ho chuka hai.",
            "scholarship": "Education mehengi hai, lekin scholarships ise affordable bana sakti hain. Agar aap ya aapke koi jaanne wale eligible hain, toh yeh opportunity miss mat karo.",
        }
        return bodies.get(category, "Yeh ek important update hai har business owner aur entrepreneur ke liye. Updated rahiye aur time se pehle action lijiye.")

    def _to_hinglish(self, text: str) -> str:
        """Convert English text to Roman Hinglish (simple word replacement)."""
        words = text.lower().split()
        result = []
        for word in words:
            clean = re.sub(r'[^\w]', '', word)
            if clean in HINGLISH_MAP:
                replacement = HINGLISH_MAP[clean]
                if replacement:
                    result.append(replacement)
            else:
                result.append(word)
        return " ".join(result)

    def _random_engagement_prompt(self) -> str:
        prompts = [
            "💬 Comment your business type below!",
            "📌 Save this for later!",
            "🔁 Share with a business owner who needs this!",
            "💬 Have questions? Drop them below!",
            "📩 DM us for help with registration!",
            "💬 Tag someone who needs to see this!",
        ]
        return random.choice(prompts)

    def _random_hinglish_engagement(self) -> str:
        prompts = [
            "💬 Comment mein apna business type batao!",
            "📌 Isse save karo baad ke liye!",
            "🔁 Business owner dost ke saath share karo!",
            "💬 Koi sawaal hai? Neeche comment karo!",
            "📩 Registration mein help ke liye DM karo!",
            "💬 Kisi ko tag karo jisko yeh dekhna chahiye!",
        ]
        return random.choice(prompts)

    def _seo_line(self, topic: str, category: str) -> str:
        """Generate SEO keyword line."""
        keywords = self._extract_seo_keywords(topic, category)
        if keywords:
            return " | ".join(keywords[:5])
        return ""

    def _extract_seo_keywords(self, topic: str, category: str) -> list:
        """Extract SEO keywords from topic and category."""
        keywords = []
        topic_lower = topic.lower()

        keyword_map = {
            "gst": "GST Registration",
            "udyam": "Udyam Registration",
            "msme": "MSME",
            "fssai": "FSSAI Registration",
            "shop act": "Shop Act License",
            "startup": "Startup India",
            "mudra": "Mudra Loan",
            "pmegp": "PMEGP Loan",
            "vishwakarma": "PM Vishwakarma",
            "loan": "Business Loan",
            "subsidy": "Government Subsidy",
            "scholarship": "Scholarship",
            "certificate": "Government Certificate",
            "pan": "PAN Card",
            "aadhaar": "Aadhaar",
            "passport": "Passport",
            "caste": "Caste Certificate",
            "income": "Income Certificate",
            "domicile": "Domicile Certificate",
            "itr": "ITR Filing",
            "compliance": "Business Compliance",
            "registration": "Business Registration",
            "maharashtra": "Maharashtra Government Scheme",
        }

        for key, keyword in keyword_map.items():
            if key in topic_lower and keyword not in keywords:
                keywords.append(keyword)

        # Always include brand
        keywords.append("Prisha Online Documentation")
        return keywords

    def _generate_hashtags(self, category: str, topic: str) -> list:
        """Generate 25-30 hashtags mixing large, medium, niche, and local."""
        base = ["PrishaOnlineDocumentation", "BusinessRegistration", "GovernmentScheme", "India", "Maharashtra"]

        category_tags = {
            "loan_subsidy": ["MudraLoan", "PMEGP", "BusinessLoan", "SmallBusinessLoan", "GovernmentLoan", "CollateralFreeLoan", "StartupFunding", "MSMELoan"],
            "government_schemes": ["GovernmentScheme", "SarkarYojana", "GovernmentBenefit", "OfficialScheme", "IndiaScheme", "MaharashtraScheme"],
            "business_registration": ["GSTRegistration", "UdyamRegistration", "MSME", "StartupIndia", "FSSAI", "ShopAct", "CompanyRegistration", "BusinessIndia"],
            "compliance": ["BusinessCompliance", "GSTFiling", "ITRFiling", "TaxFiling", "BusinessUpdate", "LegalCompliance"],
            "tax": ["GST", "IncomeTax", "TaxSaving", "GSTUpdate", "TaxTips", "BusinessTax"],
            "certificates": ["Certificate", "GovernmentCertificate", "OnlineApplication", "DocumentServices", "PANCard", "AadhaarCard"],
            "scholarship": ["Scholarship", "StudentScholarship", "Education", "GovernmentScholarship", "StudyIndia"],
        }

        tags = base + category_tags.get(category, ["BusinessIndia", "SmallBusiness"])

        # Add topic-specific tags
        topic_words = re.findall(r'\b[A-Z][a-z]+\b', topic)
        for word in topic_words[:3]:
            if word not in tags and len(word) > 2:
                tags.append(word)

        # Add local tags
        tags.extend(["Mumbai", "MaharashtraBusiness", "IndianBusiness"])

        # Ensure 25-30
        while len(tags) < 25:
            tags.append("BusinessTips")

        return list(dict.fromkeys(tags))[:30]  # Deduplicate and cap at 30

    def _build_hashtag_pool(self) -> dict:
        """Build hashtag pool from config."""
        return {}


def main():
    gen = CaptionGenerator()
    result = gen.generate_captions(
        headline="💰 Government Giving Rs 25 Lakh Subsidy — Are You Eligible?",
        topic="PMEGP loan scheme gives Rs 25 lakh subsidy to small businesses",
        category="loan_subsidy",
        info_blocks=[
            {"text": "Up to Rs 25 lakh subsidy", "icon": "💰"},
            {"text": "No collateral required", "icon": "✓"},
            {"text": "For new and existing businesses", "icon": "🏢"},
            {"text": "Simple online application", "icon": "📱"},
        ],
    )
    print("=== ENGLISH ===")
    print(result["english"])
    print("\n=== HINGLISH ===")
    print(result["hinglish"])
    print("\n=== HASHTAGS ===")
    print(" ".join(f"#{h}" for h in result["hashtags"]))


if __name__ == "__main__":
    main()
