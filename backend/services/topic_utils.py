"""Shared topic cleaning helpers used across the AICES backend."""

import re


TOPIC_NORMALIZATION_PATTERNS = (
    (re.compile(r"\bdeepth\b", flags=re.IGNORECASE), "depth"),
    (re.compile(r"\bdeeply\b", flags=re.IGNORECASE), "depth"),
    (re.compile(r"\blinked[\s-]*lists?\b", flags=re.IGNORECASE), "linked list"),
    (re.compile(r"\bbinary[\s-]*search(?:ing)?\b", flags=re.IGNORECASE), "binary search"),
    (re.compile(r"\barrays\b", flags=re.IGNORECASE), "array"),
    (re.compile(r"\bstacks\b", flags=re.IGNORECASE), "stack"),
    (re.compile(r"\bqueues\b", flags=re.IGNORECASE), "queue"),
    (re.compile(r"\brecursive\s+function\b", flags=re.IGNORECASE), "recursion"),
)
COMMAND_PATTERN = re.compile(
    r"\b(?:" 
    r"please\s+)?(?:"
    r"explain|teach\s+me|tell\s+me\s+about|describe|define|what\s+is|what\s+are|how\s+does|how\s+do|why\s+does|why\s+do|"
    r"give(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|"
    r"show(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|"
    r"create(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|"
    r"make(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|"
    r"generate(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?"
    r")\b",
    flags=re.IGNORECASE,
)
FILLER_TOPIC_PATTERN = re.compile(
    r"\b("
    r"please|kindly|can|could|would|you|me|about|of|for|on|in|with|a|an|the|what|is|are|how|why|do|does|"
    r"explain|teach|tell|describe|define|give|show|create|make|generate|"
    r"concept|topic|question|answer|explanation|"
    r"simple|simpler|simply|easy|easier|basic|technical|technically|advanced|"
    r"example|examples|real[-\s]?life|way|words|detail|detailed|deep|depth|dive|"
    r"notes|code|program|implementation|output|step|quiz|full|short|brief|quick|and|or|"
    r"interview|viva|class|study|mode|algorithm|method|approach|function|structure|data"
    r")\b",
    flags=re.IGNORECASE,
)
GENERIC_TOPICS = {
    "it",
    "this",
    "that",
    "concept",
    "topic",
    "question",
    "example",
    "explanation",
}


def _normalize_topic_phrasing(value: str) -> str:
    normalized = re.sub(r"[_]+", " ", value or "")
    for pattern, replacement in TOPIC_NORMALIZATION_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def clean_core_topic(value: str, max_words: int = 2) -> str:
    """Extract the clean 1-2 word concept from a learner message or stored topic."""
    if not value or not value.strip():
        return ""

    topic = _normalize_topic_phrasing(value)
    topic = COMMAND_PATTERN.sub(" ", topic)
    topic = re.sub(
        r"\b(in\s+)?(a\s+)?(very\s+)?(simple|simpler|easy|easier|basic)\s+(way|words)\b",
        " ",
        topic,
        flags=re.IGNORECASE,
    )
    topic = re.sub(r"\b(with\s+)?(real[-\s]?life\s+)?examples?\b", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\b(in\s+)?(technical|advanced)\s+(way|detail)\b", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(
        r"\b(full\s+notes|class\s+notes|study\s+notes|interview\s+mode|notes\s+mode)\b",
        " ",
        topic,
        flags=re.IGNORECASE,
    )
    topic = re.sub(
        r"\b(in\s+depth|in\s+detail|detail|detailed|full\s+notes|notes|with\s+code|with\s+output|step\s+by\s+step)\b",
        " ",
        topic,
        flags=re.IGNORECASE,
    )
    topic = re.sub(r"\b(short|brief|quick|summary|interview|viva)\b", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\b(?:in|using|with)\s+(python|java|c)\b", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\b(?:python|java|c)\s+(?:code|program|implementation)\b", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\b(code|program|implementation|output)\b", " ", topic, flags=re.IGNORECASE)
    topic = FILLER_TOPIC_PATTERN.sub(" ", topic)
    topic = _normalize_topic_phrasing(topic)
    topic = re.sub(r"^(?:and|or)\b", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\b(?:and|or)$", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\s+", " ", topic).strip(" .?!:-_").lower()

    if not re.search(r"[a-z0-9]", topic, flags=re.IGNORECASE):
        return ""

    limited_topic = " ".join(topic.split()[:max_words])
    if limited_topic in GENERIC_TOPICS:
        return ""

    return limited_topic


def normalize_topic_text(value: str, fallback: str = "") -> str:
    """Return a sanitized topic, preserving a normalized fallback when needed."""
    cleaned_topic = clean_core_topic(value)
    if cleaned_topic:
        return cleaned_topic

    return " ".join((value or fallback).strip().lower().split())
