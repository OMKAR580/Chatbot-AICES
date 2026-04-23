"""Quiz generation and evaluation routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import get_db
from backend.services.adaptation_engine import (
    detect_weak_area,
    get_user_level,
    update_concept_progress,
    update_user_level_from_score,
)
from backend.services.ai_service import (
    AIServiceError,
    MissingAPIKeyError,
    generate_feedback,
    generate_quiz,
    normalize_language,
)
from backend.services.topic_utils import normalize_topic_text


router = APIRouter()


@router.post("/quiz", response_model=schemas.QuizResponse, status_code=status.HTTP_200_OK)
def create_quiz(payload: schemas.QuizRequest, db: Session = Depends(get_db)):
    """Generate a short adaptive MCQ quiz for the requested topic."""
    user_id = payload.user_id.strip()
    topic = normalize_topic_text(payload.topic, fallback="").strip()
    question_count = payload.count

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id cannot be empty.")

    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="topic cannot be empty.")

    user = _get_or_create_user(db=db, user_id=user_id, preferred_language=payload.language)
    level = payload.level or get_user_level(db=db, user_id=user.user_id)
    language = normalize_language(user.preferred_language or payload.language)

    try:
        quiz_payload = generate_quiz(
            topic=topic,
            level=level,
            language=language,
            count=question_count,
        )
        return schemas.QuizResponse.model_validate(quiz_payload)
    except MissingAPIKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider returned malformed quiz data.",
        ) from exc


@router.post("/evaluate", response_model=schemas.EvaluateResponse, status_code=status.HTTP_200_OK)
def evaluate_quiz(payload: schemas.EvaluateRequest, db: Session = Depends(get_db)):
    """Evaluate submitted answers, update learner state, and return feedback."""
    user_id = payload.user_id.strip()
    topic = normalize_topic_text(payload.topic, fallback="").strip()
    answers = payload.answers

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id cannot be empty.")

    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="topic cannot be empty.")

    if not answers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="answers cannot be empty.")

    user = _get_or_create_user(db=db, user_id=user_id)
    total_questions = len(answers)
    correct_answers = sum(
        1
        for answer in answers
        if _normalize_answer(answer.selected_answer) == _normalize_answer(answer.correct_answer)
    )
    score_percent = int(round((correct_answers / total_questions) * 100))
    weak_area = detect_weak_area(topic=topic, answers=answers)
    new_level = update_user_level_from_score(
        db=db,
        user_id=user_id,
        score_percent=score_percent,
    )

    update_concept_progress(
        db=db,
        user_id=user_id,
        topic=topic,
        score_percent=score_percent,
        weak_area=weak_area,
    )
    db.add(
        models.QuizResult(
            user_id=user_id,
            topic=topic,
            total_questions=total_questions,
            correct_answers=correct_answers,
            score_percent=score_percent,
            learner_level_after_quiz=new_level,
            weak_area=weak_area,
        )
    )
    db.commit()

    feedback = generate_feedback(
        topic=topic,
        score=score_percent,
        weak_area=weak_area,
        level=new_level,
        language=user.preferred_language,
    )

    return schemas.EvaluateResponse(
        score_percent=score_percent,
        correct_answers=correct_answers,
        total_questions=total_questions,
        new_level=new_level,
        weak_area=weak_area,
        feedback=feedback,
    )


def _get_or_create_user(
    db: Session,
    user_id: str,
    preferred_language: str | None = None,
) -> models.User:
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is not None:
        normalized_language = normalize_language(user.preferred_language)
        if user.preferred_language != normalized_language:
            user.preferred_language = normalized_language
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    user = models.User(
        user_id=user_id,
        preferred_language=normalize_language(preferred_language),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _normalize_answer(answer: str) -> str:
    return " ".join((answer or "").strip().lower().split())
