"""Chat history routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import get_db
from backend.services.topic_utils import normalize_topic_text


router = APIRouter()


@router.get(
    "/history/{user_id}",
    response_model=schemas.ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_history(
    user_id: str,
    limit: int = Query(default=12, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Return recent chat history in reverse chronological order."""
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id cannot be empty.")

    history = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.user_id == cleaned_user_id)
        .order_by(models.ChatHistory.created_at.desc(), models.ChatHistory.id.desc())
        .limit(limit)
        .all()
    )

    history_items = [
        schemas.ChatHistoryItem(
            topic=normalize_topic_text(item.topic, fallback="topic"),
            user_message=item.user_message,
            ai_response=item.ai_response,
            learner_level=item.learner_level,
            language=item.language,
            created_at=item.created_at,
        )
        for item in history
    ]

    return schemas.ChatHistoryResponse(user_id=cleaned_user_id, history=history_items)
