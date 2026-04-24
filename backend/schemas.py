"""Pydantic request and response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LevelLiteral = Literal["beginner", "intermediate", "advanced"]
LanguageLiteral = Literal["English", "Hindi", "Hinglish"]
ExplanationModeLiteral = Literal["standard", "simpler", "example", "technical", "quiz"]
ResponseDepthLiteral = Literal["normal", "detailed"]
ResponseModeLiteral = Literal["auto", "short", "detailed", "notes", "code", "with_code", "interview"]
CodeLanguageLiteral = Literal["Python", "Java", "C"]


class ChatRequest(BaseModel):
    """Incoming payload for the /chat endpoint."""

    user_id: str = Field(..., min_length=1, examples=["user_001"])
    message: str = Field(..., min_length=1, examples=["Explain recursion"])
    request_id: str | None = Field(default=None, examples=["chat_123"])
    topic: str | None = Field(default=None, examples=["recursion"])
    mode: ExplanationModeLiteral = Field(default="standard", examples=["simpler"])
    response_depth: ResponseDepthLiteral = Field(default="normal", examples=["detailed"])
    response_mode: ResponseModeLiteral = Field(default="auto", examples=["notes"])
    code_required: bool | None = Field(default=None, examples=[True])
    code_language: CodeLanguageLiteral | None = Field(default=None, examples=["Python"])


class ChatResponse(BaseModel):
    """Outgoing payload for the /chat endpoint."""

    response: str
    explanation: str | None = None
    level: LevelLiteral
    topic: str
    language: LanguageLiteral
    mode: ExplanationModeLiteral
    response_depth: ResponseDepthLiteral
    response_mode: ResponseModeLiteral
    request_id: str | None = None
    error_type: str | None = None


class UserRead(BaseModel):
    """Optional read schema for user records."""

    id: int
    user_id: str
    level: str
    preferred_language: str

    model_config = ConfigDict(from_attributes=True)


class LanguageUpdateRequest(BaseModel):
    """Incoming payload for language preference updates."""

    user_id: str = Field(..., min_length=1, examples=["user_001"])
    preferred_language: str = Field(..., min_length=1, examples=["Hindi"])


class LanguageUpdateResponse(BaseModel):
    """Language preference update response."""

    user_id: str
    preferred_language: LanguageLiteral
    message: str


class UserProfileResponse(BaseModel):
    """Small learner profile response for UI hydration."""

    user_id: str
    current_level: LevelLiteral
    preferred_language: LanguageLiteral


class QuizRequest(BaseModel):
    """Incoming payload for quiz generation."""

    user_id: str = Field(..., min_length=1, examples=["user_001"])
    topic: str = Field(..., min_length=1, examples=["recursion"])
    language: LanguageLiteral = Field(default="Hinglish", examples=["Hinglish"])
    count: int = Field(default=5, ge=3, le=15, examples=[5])
    level: LevelLiteral | None = Field(default=None, examples=["beginner"])


class QuizQuestion(BaseModel):
    """A single multiple-choice question."""

    question: str = Field(..., min_length=1)
    options: list[str] = Field(..., min_length=2, max_length=4)
    correct_answer: str = Field(..., min_length=1)


class QuizResponse(BaseModel):
    """Outgoing quiz payload."""

    topic: str
    questions: list[QuizQuestion] = Field(..., min_length=1)


class QuizAnswer(BaseModel):
    """One submitted quiz answer."""

    question: str = Field(..., min_length=1)
    selected_answer: str = Field(..., min_length=1)
    correct_answer: str = Field(..., min_length=1)


class EvaluateRequest(BaseModel):
    """Incoming payload for quiz evaluation."""

    user_id: str = Field(..., min_length=1, examples=["user_001"])
    topic: str = Field(..., min_length=1, examples=["recursion"])
    answers: list[QuizAnswer] = Field(..., min_length=1)


class EvaluateResponse(BaseModel):
    """Quiz evaluation result plus adaptive feedback."""

    score_percent: int
    correct_answers: int
    total_questions: int
    new_level: LevelLiteral
    weak_area: str
    feedback: str


class TopicProgressRead(BaseModel):
    """Topic-level mastery data for the dashboard."""

    topic: str
    mastery_percent: int
    weak_points: list[str] = Field(default_factory=list)


class ProgressResponse(BaseModel):
    """Aggregated learner progress for the dashboard."""

    user_id: str
    current_level: LevelLiteral
    preferred_language: LanguageLiteral
    weak_topics: list[str]
    topic_progress: list[TopicProgressRead]
    recent_scores: list[int]


class ChatHistoryItem(BaseModel):
    """A persisted chat interaction for a learner."""

    topic: str
    user_message: str
    ai_response: str
    learner_level: LevelLiteral
    language: LanguageLiteral
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    """Recent chat history response."""

    user_id: str
    history: list[ChatHistoryItem]


class RecommendationsResponse(BaseModel):
    """Recommended next topics for adaptive study."""

    user_id: str
    recommended_topics: list[str]
