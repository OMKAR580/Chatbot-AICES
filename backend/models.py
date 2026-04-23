"""SQLAlchemy ORM models."""

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, UniqueConstraint, func

from backend.database import Base


class User(Base):
    """Stores a learner profile used by the adaptation engine."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    level = Column(String, nullable=False, default="beginner")
    preferred_language = Column(String, nullable=False, default="Hinglish")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QuizResult(Base):
    """Stores every submitted quiz attempt for progress analytics."""

    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    topic = Column(String, index=True, nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percent = Column(Float, nullable=False)
    learner_level_after_quiz = Column(String, nullable=False)
    weak_area = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ConceptProgress(Base):
    """Stores the latest topic-level mastery snapshot for a learner."""

    __tablename__ = "concept_progress"
    __table_args__ = (UniqueConstraint("user_id", "topic", name="uq_concept_progress_user_topic"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    topic = Column(String, index=True, nullable=False)
    mastery_percent = Column(Float, nullable=False, default=0)
    weak_points = Column(Text, nullable=True)
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ChatHistory(Base):
    """Stores successful adaptive chat interactions for session continuity."""

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    topic = Column(String, index=True, nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    learner_level = Column(String, nullable=False)
    language = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
