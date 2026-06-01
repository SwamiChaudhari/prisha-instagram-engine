"""
caption_generator.py — Prisha Online Centre Caption Engine v2.0

Generates bilingual (English + Marathi) captions following the
CAPTION_FRAMEWORK.md structure. Trust-first, local business tone.

Structure:
1. Hook (attention-grabbing)
2. English explanation
3. Marathi explanation
4. Benefits (checkmark bullets)
5. Why Choose Prisha (trust section)
6. Call to action
7. Contact details
8. Brand tagline
9. Hashtags (8-12)
"""

import random
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

# ── Contact Info (centralized) ──────────────────────────────────────────────
CONTACT = {
    "address": "Balaji Nagar, Ambi Road, Varale",
    "phone": "9145564291",
    "tagline_en": "Customer Satisfaction is Our Priority",
    "tagline_mr": "ग्राहक सेवा हाच आमचा उद्देश",
}

# ── Hook Templates ──────────────────────────────────────────────────────────
HOOKS = {
    "loan_subsidy": {
        "en": [
            "💰 You may be missing benefits worth lakhs.",
            "⚠️ Most business owners don't know about this funding option.",
            "❌ Don't let your business miss this government support.",
            "📢 Important funding update for small business owners.",
        ],
        "mr": [
            "💰 तुम्ही लाखांच्या फायद्यांना मागे टाकत असाल!",
            "⚠️ बहुतेक व्यवसाय मालकांना या निधीबद्दल माहिती नाही.",
            "❌ तुमचा व्यवसाय हे सरकारी सहाय्य गमावू नका.",
            "📢 लहान व्यवसाय मालकांसाठी महत्त्वाची निधी अपडेट.",
        ],
    },
    "government_schemes": {
        "en": [
            "📢 New government scheme — are you eligible?",
            "⚠️ Most business owners don't know this.",
            "💰 Benefits you might be missing right now.",
            "📋 Important update for every business owner.",
        ],
        "mr": [
            "📢 नवीन सरकारी योजना — तुम्ही पात्र आहात का?",
            "⚠️ बहुतेक व्यवसाय मालकांना हे माहित नाही.",
            "💰 फायदे जे तुम्ही आत्ताच गमावत असाल.",
            "📋 प्रत्येक व्यवसाय मालकासाठी महत्त्वाची अपडेट.",
        ],
    },
    "business_registration": {
        "en": [
            "❌ Don't operate without proper registration.",
            "⚠️ Is your business legally registered?",
            "📋 Registration unlocks benefits you didn't know existed.",
            "💰 Registered businesses get access to exclusive benefits.",
        ],
        "mr": [
            "❌ योग्य नोंदणीशिवाय व्यवसाय करू नका.",
            "⚠️ तुमचा व्यवसाय कायदेशीर नोंदणीकृत आहे का?",
            "📋 नोंदणीमुळे असे फायदे मिळतात जे तुम्हाला माहीत नव्हते.",
            "💰 नोंदणीकृत व्यवसायांना विशेष फायद्यांची सोय मिळते.",
        ],
    },
    "compliance": {
        "en": [
            "⚠️ Missing deadlines can cost you heavily.",
            "❌ Don't ignore this compliance update.",
            "📅 Important deadline approaching for business owners.",
            "⚠️ Stay compliant, stay protected.",
        ],
        "mr": [
            "⚠️ डेडलाइन चुकवल्यास मोठा फटका बसू शकतो.",
            "❌ ही कंप्लायन्स अपडेट दुर्लक्ष करू नका.",
            "📅 व्यवसाय मालकांसाठी महत्त्वाची डेडलाइन जवळ आली आहे.",
            "⚠️ कंप्लायंट रहा, सुरक्षित रहा.",
        ],
    },
    "taxation": {
        "en": [
            "💰 Save money this tax season — read this.",
            "⚠️ Don't overpay taxes. Know your deductions.",
            "📋 Tax update every business owner needs.",
            "❌ Common tax mistakes that cost business owners lakhs.",
        ],
        "mr": [
            "💰 या टॅक्स सीजनमध्ये पैसे वाचवा — हे वाचा.",
            "⚠️ जास्त टॅक्स देऊ नका. तुमचे कपात जाणून घ्या.",
            "📋 प्रत्येक व्यवसाय मालकाला हवी असलेली टॅक्स अपडेट.",
            "❌ सामान्य टॅक्स चुका ज्यामुळे व्यवसाय मालकांना लाखांचा फटका बसतो.",
        ],
    },
    "startup_resources": {
        "en": [
            "🚀 Starting a business? Read this first.",
            "💡 Smart entrepreneurs know about these resources.",
            "📢 Government support available for new startups.",
            "⚠️ Don't start without knowing these benefits.",
        ],
        "mr": [
            "🚀 व्यवसाय सुरू करत आहात? प्रथम हे वाचा.",
            "💡 समजदार उद्योजकांना ही संस्था माहित असतात.",
            "📢 नवीन स्टार्टअप्ससाठी सरकारी सहाय्य उपलब्ध आहे.",
            "⚠️ हे फायदे न जाणता सुरू करू नका.",
        ],
    },
}

