"""
lib/content_engine.py — AI-powered content generation.

Primary:  Google Gemini API
Fallback: OpenAI API

Generates a complete Instagram post (topic, hook, headline, caption,
CTA, hashtags, image text) as structured JSON.

Usage:
    engine = ContentEngine()
    post = engine.generate_post(category="Udyam", used_topics=["..."])
"""

import json
import re
import time
import requests
from lib.utils import load_config, get_env
from lib.logger import EngineLogger

log = EngineLogger("content_engine")

# ── Prompt template ───────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a world-class Instagram content strategist for an Indian business documentation and registration services company called "Prisha Online Documentation".

Your job is to write HIGH-QUALITY, HUMAN-SOUNDING Instagram carousel/caption content that educates small business owners and converts them into customers.

RULES:
1. Write like a knowledgeable business consultant — never robotic, never generic.
2. Use storytelling. Start with a hook — a real scenario, a question, a surprising fact.
3. Be factually accurate. Never make legal guarantees or exaggerated promises.
4. Use simple, conversational Indian English. Short sentences. Easy to read.
5. NEVER use generic motivational quotes or obvious advice.
6. Always include a clear, natural Call-To-Action relevant to the topic.
7. The caption should be 100-200 words — not too short, not too long.
8. Hashtags should be specific and relevant, not generic spam.

OUTPUT FORMAT — Return ONLY valid JSON (no markdown, no code fences, no extra text):
{{
  "topic": "Specific topic for today's post",
  "category": "One of the provided categories",
  "headline": "Short powerful headline (6-10 words)",
  "hook": "One-sentence hook that grabs attention",
  "caption": "Full caption with storytelling, value, and natural CTA",
  "cta": "Clear call-to-action line",
  "hashtags": ["hashtag1", "hashtag2", ...],
  "image_text": "Text to display on the image (short, max 12 words)"
}}"""


def _make_user_prompt(
    category: str,
    used_topics: list[str],
    used_headlines: list[str],
    services: list[str],
    frameworks: list[str],
    tone: str,
) -> str:
    """Build the user prompt for the LLM."""
    return f"""Generate a unique Instagram post for Prisha Online Documentation.

STORYTELLING FRAMEWORK TO USE TODAY: {frameworks[hash(str(used_topics)) % len(frameworks)]}

CONTENT CATEGORY: {category}

BUSINESS SERVICES: {', '.join(services)}

TONE: {tone}

IMPORTANT — DO NOT reuse any of these previously used topics or headlines:
Previously used topics: {used_topics[-30:] if used_topics else 'none yet'}
Previously used headlines: {used_headlines[-20:] if used_headlines else 'none yet'}

