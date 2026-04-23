"""Rule-based adaptation engine for learner level and progress tracking."""

import json

from sqlalchemy.orm import Session

from backend import models
from backend.services.topic_utils import normalize_topic_text


DEFAULT_LEVEL = "beginner"
SUPPORTED_LEVELS = {"beginner", "intermediate", "advanced"}
LEVEL_ORDER = ["beginner", "intermediate", "advanced"]


def get_user_level(db: Session, user_id: str) -> str:
    """Return the stored learner level, falling back safely to beginner."""
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        return DEFAULT_LEVEL

    stored_level = (user.level or DEFAULT_LEVEL).lower()
    if stored_level not in SUPPORTED_LEVELS:
        return DEFAULT_LEVEL

    return stored_level


def update_user_level_from_score(db: Session, user_id: str, score_percent: float) -> str:
    """Update and return a user's level from quiz performance and recent trend."""
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        user = models.User(user_id=user_id)
        db.add(user)
        db.flush()

    current_level = get_user_level(db=db, user_id=user_id)
    score = _clamp_score(score_percent)
    new_level = _level_from_score(score)

    recent_scores = [
        _clamp_score(result.score_percent)
        for result in (
            db.query(models.QuizResult)
            .filter(models.QuizResult.user_id == user_id)
            .order_by(models.QuizResult.created_at.desc(), models.QuizResult.id.desc())
            .limit(2)
            .all()
        )
    ]
    score_trend = [score, *recent_scores]

    if len(score_trend) >= 3:
        current_score, previous_score, older_score = score_trend[:3]
        if current_score > previous_score > older_score and current_score >= 60:
            new_level = _higher_level(new_level, _raise_level(current_level))
        elif current_score < previous_score < older_score and current_score < 50:
            new_level = _lower_level(new_level)
        elif all(recent_score < 40 for recent_score in score_trend[:3]):
            new_level = "beginner"

    user.level = new_level
    db.add(user)
    db.flush()
    return new_level


def detect_weak_area(topic: str, answers: list) -> str:
    """Infer the likely weak area from incorrectly answered questions."""
    incorrect_questions = []
    for answer in answers:
        selected_answer = getattr(answer, "selected_answer", "")
        correct_answer = getattr(answer, "correct_answer", "")
        if _normalize_answer(selected_answer) != _normalize_answer(correct_answer):
            incorrect_questions.append(getattr(answer, "question", ""))

    if not incorrect_questions:
        return "none"

    keyword_map = {
        "base condition": ["base", "condition", "terminate", "termination", "stop"],
        "recursive flow": ["recursive call", "flow", "stack", "trace", "unwind"],
        "edge cases": ["edge", "empty", "zero", "negative", "boundary", "overflow"],
        "time and space complexity": ["complexity", "time", "space", "big o", "performance"],
        "implementation logic": ["code", "output", "logic", "result", "function", "loop"],
    }

    combined_questions = " ".join(incorrect_questions).lower()
    scored_areas = {
        area: sum(1 for keyword in keywords if keyword in combined_questions)
        for area, keywords in keyword_map.items()
    }
    best_area, best_score = max(scored_areas.items(), key=lambda item: item[1])

    if best_score > 0:
        return best_area

    cleaned_topic = normalize_topic_text(topic, fallback="topic")
    return f"{cleaned_topic} fundamentals"


def update_concept_progress(
    db: Session,
    user_id: str,
    topic: str,
    score_percent: float,
    weak_area: str,
) -> models.ConceptProgress:
    """Create or update the latest mastery snapshot for a topic."""
    cleaned_topic = normalize_topic_text(topic, fallback="")
    score = _clamp_score(score_percent)
    weak_points = []

    progress = (
        db.query(models.ConceptProgress)
        .filter(
            models.ConceptProgress.user_id == user_id,
            models.ConceptProgress.topic == cleaned_topic,
        )
        .first()
    )

    if progress is not None:
        weak_points = _load_weak_points(progress.weak_points)
        progress.mastery_percent = round((progress.mastery_percent * 0.65) + (score * 0.35), 2)
    else:
        progress = models.ConceptProgress(
            user_id=user_id,
            topic=cleaned_topic,
            mastery_percent=score,
        )

    if weak_area and weak_area != "none" and weak_area not in weak_points:
        weak_points.append(weak_area)

    recent_topic_scores = [
        score,
        *[
            _clamp_score(result.score_percent)
            for result in (
                db.query(models.QuizResult)
                .filter(
                    models.QuizResult.user_id == user_id,
                    models.QuizResult.topic == cleaned_topic,
                )
                .order_by(models.QuizResult.created_at.desc(), models.QuizResult.id.desc())
                .limit(2)
                .all()
            )
        ],
    ]
    repeated_low_score_label = "repeated low quiz scores"
    if len(recent_topic_scores) >= 2 and all(recent_score < 50 for recent_score in recent_topic_scores[:2]):
        if repeated_low_score_label not in weak_points:
            weak_points.append(repeated_low_score_label)
    elif score >= 70 and repeated_low_score_label in weak_points:
        weak_points.remove(repeated_low_score_label)

    if score > 70 and weak_area in weak_points:
        weak_points.remove(weak_area)

    progress.weak_points = json.dumps(weak_points)
    db.add(progress)
    db.flush()
    return progress


def _level_from_score(score_percent: float) -> str:
    if score_percent < 40:
        return "beginner"

    if score_percent <= 70:
        return "intermediate"

    return "advanced"


def _raise_level(level: str) -> str:
    current_index = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 0
    return LEVEL_ORDER[min(current_index + 1, len(LEVEL_ORDER) - 1)]


def _lower_level(level: str) -> str:
    current_index = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 0
    return LEVEL_ORDER[max(current_index - 1, 0)]


def _higher_level(first_level: str, second_level: str) -> str:
    first_index = LEVEL_ORDER.index(first_level) if first_level in LEVEL_ORDER else 0
    second_index = LEVEL_ORDER.index(second_level) if second_level in LEVEL_ORDER else 0
    return LEVEL_ORDER[max(first_index, second_index)]


def _clamp_score(score_percent: float) -> float:
    return max(0, min(100, float(score_percent)))


def _normalize_answer(answer: str) -> str:
    return " ".join((answer or "").strip().lower().split())


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
