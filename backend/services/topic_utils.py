"""Shared topic cleaning helpers used across the AICES backend."""

import re


TOPIC_NORMALIZATION_PATTERNS = (
    (re.compile(r"\bdeepth\b", flags=re.IGNORECASE), "depth"),
    (re.compile(r"\bdeeply\b", flags=re.IGNORECASE), "depth"),
    (re.compile(r"\brobability\b", flags=re.IGNORECASE), "probability"),
    (re.compile(r"\bprobablity\b", flags=re.IGNORECASE), "probability"),
    (re.compile(r"\bprobabilty\b", flags=re.IGNORECASE), "probability"),
    (re.compile(r"\bprobabilities\b", flags=re.IGNORECASE), "probability"),
    (re.compile(r"\blinked[\s-]*lists?\b", flags=re.IGNORECASE), "linked list"),
    (re.compile(r"\blinkedlist\b", flags=re.IGNORECASE), "linked list"),
    (re.compile(r"\bbinary[\s-]*search(?:ing)?\b", flags=re.IGNORECASE), "binary search"),
    (re.compile(r"\bconvolutional\s+neural\s+networks?\b", flags=re.IGNORECASE), "cnn"),
    (re.compile(r"\bneural\s+networks?\b", flags=re.IGNORECASE), "neural network"),
    (re.compile(r"\barrays\b", flags=re.IGNORECASE), "array"),
    (re.compile(r"\bstacks\b", flags=re.IGNORECASE), "stack"),
    (re.compile(r"\bqueues\b", flags=re.IGNORECASE), "queue"),
    (re.compile(r"\btrees\b", flags=re.IGNORECASE), "tree"),
    (re.compile(r"\bgraphs\b", flags=re.IGNORECASE), "graph"),
    (re.compile(r"\brecursive\s+function\b", flags=re.IGNORECASE), "recursion"),
    (re.compile(r"\bmachne\s+learning\b", flags=re.IGNORECASE), "machine learning"),
    (re.compile(r"\bmachine\s+learing\b", flags=re.IGNORECASE), "machine learning"),
    (re.compile(r"\bachine\s+learning\b", flags=re.IGNORECASE), "machine learning"),
    (re.compile(r"\bnn\b", flags=re.IGNORECASE), "neural network"),
    (re.compile(r"\b/n\b", flags=re.IGNORECASE), "neural network"),
)
PROTECTED_TECHNICAL_TOPICS = (
    ("cnn", (r"\bcnn\b", r"\bcnn\s+model\b", r"\bconvolutional\s+neural\s+network\b")),
    ("natural language processing", (r"\bnlp\b", r"\bnatural\s+language\s+processing\b")),
    ("linked list", (r"\blinked\s+list\b", r"\blinkedlist\b")),
    ("binary search", (r"\bbinary\s+search\b", r"\bbinarysearch\b")),
    ("static routing", (r"\bstatic\s+routing\b",)),
    ("dynamic routing", (r"\bdynamic\s+routing\b",)),
    ("computer network", (r"\bcomputer\s+network(?:ing)?\b",)),
    ("deep learning", (r"\bdeep\s+learning\b",)),
    ("machine learning", (r"\bmachine\s+learning\b",)),
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
    ("probability", (r"\bprobability\b",)),
)
TOPIC_DISPLAY_LABELS = {
    "cnn": "CNN / Convolutional Neural Network",
    "linked list": "Linked List",
    "binary search": "Binary Search",
    "static routing": "Static Routing",
    "dynamic routing": "Dynamic Routing",
    "computer network": "Computer Network",
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
    "probability": "Probability",
    "natural language processing": "Natural Language Processing",
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
    return extract_topic(value)



def normalize_topic_text(value: str, fallback: str = "") -> str:
    """Return a sanitized topic, preserving a normalized fallback when needed."""
    cleaned = extract_topic(value)
    if cleaned:
        return cleaned
    return extract_topic(fallback)




def extract_topic(message: str) -> str:
    if not message:
        return ""

    STOP_WORDS = {
        "what", "is", "explain", "in", "the", "a", "an", "with", "example",
        "about", "of", "on", "for", "me", "tell", "teach", "define",
        "describe", "to", "are", "how", "why", "do", "does", "please", "kindly",
        "concept", "topic", "question", "answer", "and", "or"
    }

    MAPPINGS = {
        "ml": "Machine Learning",
        "ai": "Artificial Intelligence",
        "cnn": "Convolutional Neural Network",
        "nlp": "Natural Language Processing"
    }

    words = message.split()
    filtered = []

    for w in words:
        clean_w = w.lower().strip(".,?!:;()")

        if not clean_w or clean_w in STOP_WORDS:
            continue

        if clean_w in MAPPINGS:
            filtered.append(MAPPINGS[clean_w])
        else:
            filtered.append(clean_w)

    if not filtered:
        return ""

    topic = " ".join(filtered)

    protected = _extract_protected_topic(topic)
    if protected:
        return _format_topic_label(protected)

    return _format_topic_label(topic)