Generate fresh, unique content that has NEVER been posted before.
Focus on the "{category}" category and use a storytelling approach."""


class ContentEngine:
    """Generates Instagram content using Gemini (primary) or OpenAI (fallback)."""

    def __init__(self):
        self.config = load_config()
        self.api_config = self.config.get("api", {})

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate_post(
        self,
        category: str,
        used_topics: list[str],
        used_headlines: list[str],
    ) -> dict:
        """
        Generate a complete Instagram post.

        Args:
            category: Content category (e.g. "Udyam")
            used_topics: List of previously used topics (dedup)
            used_headlines: List of previously used headlines (dedup)

        Returns:
            dict with keys: topic, category, headline, hook, caption,
            cta, hashtags, image_text

        Raises:
            RuntimeError: If both Gemini and OpenAI fail.
        """
        services = self.config.get("services", [])
        frameworks = self.config.get("storytelling_frameworks", [])
        tone = self.config.get("business", {}).get("tone", "Professional")
        prompt = _make_user_prompt(category, used_topics, used_headlines, services, frameworks, tone)

        # Try Gemini first, then OpenAI, then template fallback
        result = self._try_gemini(prompt)
        if result is None:
            result = self._try_openai(prompt)
        if result is None:
            log.warn("Both APIs failed — using template fallback")
            result = self._template_fallback(category, used_topics, used_headlines)

        # Validate
        validated = self._validate_output(result, category)
        log.info("Content generated", category=category, topic=validated.get("topic", ""))
        return validated

    # ── Template Fallback ───────────────────────────────────────────────────────

    def _template_fallback(self, category: str, used_topics: list[str], used_headlines: list[str]) -> dict:
        """
        Generate content from templates when all APIs are unavailable.
        Cycles through predefined topics/headlines based on hash of used history.
        """
        import hashlib

        templates = {
            "GST": {
                "topics": [
                    "GST Registration for Freelancers — Is It Really Necessary?",
                    "Common GST Filing Mistakes That Lead to Penalties",
                    "How GST Input Tax Credit Can Save Your Business Money",
                    "GST Composition Scheme: Perfect for Small Businesses?",
                    "Why Every E-commerce Seller Needs GST Registration",
                ],
                "hooks": [
                    "Freelancers — are you ignoring GST and risking penalties?",
                    "Most small businesses overpay GST because of these simple mistakes.",
                    "What if you could legally reduce your tax bill by lakhs?",
                    "Running a business without GST? Here's what you need to know.",
                ],
                "ctas": [
                    "Need help with GST? DM us today!",
                    "Call Prisha Online Documentation for hassle-free GST registration.",
                    "Visit www.prishaonlinedocumentation.com to get started.",
                ],
                "hashtags": ["GST", "GSTRegistration", "TaxTips", "SmallBusinessIndia", "BusinessCompliance", "FreelancerLife", "GSTFiling", "TaxSaving"],
            },
            "Udyam": {
                "topics": [
                    "Udyam Registration: Your Business Gateway to Government Benefits",
                    "How Udyam Registration Helped 10,000+ MSMEs Get Bank Loans",
                    "Udyam Registration vs MSME Registration: What's the Difference?",
                    "Step-by-Step Udyam Registration Process in 2024-25",
                    "Why Udyam Registration Must Be Renewed — And How to Do It",
                ],
                "hooks": [
                    "Did you know your small business can get loans at lower interest rates?",
                    "Over 10,000 MSMEs unlocked benefits they didn't know existed.",
                    "Most business owners still don't know the difference between Udyam and MSME.",
                    "Skipping Udyam registration? You're leaving money on the table.",
                ],
                "ctas": [
                    "Register your business on Udyam today — contact us!",
                    "Let Prisha Online Documentation handle your Udyam registration.",
                    "DM us 'UDYAM' to get started in 5 minutes.",
                ],
                "hashtags": ["Udyam", "UdyamRegistration", "MSMEIndia", "SmallBusiness", "GovernmentScheme", "BusinessRegistration", "StartupIndia"],
            },
            "MSME": {
                "topics": [
                    "MSME Registration: The Easiest Way to Legally Recognize Your Business",
                    "Top 5 Benefits of MSME Registration Most Business Owners Don't Know",
                    "How MSME Registration Helped a Local Shop Owner Get a 20 Lakh Loan",
                    "MSME Government Subsidies: Are You Missing Out?",
                    "Why Every Street Food Vendor Should Get MSME Registration",
                ],
                "hooks": [
                    "Your small business deserves bigger opportunities — here's how to unlock them.",
                    "A local shop owner once struggled to get a loan. MSME registration changed everything.",
                    "The Indian government has allocated crores in subsidies for MSMEs. Are you registered?",
                    "Even street vendors can now get government benefits. Here's how.",
                ],
                "ctas": [
                    "Get your MSME certificate in 3-5 days. Call us now!",
                    "Prisha Online Documentation — your trusted MSME registration partner.",
                    "DM 'MSME' and we'll call you back within 24 hours.",
                ],
                "hashtags": ["MSME", "MSMERegistration", "SmallBusiness", "GovernmentScheme", "MakeInIndia", "BusinessIndia", "MICROBUSINESS"],
            },
            "FSSAI": {
                "topics": [
                    "FSSAI License for Home-Based Food Business — Everything You Need to Know",
                    "Selling Food Online Without FSSAI? You Could Face Heavy Penalties",
                    "Basic vs State vs Central FSSAI License: Which One Do You Need?",
                    "How to Get FSSAI License for Your Cloud Kitchen in 7 Days",
                    "FSSAI Renewal: Don't Let Your Food Business License Expire",
                ],
                "hooks": [
                    "Starting a food business from home? FSSAI license is mandatory — not optional.",
                    "Selling on Instagram or Zomato without FSSAI? Big mistake.",
                    "Not all FSSAI licenses are the same. Picking the wrong one costs time and money.",
                    "Your cloud kitchen can be fully legal in just one week.",
                ],
                "ctas": [
                    "Apply for FSSAI license with Prisha Online Documentation today!",
                    "Call us for FSSAI registration — quick, easy, affordable.",
                    "DM 'FSSAI' for a free consultation on food business licensing.",
                ],
                "hashtags": ["FSSAI", "FSSAILicense", "FoodBusiness", "CloudKitchen", "HomeBusiness", "FoodSafety", "FoodLicense"],
            },
            "Startup Registration": {
                "topics": [
                    "Startup India Registration: Benefits Worth Lakhs for New Businesses",
                    "How Startup India Recognition Helped This Founder Get Tax-Free Funding",
                    "Startup vs Pvt Ltd: Which Business Structure Should You Choose?",
                    "A-Z Guide to DPIIT Recognition for Startups",
                    "Why Most Early-Stage Startups Delay Registration (And Regret It)",
                ],
                "hooks": [
                    "Your great business idea deserves government backing. Here's how to get it.",
                    "One founder saved 3 years of income tax by registering correctly.",
                    "Choosing the wrong business structure can cost you lakhs in the long run.",
                    "Most founders focus on the product and ignore the paperwork. Big mistake.",
                ],
                "ctas": [
                    "Register your startup with expert help — contact Prisha Online!",
                    "DM 'STARTUP' and we'll guide you through the entire process.",
                    "Startup registration takes 2-3 days with us. Call now!",
                ],
                "hashtags": ["Startup", "StartupIndia", "DPIT", "Entrepreneurship", "NewBusiness", "BusinessRegistration", "StartupIndiaRegistration"],
            },
            "Company Registration": {
                "topics": [
                    "One Person Company (OPC): The Best Structure for Solo Founders",
                    "Pvt Ltd vs OPC vs LLP: Which One Fits Your Business?",
                    "How to Register a Company in India in Under 7 Days",
                    "Common Company Registration Mistakes That Cause MCA Rejection",
                    "Why Registering Early Saves Your Business from Legal Trouble",
                ],
                "hooks": [
                    "Solo entrepreneur? OPC might be the perfect structure for you.",
                    "Picking the wrong business entity can cost you double the taxes.",
                    "Yes, you can register a company in India without leaving your home.",
                    "The #1 reason MCA rejects company applications — and how to avoid it.",
                ],
                "ctas": [
                    "Register your company with Prisha Online Documentation — hassle-free!",
                    "DM 'COMPANY' for a free consultation on business structure.",
                    "Call us to find the best structure for your new business.",
                ],
                "hashtags": ["CompanyRegistration", "PvtLtd", "OPC", "LLP", "BusinessInIndia", "MCA", "Entrepreneurship"],
            },
            "Proprietorship Registration": {
                "topics": [
                    "Sole Proprietorship: Simplest Way to Make Your Business Legal",
                    "Why Every Freelancer Should Register as a Sole Proprietor",
                    "Proprietorship Registration: Costs, Documents, and Timeline",
                    "Door-to-Door Business? Proprietorship Registration Makes It Legit",
                    "How to Open a Business Bank Account Without a Proprietorship Certificate",
                ],
                "hooks": [
                    "Running your own business informally? Time to make it official.",
                    "Freelancers: your work is legal the moment you register as a proprietor.",
                    "No complex paperwork. No heavy fees. Just simple, legit business.",
                    "Even small door-to-door businesses need this one certificate.",
                ],
                "ctas": [
                    "Get your proprietorship registered in 2-3 days. Call Prisha Online!",
                    "DM 'SOLE' to start your proprietorship registration today.",
                    "Simple. Fast. Legal. Visit www.prishaonlinedocumentation.com",
                ],
                "hashtags": ["Proprietorship", "SoleProprietor", "SmallBusiness", "BusinessRegistration", "Freelancer", "BusinessIndia"],
            },
            "Government Schemes": {
                "topics": [
                    "PMEGP Scheme: Get Up to 25 Lakhs Subsidy for Your Small Business",
                    "Mudra Loan Under PMMY: How to Apply and How Much You Can Get",
                    "Stand-Up India SCHEME: Loans for SC/ST Women Entrepreneurs",
                    "Credit Guarantee Scheme (CGTMSE): Loans Without Collateral",
                    "PM Vishwakarma Scheme: Benefits for Artisans and Craftsmen",
                ],
                "hooks": [
                    "The government is literally giving away lakhs in subsidies. Are you applying?",
                    "No collateral. No heavy paperwork. Just a small business and a dream.",
                    "Women entrepreneurs: a special government scheme wants to fund your dream.",
                    "Banks rejecting your loan application? CGTMSE has your back.",
                ],
                "ctas": [
                    "Check your eligibility today — call Prisha Online Documentation!",
                    "DM 'SCHEME' and we'll identify which government benefits you qualify for.",
                    "Get expert assistance with government scheme applications.",
                ],
                "hashtags": ["GovernmentScheme", "PMEGP", "MudraLoan", "StandUpIndia", "CGTMSE", "SmallBusiness", "Subsidy"],
            },
            "Shop Act Registration": {
                "topics": [
                    "Shop Act License: Why Every Retail Business in India Needs One",
                    "How to Get Shop Act License in Under 5 Days",
                    "Running a Business Without Shop Act License? Here Are the Penalties",
                    "Shop Act Registration Documents Checklist: Don't Miss Any",
                    "The Complete Guide to Shop Act Renewal Process",
                ],
                "hooks": [
                    "If you run any shop or commercial establishment, this license is mandatory.",
                    "Surprise inspections are real. Is your shop legally compliant?",
                    "The fines for running without Shop Act can shut down your business.",
                    "Missing one document can delay your license by weeks.",
                ],
                "ctas": [
                    "Get your Shop Act license quickly with Prisha Online!",
                    "DM 'SHOP ACT' to apply for your license today.",
                    "Call us — we handle the entire process for you.",
                ],
                "hashtags": ["ShopAct", "ShopActLicense", "BusinessLicense", "RetailBusiness", "Compliance", "BusinessIndia"],
            },
            "Business Compliance": {
                "topics": [
                    "Annual Compliance Checklist for Small Businesses in India",
                    "ITR Filing for Business Owners: Deadline Reminder and Penalties",
                    "GST + ITR + Annual Compliance: Your Complete Guide",
                    "Why Compliance Is the Cheapest Insurance for Your Business",
                    "New Business? Here's Your First-Year Compliance Checklist",
                ],
                "hooks": [
                    "Missing compliance deadlines? You could face lakhs in penalties.",
                    "Business owners: your ITR deadline is closer than you think.",
                    "Most new business owners don't know they need GST AND ITR AND annual filings.",
                    "Think of compliance as insurance — cheap now, expensive if ignored.",
                ],
                "ctas": [
                    "Stay compliant, stay stress-free. Contact Prisha Online!",
                    "DM 'COMPLIANCE' for a free first-year compliance consultation.",
                    "Let our experts handle your business compliance end-to-end.",
                ],
                "hashtags": ["Compliance", "ITRFiling", "GSTFiling", "BusinessIndia", "TaxFiling", "SmallBusiness", "LegalCompliance"],
            },
        }

        # Default to a generic template if category not found
        cat_templates = templates.get(category, templates["GST"])

        # Pick based on how many topics already used (cycle through)
        idx = len(used_topics) % len(cat_templates["topics"])

        topic = cat_templates["topics"][idx]
        hook = cat_templates["hooks"][idx % len(cat_templates["hooks"])]
        cta = cat_templates["ctas"][idx % len(cat_templates["ctas"])]
        hashtags = cat_templates["hashtags"]

        # Build caption from hook + topic context + cta
        service_context = {
            "GST": "GST registration is mandatory for businesses with turnover above the threshold. It not only makes your business legal but also allows you to claim input tax credit. Many freelancers and small business owners delay GST registration and end up facing penalties. At Prisha Online Documentation, we handle end-to-end GST registration so you can focus on your business.",
            "Udyam": "Udyam Registration is the Indian government's way of recognizing MSMEs. Once registered, your business becomes eligible for priority lending, lower interest rates on loans, tax benefits, and access to government tenders. The process is entirely online and free of cost. Prisha Online Documentation helps you get your Udyam certificate in just 3-5 working days.",
            "MSME": "MSME registration opens doors to countless government benefits — from subsidized loans to tax exemptions, electricity bill reductions, and protection against delayed payments. Whether you're a tiny shop owner or a growing startup, being an MSME-registered business gives you a competitive edge. Let Prisha Online Documentation handle your registration.",
            "FSSAI": "If you're in the food business — whether it's a cloud kitchen, restaurant, home bakery, or food truck — an FSSAI license isn't optional. It's the law. Operating without one can lead to heavy fines and even imprisonment. Prisha Online Documentation helps you get the right FSSAI license (Basic, State, or Central) based on your business size and turnover.",
            "Startup Registration": "Startup India recognition by DPIIT gives your new business access to tax exemptions for 3 years, easier compliance, IPR fast-tracking, and access to government funding schemes. But the application requires proper documentation and a clear innovation story. Prisha Online Documentation's experts guide you through every step.",
            "Company Registering": "Registering your company isn't just about legality — it's about building trust. A registered company can open corporate bank accounts, raise funding, sign contracts, and protect your personal assets. Whether it's OPC, Pvt Ltd, or LLP, we pick the right structure for you. Prisha Online Documentation makes company registration simple.",
            "Proprietorship Registration": "A sole proprietorship is the simplest business structure in India. It requires minimal documentation, zero heavy compliance, and can be registered in just 2-3 days. Perfect for freelancers, consultants, and small shop owners who want to go legit without the complexity. Prisha Online Documentation does it all — quickly and affordably.",
            "Government Schemes": "The Indian government runs dozens of schemes to support small businesses — from PMEGP subsidies to Mudra loans, Stand-Up India, and CGTMSE collateral-free loans. But most business owners either don't know about them or struggle with the paperwork. Prisha Online Documentation identifies which schemes you qualify for and handles the application.",
            "Shop Act Registration": "The Shop and Establishment Act license is mandatory for every commercial establishment in India — shops, offices, restaurants, and more. Without it, you risk fines, legal complications, and even forced closure. The good news? It can be done in under 5 days. Prisha Online Documentation handles your Shop Act registration from start to finish.",
            "Business Compliance": "Running a business means more than just making sales — you need to stay on top of GST returns, income tax filings, annual reports, and regulatory deadlines. Miss one and penalties pile up fast. Prisha Online Documentation offers comprehensive compliance packages so you never miss a deadline.",
        }

        return {
            "topic": topic,
            "category": category,
            "headline": topic.split(":")[0] if ":" in topic else topic[:60],
            "hook": hook,
            "caption": f"{hook}\n\n{service_context.get(category, service_context['GST'])}",
            "cta": cta,
            "hashtags": hashtags,
            "image_text": topic.split(":")[0][:50] if ":" in topic else topic[:50],
        }

    # ── Gemini ─────────────────────────────────────────────────────────────────

    def _try_gemini(self, prompt: str) -> dict | None:
        api_key = get_env("GEMINI_API_KEY")
        if not api_key:
            log.warn("GEMINI_API_KEY not set, skipping Gemini.")
            return None

        model = self.api_config.get("gemini", {}).get("model", "gemini-2.0-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        gemini_config = self.api_config.get("gemini", {})

        payload = {
            "contents": [{"parts": [{"text": _SYSTEM_PROMPT + "\n\n" + prompt}]}],
            "generationConfig": {
                "temperature": gemini_config.get("temperature", 0.85),
                "maxOutputTokens": gemini_config.get("max_tokens", 1024),
            },
        }

        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                log.debug(f"Gemini attempt {attempt}/{max_retries}")
                resp = requests.post(
                    url,
                    params={"key": api_key},
                    json=payload,
                    timeout=60,
                )
                if resp.status_code == 429:
                    wait = 10 * attempt
                    log.warn(f"Gemini rate limited (429), waiting {wait}s before retry", extra={"attempt": attempt})
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()

                # Extract text from Gemini response
                candidates = data.get("candidates", [])
                if not candidates:
                    log.warn("Gemini returned no candidates", extra={"response": str(data)[:200]})
                    continue

                text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if not text_content:
                    log.warn("Gemini returned empty text")
                    continue

                return self._parse_json_response(text_content)

            except requests.exceptions.RequestException as e:
                log.warn(f"Gemini request failed (attempt {attempt})", extra={"error": str(e)})
                if attempt < max_retries:
                    time.sleep(5 * attempt)
            except Exception as e:
                log.error(f"Gemini unexpected error: {e}")
                break

        return None

    # ── OpenAI ─────────────────────────────────────────────────────────────────

    def _try_openai(self, prompt: str) -> dict | None:
        api_key = get_env("OPENAI_API_KEY")
        if not api_key:
            log.warn("OPENAI_API_KEY not set, skipping OpenAI.")
            return None

        model = self.api_config.get("openai", {}).get("model", "gpt-4o-mini")
        openai_config = self.api_config.get("openai", {})

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                log.debug(f"OpenAI attempt {attempt}/{max_retries}")
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": _SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": openai_config.get("temperature", 0.85),
                        "max_tokens": openai_config.get("max_tokens", 1024),
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()

                choices = data.get("choices", [])
                if not choices:
                    log.warn("OpenAI returned no choices")
                    continue

                text_content = choices[0].get("message", {}).get("content", "")
                if not text_content:
                    log.warn("OpenAI returned empty text")
                    continue

                return self._parse_json_response(text_content)

            except requests.exceptions.RequestException as e:
                log.warn(f"OpenAI request failed (attempt {attempt})", extra={"error": str(e)})
                if attempt < max_retries:
                    time.sleep(2 * attempt)
            except Exception as e:
                log.error(f"OpenAI unexpected error: {e}")
                break

        return None

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json_response(text: str) -> dict | None:
        """Extract and parse JSON from LLM text. Handles markdown fences."""
        # Strip markdown code fences
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            log.error("Failed to parse JSON from LLM response", extra={"raw": text[:300]})
            return None

    @staticmethod
    def _validate_output(data: dict, category: str) -> dict:
        """Ensure all required fields exist, fill defaults if missing."""
        required = {
            "topic": f"Understanding {category} Registration",
            "category": category,
            "headline": f"Why {category} Matters for Your Business",
            "hook": "Did you know?",
            "caption": "Contact Prisha Online Documentation for expert assistance.",
            "cta": "DM us or call to get started today!",
            "hashtags": [category.replace(" ", ""), "BusinessRegistration", "India"],
            "image_text": category,
        }
        for key, default in required.items():
            if key not in data or not data[key]:
                data[key] = default

        # Ensure hashtags is a list
        if isinstance(data.get("hashtags"), str):
            data["hashtags"] = [h.strip() for h in data["hashtags"].split() if h.strip()]

        # Trim hashtags to max 30
        data["hashtags"] = data["hashtags"][:30]

        return data
