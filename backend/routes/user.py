"""Learner profile routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import get_db
from backend.services.adaptation_engine import get_user_level
from backend.services.ai_service import normalize_language


router = APIRouter()
SUPPORTED_LANGUAGE_INPUTS = {"english", "hindi", "hinglish"}


@router.post(
    "/user/language",
    response_model=schemas.LanguageUpdateResponse,
    status_code=status.HTTP_200_OK,
)
def update_language(payload: schemas.LanguageUpdateRequest, db: Session = Depends(get_db)):
    """Update and persist the learner's preferred explanation language."""
    user_id = payload.user_id.strip()
    preferred_language = payload.preferred_language.strip()

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id cannot be empty.")

    if preferred_language.lower() not in SUPPORTED_LANGUAGE_INPUTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="preferred_language must be English, Hindi, or Hinglish.",
        )

    user = _get_or_create_user(db=db, user_id=user_id)
    user.preferred_language = normalize_language(preferred_language)
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.LanguageUpdateResponse(
        user_id=user.user_id,
        preferred_language=user.preferred_language,
        message="Language updated successfully",
    )


@router.get(
    "/user/{user_id}",
    response_model=schemas.UserProfileResponse,
    status_code=status.HTTP_200_OK,
)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Return a compact learner profile for frontend hydration."""
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id cannot be empty.")

    user = _get_or_create_user(db=db, user_id=cleaned_user_id)
    language = normalize_language(user.preferred_language)
    if user.preferred_language != language:
        user.preferred_language = language
        db.add(user)
        db.commit()
        db.refresh(user)

    return schemas.UserProfileResponse(
        user_id=user.user_id,
        current_level=get_user_level(db=db, user_id=user.user_id),
        preferred_language=user.preferred_language,
    )


def _get_or_create_user(db: Session, user_id: str) -> models.User:
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is not None:
        return user

    user = models.User(user_id=user_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
