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

        # Try Gemini first, then OpenAI
        result = self._try_gemini(prompt)
        if result is None:
            result = self._try_openai(prompt)
        if result is None:
            raise RuntimeError("Both Gemini and OpenAI content generation failed. Check API keys and quotas.")

        # Validate
        validated = self._validate_output(result, category)
        log.info("Content generated", category=category, topic=validated.get("topic", ""))
        return validated

    # ── Gemini ─────────────────────────────────────────────────────────────────

    def _try_gemini(self, prompt: str) -> dict | None:
        api_key = get_env("GEMINI_API_KEY")
        if not api_key:
            log.warn("GEMININ_API_KEY not set, skipping Gemini.")
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