# ── Body Templates (English) ───────────────────────────────────────────────
BODY_EN = {
    "loan_subsidy": [
        "The government is offering financial support to help small businesses grow. Whether you're starting fresh or expanding, this scheme can provide funding without heavy collateral requirements.",
        "Many small business owners have already benefited from this scheme. The application process is straightforward, and the support team is available to guide you through every step.",
    ],
    "government_schemes": [
        "A new government scheme has been launched that directly benefits small business owners, entrepreneurs, and self-employed professionals.",
        "The application process is simple and can be completed with proper documentation. Don't miss this opportunity to get official government recognition and benefits.",
    ],
    "business_registration": [
        "Registering your business isn't just about legality — it's about unlocking benefits that help you grow.",
        "From tax advantages to government tenders, a registered business has access to opportunities that unregistered ones don't. The process is simpler than you think.",
    ],
    "compliance": [
        "Missing compliance deadlines can lead to heavy penalties and legal trouble for your business.",
        "Stay updated with the latest rules and ensure your business is fully compliant. A small effort now can save you from big problems later.",
    ],
    "taxation": [
        "Tax season can be stressful, but knowing the right information can save you money and prevent penalties.",
        "Here's what every business owner needs to know about the latest tax updates and how to stay on the right side of the law.",
    ],
    "startup_resources": [
        "Starting a business is exciting, but knowing the right resources and government support can make all the difference.",
        "From registration to funding to compliance, having the right guidance from the start sets you up for long-term success.",
    ],
}

# ── Body Templates (Marathi) ────────────────────────────────────────────────
BODY_MR = {
    "loan_subsidy": [
        "सरकार लहान व्यवसाय वाढवण्यासाठी आर्थिक सहाय्य देत आहे. तुम्ही नवीन व्यवसाय सुरू करत असाल किंवा विस्तार करत असाल, ही योजना जास्त कोलेटरलशिवाय निधी उपलब्ध करून देते.",
        "बरेच लहान व्यवसाय मालकांनी या योजनेचा फायदा घेतला आहे. अर्ज प्रक्रिया सोपी आहे आणि सपोर्ट टीम तुम्हाला प्रत्येक पायरीवर मार्गदर्शन करण्यासाठी उपलब्ध आहे.",
    ],
    "government_schemes": [
        "एक नवीन सरकारी योजना सुरू करण्यात आली आहे जी थेट लहान व्यवसाय मालकांना, उद्योजकांना आणि स्वयंरोजगार व्यावसायिकांना फायदेशीर ठरते.",
        "अर्ज प्रक्रिया सोपी आहे आणि योग्य कागदपत्रांसह पूर्ण केली जाऊ शकते. अधिकृत सरकाने मान्यता आणि फायदे मिळवण्याची ही संधी गमावू नका.",
    ],
    "business_registration": [
        "व्यवसाय नोंदणी करणे हे फक्त कायदेशीरतेबद्दल नाही — हे तुम्हाला वाढण्यास मदत करणाऱ्या फायदे उघड करणे आहे.",
        "कर सवलतीपासून ते सरकारी निविदांपर्यंत, नोंदणीकृत व्यवसायांना अशी संधी मिळतात जी नोंदणी न केलेल्यांना मिळत नाहीत. प्रक्रिया तुम्हाला वाटल्यापेक्षा सोपी आहे.",
    ],
    "compliance": [
        "कंप्लायन्स डेडलाइन चुकवल्यास तुमच्या व्यवसायासाठी जबरदस्त दंड आणि कायदेशीर अडचणी निर्माण होऊ शकतात.",
        "नियमांच्या नवीनतम अपडेटसह अपडेट रहा आणि तुमचा व्यवसाय पूर्णपणे कंप्लायंट असल्याची खात्री करा. आता थोडा प्रयत्न नंतर मोठ्या समस्येपासून वाचवू शकतो.",
    ],
    "taxation": [
        "टॅक्स सीजन ताणदायक असू शकते, पण योग्य माहिती जाणून घेणे तुमचे पैसे वाचवू शकते आणि दंड टाळू शकते.",
        "नवीनतम टॅक्स अपडेट आणि कायद्याच्या योग्य बाजूने कसे राहावे हे प्रत्येक व्यवसाय मालकाला जाणून घेणे आवश्यक आहे.",
    ],
    "startup_resources": [
        "व्यवसाय सुरू करणे रोमांचक आहे, पण योग्य संस्था आणि सरकारी सहाय्य जाणून घेणे सर्व वेगळे करू शकते.",
        "नोंदणीपासून निधीपर्यंत कंप्लायन्सपर्यंत, सुरुवातीपासून योग्य मार्गदर्शन घेणे दीर्घकालीन यशासाठी तुम्हाला तयार करते.",
    ],
}

