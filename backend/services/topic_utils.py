"""Shared topic cleaning helpers used across the AICES backend."""

import re


TOPIC_NORMALIZATION_PATTERNS = (
    (re.compile(r"\bdeepth\b", flags=re.IGNORECASE), "depth"),
    (re.compile(r"\bdeeply\b", flags=re.IGNORECASE), "depth"),
    (re.compile(r"\blinked[\s-]*lists?\b", flags=re.IGNORECASE), "linked list"),
    (re.compile(r"\bbinary[\s-]*search(?:ing)?\b", flags=re.IGNORECASE), "binary search"),
    (re.compile(r"\bconvolutional\s+neural\s+networks?\b", flags=re.IGNORECASE), "cnn"),
    (re.compile(r"\bneural\s+networks?\b", flags=re.IGNORECASE), "neural network"),
    (re.compile(r"\barrays\b", flags=re.IGNORECASE), "array"),
    (re.compile(r"\bstacks\b", flags=re.IGNORECASE), "stack"),
    (re.compile(r"\bqueues\b", flags=re.IGNORECASE), "queue"),
    (re.compile(r"\btrees\b", flags=re.IGNORECASE), "tree"),
    (re.compile(r"\bgraphs\b", flags=re.IGNORECASE), "graph"),
    (re.compile(r"\brecursive\s+function\b", flags=re.IGNORECASE), "recursion"),
)
PROTECTED_TECHNICAL_TOPICS = (
    ("cnn", (r"\bcnn\b", r"\bcnn\s+model\b", r"\bconvolutional\s+neural\s+network\b")),
    ("linked list", (r"\blinked\s+list\b", r"\blinkedlist\b")),
    ("binary search", (r"\bbinary\s+search\b", r"\bbinarysearch\b")),
    ("neural network", (r"\bneural\s+network\b",)),
    ("array", (r"\barray\b",)),
    ("stack", (r"\bstack\b",)),
    ("queue", (r"\bqueue\b",)),
    ("tree", (r"\btree\b",)),
    ("graph", (r"\bgraph\b",)),
    ("dbms", (r"\bdbms\b",)),
    ("os", (r"\bos\b",)),
    ("cn", (r"\bcn\b",)),
    ("oop", (r"\boop\b",)),
    ("dsa", (r"\bdsa\b",)),
    ("recursion", (r"\brecursion\b",)),
    ("deep learning", (r"\bdeep\s+learning\b",)),
    ("machine learning", (r"\bmachine\s+learning\b",)),
)
TOPIC_DISPLAY_LABELS = {
    "cnn": "CNN / Convolutional Neural Network",
    "linked list": "Linked List",
    "binary search": "Binary Search",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "neural network": "Neural Network",
    "array": "Array",
    "stack": "Stack",
    "queue": "Queue",
    "tree": "Tree",
    "graph": "Graph",
    "dbms": "DBMS",
    "os": "OS",
    "cn": "CN",
    "oop": "OOP",
    "dsa": "DSA",
    "recursion": "Recursion",
}
ALL_PROTECTED_TERMS = frozenset(TOPIC_DISPLAY_LABELS)
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
UPPERCASE_TOPIC_TOKENS = {"cnn", "dbms", "os", "cn", "oop", "dsa"}


def _normalize_topic_phrasing(value: str) -> str:
    normalized = re.sub(r"[_]+", " ", value or "")
    for pattern, replacement in TOPIC_NORMALIZATION_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def _normalize_topic_search_text(value: str) -> str:
    normalized = _normalize_topic_phrasing(value)
    normalized = normalized.replace("/", " ")
    normalized = re.sub(r"[^a-zA-Z0-9\s-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def _extract_protected_topic(value: str) -> str:
    search_text = _normalize_topic_search_text(value)
    if not search_text:
        return ""

    for canonical_topic, patterns in PROTECTED_TECHNICAL_TOPICS:
        if any(re.search(pattern, search_text, flags=re.IGNORECASE) for pattern in patterns):
            return canonical_topic

    return ""


def _format_topic_label(topic: str) -> str:
    normalized_topic = _normalize_topic_search_text(topic)
    if normalized_topic in TOPIC_DISPLAY_LABELS:
        return TOPIC_DISPLAY_LABELS[normalized_topic]

    if not normalized_topic:
        return ""

    parts = []
    for part in normalized_topic.split():
        if part in UPPERCASE_TOPIC_TOKENS:
            parts.append(part.upper())
        else:
            parts.append(part.capitalize())
    return " ".join(parts)


def clean_core_topic(value: str, max_words: int = 4) -> str:
    """Extract the clean concept from a learner message or stored topic."""
    if not value or not value.strip():
        return ""

    topic = _normalize_topic_phrasing(value)
    protected_topic = _extract_protected_topic(topic)
    if protected_topic:
        return _format_topic_label(protected_topic)

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

    protected_topic = _extract_protected_topic(topic)
    if protected_topic:
        return _format_topic_label(protected_topic)

    topic = FILLER_TOPIC_PATTERN.sub(" ", topic)
    topic = _normalize_topic_phrasing(topic)
    topic = re.sub(r"^(?:and|or)\b", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\b(?:and|or)$", " ", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\s+", " ", topic).strip(" .?!:-_").lower()

    if not re.search(r"[a-z0-9]", topic, flags=re.IGNORECASE):
        return ""

    protected_topic = _extract_protected_topic(topic)
    if protected_topic:
        return _format_topic_label(protected_topic)

    limited_topic = " ".join(topic.split()[:max_words])
    if limited_topic in GENERIC_TOPICS:
        return ""

    return _format_topic_label(limited_topic)


def normalize_topic_text(value: str, fallback: str = "") -> str:
    """Return a sanitized topic, preserving a normalized fallback when needed."""
    cleaned_topic = clean_core_topic(value)
    if cleaned_topic:
        return cleaned_topic

    normalized_fallback = _normalize_topic_search_text(value or fallback)
    return _format_topic_label(normalized_fallback)
