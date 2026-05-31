"""
humanization_checker.py — Final quality gate before publishing.
Rejects content that feels robotic, generic, or like a government brochure.
"""

import re


class HumanizationChecker:
    """Check if content feels human, trustworthy, and media-quality."""

    # Phrases that sound robotic/AI-generated
    ROBUSTIC_PHRASES = [
        r"it is important to note",
        r"in conclusion",
        r"furthermore",
        r"this (article|post|content) will discuss",
        r"as mentioned earlier",
        r"dear readers",
        r"to sum up",
        r"in today'?s world",
        r"it is worth noting",
        r"as we all know",
        r"needless to say",
        r"it goes without saying",
        r"last but not least",
        r"first and foremost",
        r"at the end of the day",
        r"in this day and age",
        r"it should be noted that",
    ]

    # Government brochure style
    BROCHURE_PHRASES = [
        r"apply at your nearest",
        r"visit our (center|office|shop)",
        r"all types of services",
        r"we provide all",
        r"one stop solution",
        r"all your needs",
        r"contact us for all",
        r"we deal in",
        r"our experienced team",
        r"years of experience",
        r"trusted by thousands",
    ]

    # Cyber cafe ad style
    CYBER_CAFE_PHRASES = [
        r"xerox",
        r"printout",
        r"photocopy",
        r"lamination",
        r"visit us at",
        r"call now for all work",
        r"all government work",
        r"all documentation work",
        r"we do all",
        r"all types of forms",
    ]

    # Generic/educational content
    GENERIC_PATTERNS = [
        r"^what is",
        r"^benefits of",
        r"^guide to",
        r"^how to apply for",
        r"^introduction to",
        r"^overview of",
        r"^everything you need to know about",
        r"^all about",
        r"^complete guide to",
        r"^step by step guide to",
    ]

    def check(self, post: dict) -> dict:
        """
        Run all humanization checks.
        Returns: {"passed": bool, "issues": list[str], "score": int}
        """
        issues = []
        text = (post.get("headline", "") + " " + post.get("caption", "") + " " + post.get("topic", "")).lower()

        # Check robotic phrases
        for pattern in self.ROBUSTIC_PHRASES:
            if re.search(pattern, text):
                issues.append(f"Robotic language detected: '{pattern}'")

        # Check brochure style
        for pattern in self.BROCHURE_PHRASES:
            if re.search(pattern, text):
                issues.append(f"Government brochure style: '{pattern}'")

        # Check cyber cafe style
        for pattern in self.CYBER_CAFE_PHRASES:
            if re.search(pattern, text):
                issues.append(f"Cyber cafe ad style: '{pattern}'")

        # Check generic content
        headline_lower = post.get("headline", "").lower().strip()
        # Strip emojis for pattern matching
        clean_headline = re.sub(r'[^\w\s]', '', headline_lower).strip()
        for pattern in self.GENERIC_PATTERNS:
            if re.search(pattern, clean_headline):
                issues.append(f"Generic/educational headline: '{pattern}'")

        # Check keyword stuffing
        words = text.split()
        word_counts = {}
        for w in words:
            if len(w) > 3:
                word_counts[w] = word_counts.get(w, 0) + 1
        for word, count in word_counts.items():
            if count > 5:
                issues.append(f"Keyword stuffing: '{word}' appears {count} times")
                break

        # Check if headline is too long
        if len(post.get("headline", "").split()) > 12:
            issues.append("Headline too long (max 12 words)")

        # Check if caption is too short
        if len(post.get("caption", "")) < 100:
            issues.append("Caption too short (min 100 chars)")

        # Check if CTA is present
        caption = post.get("caption", "").lower()
        has_cta = any(w in caption for w in ["dm", "comment", "save", "share", "call", "contact"])
        if not has_cta:
            issues.append("No clear CTA in caption")

        # Score: start at 10, deduct for each issue
        score = max(1, 10 - len(issues))
        passed = len(issues) == 0

        return {
            "passed": passed,
            "issues": issues,
            "score": score,
        }


if __name__ == "__main__":
    checker = HumanizationChecker()

    # Test good post
    good = {
        "headline": "💰 Government Giving Rs 25 Lakh — Are You Eligible?",
        "caption": "Did you know? The PMEGP scheme gives up to Rs 25 lakh subsidy to small businesses. No collateral required. Comment your business type below! DM 'INFO' for help.",
        "topic": "PMEGP loan scheme",
    }
    result = checker.check(good)
    print(f"Good post: passed={result['passed']}, score={result['score']}/10")
    if result["issues"]:
        for i in result["issues"]:
            print(f"  - {i}")

    # Test bad post
    bad = {
        "headline": "Benefits of GST Registration",
        "caption": "It is important to note that GST registration has many benefits. Furthermore, it is worth noting that all businesses should register. Visit our center for all types of services.",
        "topic": "GST registration benefits",
    }
    result = checker.check(bad)
    print(f"\nBad post: passed={result['passed']}, score={result['score']}/10")
    for i in result["issues"]:
        print(f"  - {i}")