# ── Benefits by Category ────────────────────────────────────────────────────
BENEFITS = {
    "loan_subsidy": [
        "Faster approval process",
        "Government-recognized funding",
        "Better business credibility",
        "Access to applicable schemes",
        "Proper documentation support",
        "Collateral-free options available",
    ],
    "government_schemes": [
        "Scheme guidance and awareness",
        "Registration assistance",
        "Documentation support",
        "Application assistance",
        "Business growth support",
        "Government liaison support",
    ],
    "business_registration": [
        "Quick registration process",
        "Lifetime validity",
        "Tax benefits unlocked",
        "Government recognized",
        "Access to tenders and loans",
        "Professional business identity",
    ],
    "compliance": [
        "Avoid penalties and fines",
        "Stay legally protected",
        "Timely filing support",
        "Complete documentation",
        "Expert guidance",
        "Regular compliance updates",
    ],
    "taxation": [
        "Maximize your deductions",
        "Avoid tax penalties",
        "Proper filing support",
        "Up-to-date tax guidance",
        "ITR filing assistance",
        "GST compliance support",
    ],
    "startup_resources": [
        "End-to-end startup guidance",
        "Registration to funding support",
        "Government scheme awareness",
        "Compliance roadmap",
        "Documentation assistance",
        "Growth strategy support",
    ],
}

# ── Why Choose Prisha (Trust Section) ──────────────────────────────────────
TRUST_SECTION = [
    "🤝 Reliable Guidance",
    "📄 Complete Documentation Support",
    "⚡ Fast Process",
    "📞 Dedicated Assistance",
]

# ── CTAs ────────────────────────────────────────────────────────────────────
CTAS = [
    "📞 Contact us today.",
    "📩 Send us a message.",
    "💬 Comment \"HELP\" for assistance.",
    "📱 WhatsApp us for details.",
    "📞 Call us for free consultation.",
    "📩 DM us for more information.",
]

# ── Hashtag Pools ──────────────────────────────────────────────────────────
HASHTAG_POOLS = {
    "loan_subsidy": [
        "PrishaOnlineCentre", "PrishaOnlineDocumentation", "MahaESewa", "CSC",
        "BusinessRegistration", "MSME", "GovernmentSchemes", "MaharashtraBusiness",
        "MudraLoan", "PMEGP", "BusinessLoan", "SmallBusiness", "GovernmentSubsidy",
    ],
    "government_schemes": [
        "PrishaOnlineCentre", "PrishaOnlineDocumentation", "MahaESewa", "CSC",
        "BusinessRegistration", "MSME", "GovernmentSchemes", "MaharashtraBusiness",
        "SarkarYojana", "GovernmentBenefit", "BusinessSupport", "India",
    ],
    "business_registration": [
        "PrishaOnlineCentre", "PrishaOnlineDocumentation", "MahaESewa", "CSC",
        "BusinessRegistration", "MSME", "GovernmentSchemes", "MaharashtraBusiness",
        "GSTRegistration", "UdyamRegistration", "StartupIndia", "BusinessIndia",
    ],
    "compliance": [
        "PrishaOnlineCentre", "PrishaOnlineDocumentation", "MahaESewa", "CSC",
        "BusinessRegistration", "MSME", "GovernmentSchemes", "MaharashtraBusiness",
        "BusinessCompliance", "GSTFiling", "LegalCompliance", "BusinessUpdate",
    ],
    "taxation": [
        "PrishaOnlineCentre", "PrishaOnlineDocumentation", "MahaESewa", "CSC",
        "BusinessRegistration", "MSME", "GovernmentSchemes", "MaharashtraBusiness",
        "GST", "IncomeTax", "TaxSaving", "ITRFiling",
    ],
    "startup_resources": [
        "PrishaOnlineCentre", "PrishaOnlineDocumentation", "MahaESewa", "CSC",
        "BusinessRegistration", "MSME", "GovernmentSchemes", "MaharashtraBusiness",
        "StartupIndia", "BusinessIndia", "EntrepreneurIndia", "SmallBusiness",
    ],
}


