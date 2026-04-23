"""Rule-based topic recommendation engine for AICES."""

import json

from sqlalchemy.orm import Session

from backend import models
from backend.services.topic_utils import normalize_topic_text


DEFAULT_RECOMMENDATIONS = [
    "Recursion basics",
    "Binary search dry run",
    "Stack vs Queue",
    "Time complexity basics",
    "Base condition practice",
]

FOUNDATIONAL_TOPIC_MAP = {
    "recursion": ["Recursion basics", "Base condition practice", "Recursive flow dry run"],
    "binary search": ["Binary search dry run", "Search boundary practice", "Time complexity basics"],
    "stack": ["Stack operations", "Stack vs Queue", "Call stack basics"],
    "queue": ["Queue operations", "Stack vs Queue", "Breadth-first search basics"],
    "tree": ["Tree traversal basics", "Recursion in trees", "Depth-first search basics"],
    "graph": ["Graph traversal basics", "Breadth-first search basics", "Depth-first search basics"],
}


def get_recommendations(db: Session, user_id: str, limit: int = 5) -> list[str]:
    """Return 3 to 5 recommended next topics using simple progress signals."""
    recommendations: list[str] = []
    progress_rows = (
        db.query(models.ConceptProgress)
        .filter(models.ConceptProgress.user_id == user_id)
        .order_by(models.ConceptProgress.mastery_percent.asc(), models.ConceptProgress.last_updated.desc())
        .all()
    )

    weak_topics = []
    low_mastery_topics = []
    for progress in progress_rows:
        normalized_topic = normalize_topic_text(progress.topic, fallback="")
        if not normalized_topic:
            continue

        if (progress.mastery_percent or 0) < 50 or _load_weak_points(progress.weak_points):
            weak_topics.append(normalized_topic)
        elif 50 <= (progress.mastery_percent or 0) < 70:
            low_mastery_topics.append(normalized_topic)

    recent_quizzes = (
        db.query(models.QuizResult)
        .filter(models.QuizResult.user_id == user_id)
        .order_by(models.QuizResult.created_at.desc(), models.QuizResult.id.desc())
        .limit(10)
        .all()
    )
    for quiz in recent_quizzes:
        normalized_topic = normalize_topic_text(quiz.topic, fallback="")
        if quiz.score_percent < 50 and normalized_topic not in weak_topics:
            weak_topics.append(normalized_topic)

    for topic in weak_topics:
        _add_topic_recommendations(recommendations, topic)

    for topic in low_mastery_topics:
        _add_unique(recommendations, f"{_title_topic(topic)} revision sprint")
        _add_topic_recommendations(recommendations, topic)

    recent_history = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.user_id == user_id)
        .order_by(models.ChatHistory.created_at.desc(), models.ChatHistory.id.desc())
        .limit(5)
        .all()
    )
    for history_item in recent_history:
        normalized_topic = normalize_topic_text(history_item.topic, fallback="")
        if normalized_topic:
            _add_topic_recommendations(recommendations, normalized_topic)

    for default_topic in DEFAULT_RECOMMENDATIONS:
        _add_unique(recommendations, default_topic)

    return recommendations[: max(3, min(limit, 5))]


def _add_topic_recommendations(recommendations: list[str], topic: str) -> None:
    normalized_topic = _topic_key(topic)
    related_topics = FOUNDATIONAL_TOPIC_MAP.get(normalized_topic)

    if related_topics:
        for related_topic in related_topics:
            _add_unique(recommendations, related_topic)
        return

    if normalized_topic:
        if normalized_topic.endswith("basics"):
            _add_unique(recommendations, f"{_title_topic(normalized_topic)} practice")
            return

        _add_unique(recommendations, f"{_title_topic(normalized_topic)} basics")
        _add_unique(recommendations, f"{_title_topic(normalized_topic)} example practice")


def _add_unique(recommendations: list[str], topic: str) -> None:
    normalized_existing = {recommendation.strip().lower() for recommendation in recommendations}
    cleaned_topic = topic.strip()
    if cleaned_topic and cleaned_topic.lower() not in normalized_existing:
        recommendations.append(cleaned_topic)


def _title_topic(topic: str) -> str:
    return " ".join(word.capitalize() for word in topic.split())


def _topic_key(topic: str) -> str:
    normalized_topic = normalize_topic_text(topic, fallback="")
    for suffix in (" revision sprint", " example practice", " dry run", " practice", " basics"):
        if normalized_topic.endswith(suffix):
            return normalized_topic[: -len(suffix)].strip() or normalized_topic

    return normalized_topic


def _load_weak_points(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []

    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError:
        return [point.strip() for point in raw_value.split(",") if point.strip()]

    if not isinstance(parsed_value, list):
        return []

    return [str(point).strip() for point in parsed_value if str(point).strip()]
