"""Topic recommendation engine driven by recent learner study history."""

from sqlalchemy.orm import Session

from backend import models
from backend.services.topic_utils import normalize_topic_text


TOPIC_RECOMMENDATION_MAP = {
    "probability": [
        "Probability Basics",
        "Conditional Probability",
        "Bayes Theorem",
        "Practice Problems",
    ],
    "cnn": [
        "Convolution Operation",
        "Filters and Kernels",
        "Pooling Layers",
        "CNN Practice Problems",
    ],
    "machine learning": [
        "Machine Learning Basics",
        "Supervised vs Unsupervised Learning",
        "Model Evaluation",
        "Machine Learning Practice Problems",
    ],
    "deep learning": [
        "Deep Learning Basics",
        "Activation Functions",
        "Backpropagation",
        "Deep Learning Practice Problems",
    ],
    "neural network": [
        "Neural Network Basics",
        "Activation Functions",
        "Forward and Backward Propagation",
        "Neural Network Practice Problems",
    ],
    "linked list": [
        "Linked List Basics",
        "Singly vs Doubly Linked List",
        "Linked List Operations",
        "Linked List Practice Problems",
    ],
    "binary search": [
        "Binary Search Basics",
        "Boundary Conditions",
        "Sorted Array Search",
        "Binary Search Practice Problems",
    ],
    "array": [
        "Array Basics",
        "Array Traversal",
        "Insertion and Deletion",
        "Array Practice Problems",
    ],
    "stack": [
        "Stack Basics",
        "Push and Pop Operations",
        "Stack vs Queue",
        "Stack Practice Problems",
    ],
    "queue": [
        "Queue Basics",
        "Enqueue and Dequeue Operations",
        "Queue vs Stack",
        "Queue Practice Problems",
    ],
    "tree": [
        "Tree Basics",
        "Tree Traversal",
        "Binary Tree Practice",
        "Tree Practice Problems",
    ],
    "graph": [
        "Graph Basics",
        "BFS and DFS",
        "Graph Representation",
        "Graph Practice Problems",
    ],
    "recursion": [
        "Recursion Basics",
        "Base Case and Recursive Case",
        "Recursive Dry Run",
        "Recursion Practice Problems",
    ],
    "dbms": [
        "DBMS Basics",
        "Normalization",
        "Transactions and ACID",
        "DBMS Practice Problems",
    ],
    "os": [
        "OS Basics",
        "Process vs Thread",
        "Scheduling",
        "OS Practice Problems",
    ],
    "oop": [
        "OOP Basics",
        "Encapsulation and Inheritance",
        "Polymorphism",
        "OOP Practice Problems",
    ],
    "dsa": [
        "DSA Basics",
        "Complexity Analysis",
        "Core Data Structures",
        "DSA Practice Problems",
    ],
}


def get_recommendations(db: Session, user_id: str, limit: int = 5) -> list[str]:
    """Return unique next-study suggestions from the learner's last 3 to 5 chat topics."""
    max_items = max(3, min(limit, 5))
    recent_topics = _get_recent_chat_topics(db=db, user_id=user_id, max_topics=5)
    if not recent_topics:
        recent_topics = _get_recent_progress_topics(db=db, user_id=user_id, max_topics=3)

    recommendations: list[str] = []
    for topic in recent_topics:
        for recommendation in _recommendations_for_topic(topic):
            _add_unique(recommendations, recommendation)
            if len(recommendations) >= max_items:
                return recommendations[:max_items]

    return recommendations[:max_items]


def _get_recent_chat_topics(db: Session, user_id: str, max_topics: int) -> list[str]:
    history_rows = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.user_id == user_id)
        .order_by(models.ChatHistory.created_at.desc(), models.ChatHistory.id.desc())
        .limit(15)
        .all()
    )
    recent_topics: list[str] = []
    seen_topics: set[str] = set()
    for row in history_rows:
        normalized_topic = normalize_topic_text(row.topic, fallback="")
        topic_key = _topic_key(normalized_topic)
        if not normalized_topic or topic_key in seen_topics:
            continue

        seen_topics.add(topic_key)
        recent_topics.append(normalized_topic)
        if len(recent_topics) >= max_topics:
            break

    return recent_topics


def _get_recent_progress_topics(db: Session, user_id: str, max_topics: int) -> list[str]:
    progress_rows = (
        db.query(models.ConceptProgress)
        .filter(models.ConceptProgress.user_id == user_id)
        .order_by(models.ConceptProgress.last_updated.desc(), models.ConceptProgress.id.desc())
        .limit(max_topics)
        .all()
    )
    recent_topics: list[str] = []
    for progress in progress_rows:
        normalized_topic = normalize_topic_text(progress.topic, fallback="")
        if normalized_topic:
            recent_topics.append(normalized_topic)
    return recent_topics


def _recommendations_for_topic(topic: str) -> list[str]:
    topic_key = _topic_key(topic)
    mapped_recommendations = TOPIC_RECOMMENDATION_MAP.get(topic_key)
    if mapped_recommendations:
        return mapped_recommendations

    display_topic = normalize_topic_text(topic, fallback="")
    if not display_topic:
        return []

    return [
        f"{display_topic} Basics",
        f"{display_topic} Key Concepts",
        f"{display_topic} Practice Problems",
    ]


def _topic_key(topic: str) -> str:
    normalized_topic = normalize_topic_text(topic, fallback="").strip().lower()
    if normalized_topic.startswith("cnn"):
        return "cnn"
    return normalized_topic


def _add_unique(recommendations: list[str], topic: str) -> None:
    cleaned_topic = topic.strip()
    if not cleaned_topic:
        return

    existing = {recommendation.strip().lower() for recommendation in recommendations}
    if cleaned_topic.lower() not in existing:
        recommendations.append(cleaned_topic)
