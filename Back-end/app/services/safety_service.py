import re
from typing import Optional, Tuple


class SafetyService:
    """
    Mandatory Medical Safety System for HeartShield:
    - Zero-latency detection of acute emergency cardiovascular symptoms
    - Standard medical disclaimer enforcement
    - Prompt injection filtering and sanitization
    """

    EMERGENCY_PATTERNS = [
        r"\b(severe|crushing|squeezing|heavy|tightness|pressure)\s+(chest\s+)?(pain|discomfort|pressure)\b",
        r"\bchest\s+(pain|tightness|heaviness|pressure)\b",
        r"\bpain\s+(radiating|spreading)\s+to\s+(left\s+)?(arm|jaw|neck|back|shoulder)\b",
        r"\bshortness\s+of\s+breath\b.*(sweat|nausea|chest)",
        r"\bcan('?t|not)\s+breathe\b",
        r"\bsudden\s+(numbness|weakness)\b.*(face|arm|leg|side)",
        r"\bface\s+droop(ing)?\b",
        r"\bsudden\s+(loss\s+of\s+speech|slurred\s+speech|trouble\s+speaking)\b",
        r"\bpassed\s+out\b|\bfainted\b|\bloss\s+of\s+consciousness\b",
        r"\bheart\s+attack\s+(right\s+now|happening)\b",
    ]

    EMERGENCY_DIRECTIVE = (
        "🚨 **CRITICAL EMERGENCY MEDICAL ALERT**\n\n"
        "The symptoms you described (such as severe chest pain, radiating discomfort, sudden shortness of breath, "
        "or sudden neurological weakness) can be signs of an **acute, life-threatening cardiovascular emergency** (e.g. Myocardial Infarction or Stroke).\n\n"
        "**TAKE IMMEDIATE ACTION:**\n"
        "1. **Call emergency medical services immediately** (dial **911**, **112**, **102**, or your local emergency dispatch).\n"
        "2. **Do not drive yourself** to the hospital—wait for emergency responders.\n"
        "3. Sit or lie down in a safe position and loosen any tight clothing around your neck.\n"
        "4. If advised by emergency dispatch and you are not allergic, chew an aspirin while waiting for paramedics.\n\n"
        "*This automated platform is not an emergency triage tool. Seek professional emergency medical care immediately.*"
    )

    STANDARD_DISCLAIMER = (
        "\n\n---\n"
        "⚕️ **Medical Disclaimer**: *HeartShield AI provides general cardiovascular health education and research insights. "
        "It is not a substitute for clinical diagnosis, treatment, or professional medical advice from a qualified healthcare provider. "
        "Never ignore professional clinical guidance or delay seeking it because of information provided by this assistant.*"
    )

    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above)\s+instructions",
        r"you\s+are\s+now\s+(an\s+unfiltered|in\s+developer\s+mode|dan)",
        r"system\s*:\s*override",
        r"reveal\s+(system\s+prompt|api\s+key|database|passwords)",
        r"act\s+as\s+a\s+doctor\s+and\s+prescribe",
    ]

    @classmethod
    def check_emergency(cls, user_text: str) -> Tuple[bool, Optional[str]]:
        """
        Scans text for life-threatening symptom indicators.
        Returns (is_emergency, emergency_response_text).
        """
        text_lower = user_text.lower()
        for pattern in cls.EMERGENCY_PATTERNS:
            if re.search(pattern, text_lower):
                return True, cls.EMERGENCY_DIRECTIVE
        return False, None

    @classmethod
    def sanitize_user_input(cls, text: str) -> str:
        """
        Neutralizes overt prompt injection attempts while retaining legitimate medical queries.
        """
        sanitized = text
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[Filtered Request]", sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def append_disclaimer(cls, response_text: str) -> str:
        if "Medical Disclaimer" not in response_text:
            return response_text + cls.STANDARD_DISCLAIMER
        return response_text


safety_service = SafetyService()