class CaptionGenerator:
    """Generate bilingual (English + Marathi) captions for Prisha Online Centre."""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def generate_captions(
        self,
        headline: str,
        topic: str,
        category: str,
        info_blocks: list = None,
    ) -> dict:
        """
        Generate full bilingual caption following CAPTION_FRAMEWORK.md structure.

        Returns:
            {
                "english": str,      # English portion (hook + body)
                "marathi": str,      # Marathi portion (hook + body)
                "full_caption": str, # Complete formatted caption for Instagram
                "hashtags": list,    # 8-12 curated hashtags
            }
        """
        info_blocks = info_blocks or []
        cat = category if category in HOOKS else "government_schemes"

        # Build each section
        hook_en = self._pick(HOOKS[cat]["en"])
        hook_mr = self._pick(HOOKS[cat]["mr"])
        body_en = self._pick(BODY_EN.get(cat, BODY_EN["government_schemes"]))
        body_mr = self._pick(BODY_MR.get(cat, BODY_MR["government_schemes"]))
        benefits = BENEFITS.get(cat, BENEFITS["government_schemes"])
        cta = self._pick(CTAS)
        hashtags = self._build_hashtags(cat, topic)

        # Build full caption
        full = self._assemble_full_caption(
            headline=headline,
            hook_en=hook_en,
            body_en=body_en,
            hook_mr=hook_mr,
            body_mr=body_mr,
            benefits=benefits[:5],
            cta=cta,
            hashtags=hashtags,
        )

        return {
            "english": f"{hook_en}\n\n{body_en}",
            "marathi": f"{hook_mr}\n\n{body_mr}",
            "full_caption": full,
            "hashtags": hashtags,
        }

    def _assemble_full_caption(
        self,
        headline: str,
        hook_en: str,
        body_en: str,
        hook_mr: str,
        body_mr: str,
        benefits: list,
        cta: str,
        hashtags: list,
    ) -> str:
        """Assemble the complete caption following the 9-section framework."""
        parts = []

        # 1. Headline (topic title)
        parts.append(headline)
        parts.append("")

        # 2. English hook
        parts.append(hook_en)
        parts.append("")

        # 3. English explanation
        parts.append(body_en)
        parts.append("")

        # 4. Marathi hook + explanation
        parts.append(hook_mr)
        parts.append("")
        parts.append(body_mr)
        parts.append("")

        # 5. Benefits
        for b in benefits:
            parts.append(f"✅ {b}")
        parts.append("")

        # 6. Why Choose Prisha
        for t in TRUST_SECTION:
            parts.append(t)
        parts.append("")

        # 7. CTA
        parts.append(cta)
        parts.append("")

        # 8. Contact
        parts.append("📍 " + CONTACT["address"])
        parts.append("📞 " + CONTACT["phone"])
        parts.append("")

        # 9. Brand tagline
        parts.append(f"✨ {CONTACT['tagline_en']} ✨")
        parts.append(f"✨ {CONTACT['tagline_mr']} ✨")
        parts.append("")

        # 10. Hashtags
        parts.append(" ".join(f"#{h}" for h in hashtags))

        return "\n".join(parts)

    def _build_hashtags(self, category: str, topic: str) -> list:
        """Build 8-12 relevant hashtags."""
        pool = HASHTAG_POOLS.get(category, HASHTAG_POOLS["government_schemes"])
        # Pick 8-12 from pool, ensuring brand tags are always included
        must_have = ["PrishaOnlineCentre", "PrishaOnlineDocumentation"]
        tags = list(dict.fromkeys(must_have + pool))[:12]
        return tags

    @staticmethod
    def _pick(options: list) -> str:
        return random.choice(options)


def main():
    """Test the caption generator."""
    gen = CaptionGenerator()
    result = gen.generate_captions(
        headline="📢 MSME Champions Portal",
        topic="MSME Champions Portal — government support for small businesses",
        category="government_schemes",
        info_blocks=[
            {"text": "Scheme guidance", "icon": "✓"},
            {"text": "Registration assistance", "icon": "✓"},
            {"text": "Documentation support", "icon": "✓"},
        ],
    )
    print("=" * 50)
    print("FULL CAPTION:")
    print("=" * 50)
    print(result["full_caption"])
    print("=" * 50)
    print(f"\nHashtags ({len(result['hashtags'])}): {result['hashtags']}")


if __name__ == "__main__":
    main()
