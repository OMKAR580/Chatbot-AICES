"""Learner progress and dashboard routes."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import get_db
from backend.services.adaptation_engine import get_user_level
from backend.services.ai_service import normalize_language
from backend.services.topic_utils import normalize_topic_text


router = APIRouter()


@router.get(
    "/progress/{user_id}",
    response_model=schemas.ProgressResponse,
    status_code=status.HTTP_200_OK,
)
def get_progress(user_id: str, db: Session = Depends(get_db)):
    """Return the learner's current level, quiz history, and topic mastery."""
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id cannot be empty.")

    recent_quizzes = (
        db.query(models.QuizResult)
        .filter(models.QuizResult.user_id == cleaned_user_id)
        .order_by(models.QuizResult.created_at.desc(), models.QuizResult.id.desc())
        .limit(5)
        .all()
    )
    progress_rows = (
        db.query(models.ConceptProgress)
        .filter(models.ConceptProgress.user_id == cleaned_user_id)
        .order_by(models.ConceptProgress.last_updated.desc(), models.ConceptProgress.id.desc())
        .all()
    )
    user = db.query(models.User).filter(models.User.user_id == cleaned_user_id).first()
    preferred_language = normalize_language(user.preferred_language if user else "Hinglish")

    topic_progress = [
        schemas.TopicProgressRead(
            topic=normalize_topic_text(progress.topic, fallback="topic"),
            mastery_percent=int(round(progress.mastery_percent or 0)),
            weak_points=_load_weak_points(progress.weak_points),
        )
        for progress in progress_rows
    ]

    weak_topics = _detect_weak_topics(progress_rows=progress_rows, user_id=cleaned_user_id, db=db)

    return schemas.ProgressResponse(
        user_id=cleaned_user_id,
        current_level=get_user_level(db=db, user_id=cleaned_user_id),
        preferred_language=preferred_language,
        weak_topics=weak_topics,
        topic_progress=topic_progress,
        recent_scores=[int(round(quiz.score_percent or 0)) for quiz in recent_quizzes],
    )


def _detect_weak_topics(
    progress_rows: list[models.ConceptProgress],
    user_id: str,
    db: Session,
) -> list[str]:
    weak_topics = {
        normalize_topic_text(progress.topic, fallback="topic")
        for progress in progress_rows
        if (progress.mastery_percent or 0) < 50 or _load_weak_points(progress.weak_points)
    }

    quiz_rows = (
        db.query(models.QuizResult)
        .filter(models.QuizResult.user_id == user_id)
        .order_by(models.QuizResult.topic.asc(), models.QuizResult.created_at.desc())
        .all()
    )
    scores_by_topic: dict[str, list[float]] = {}
    for quiz in quiz_rows:
        scores_by_topic.setdefault(quiz.topic, []).append(quiz.score_percent)

    for topic, scores in scores_by_topic.items():
        recent_scores = scores[:2]
        if len(recent_scores) >= 2 and all(score < 50 for score in recent_scores):
            weak_topics.add(normalize_topic_text(topic, fallback="topic"))

    return sorted(weak_topics)


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
