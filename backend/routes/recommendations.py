"""Adaptive topic recommendation routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import schemas
from backend.database import get_db
from backend.services.recommendation_engine import get_recommendations


router = APIRouter()


@router.get(
    "/recommendations/{user_id}",
    response_model=schemas.RecommendationsResponse,
    status_code=status.HTTP_200_OK,
)
def recommendations(user_id: str, db: Session = Depends(get_db)):
    """Return recommended next topics for the learner."""
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id cannot be empty.")

    return schemas.RecommendationsResponse(
        user_id=cleaned_user_id,
        recommended_topics=get_recommendations(db=db, user_id=cleaned_user_id),
    )
