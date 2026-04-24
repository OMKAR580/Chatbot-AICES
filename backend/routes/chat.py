"""Chat route for adaptive concept explanations."""

import json
import re
from dataclasses import dataclass
from threading import Event, Lock
from time import monotonic
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import get_db
from backend.services.adaptation_engine import get_user_level
from backend.services.ai_service import (
    AIServiceError,
    MissingAPIKeyError,
    generate_explanation,
    get_openai_model,
    normalize_language,
    normalize_code_language,
    normalize_response_mode,
)
from backend.services.topic_utils import clean_core_topic, extract_topic, normalize_topic_text


router = APIRouter()


MODE_PATTERNS = (
    ("example", r"\b(real[-\s]?life|real world|examples?|give an example|example of|with example|analogy)\b"),
    ("technical", r"\b(technically|technical|advanced|complexity|operations?|edge cases?|time complexity|space complexity)\b"),
    ("simpler", r"\b(simple|simpler|simply|easy|easier|basic)\b"),
)
SHORT_PATTERNS = (
    r"\bshort\b",
    r"\bbrief\b",
    r"\bquick\b",
    r"\bin short\b",
)
DEPTH_PATTERNS = (
    r"\bin\s+depth\b",
    r"\bin\s+detail\b",
    r"\bin\s+deepth\b",
    r"\bdetail\b",
    r"\bdetailed\b",
    r"\bdeeply\b",
    r"\bfull\s+notes\b",
    r"\bnotes\b",
    r"\bstep\s+by\s+step\b",
    r"\bteach\s+me\b",
)
NOTES_PATTERNS = (
    r"\bfull\s+notes\b",
    r"\bnotes\s+mode\b",
    r"\bclass\s+notes\b",
    r"\bstudy\s+notes\b",
    r"\bnotes\b",
)
INTERVIEW_PATTERNS = (
    r"\binterview\b",
    r"\bviva\b",
    r"\binterview\s+mode\b",
)
CODE_PATTERNS = (
    r"\bwith\s+code\b",
    r"\bcode\b",
    r"\bprogram\b",
    r"\bimplementation\b",
    r"\boutput\b",
)
CODE_LANGUAGE_PATTERNS = (
    ("Python", (r"\bin\s+python\b", r"\busing\s+python\b", r"\bpython\s+(?:code|program|implementation)\b")),
    ("Java", (r"\bin\s+java\b", r"\busing\s+java\b", r"\bjava\s+(?:code|program|implementation)\b")),
    ("C", (r"\bin\s+c\b", r"\busing\s+c\b", r"\bc\s+(?:code|program|implementation)\b")),
)
LANGUAGE_REQUEST_PATTERNS = (
    ("Hinglish", (r"\bin\s+hinglish\b", r"\bhinglish\s+mein\b", r"\bhinglish\b")),
    ("Hindi", (r"\bin\s+hindi\b", r"\bhindi\s+mein\b", r"\bhindi\b")),
    ("English", (r"\bin\s+english\b", r"\benglish\s+please\b", r"\benglish\b")),
)
HINGLISH_PATTERNS = (
    r"\bsamjha(?:o|iye)?\b",
    r"\bbata(?:o|iye)?\b",
    r"\bkaise\b",
    r"\bkya\b",
    r"\bkyun\b",
    r"\bhai\b",
    r"\bhota\b",
    r"\bkar(?:ta|te|na)\b",
    r"\bwale?\b",
)
MULTI_TOPIC_RESPONSE = "Please ask one concept at a time."
UNCLEAR_TOPIC_RESPONSE = "Please mention one clear concept, for example: array, stack, or binary search."
COMMAND_PATTERN = re.compile(
    r"\b(?:"
    r"please\s+)?(?:" 
    r"explain|teach\s+me|tell\s+me\s+about|describe|define|what\s+is|what\s+are|how\s+does|how\s+do|why\s+does|why\s+do|"
    r"give(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|"
    r"show(?:\s+me)?(?:\s+a)?(?:\s+real[-\s]?life)?\s+example(?:\s+(?:of|for))?|"
    r"create(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|"
    r"make(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?|"
    r"generate(?:\s+a)?(?:\s+short)?\s+quiz(?:\s+(?:on|about|for))?"
    r")\b",
    flags=re.IGNORECASE,
)
FILLER_TOPIC_PATTERN = re.compile(
    r"\b("
    r"please|kindly|can|could|would|you|me|about|of|for|on|in|with|a|an|the|what|is|are|how|why|do|does|"
    r"explain|teach|tell|describe|define|give|show|create|make|generate|"
    r"concept|topic|question|answer|explanation|"
    r"simple|simpler|simply|easy|easier|basic|technical|technically|advanced|"
    r"example|examples|real[-\s]?life|way|words|detail|detailed|deep|depth|dive|"
    r"notes|code|program|implementation|output|step|quiz|full|short|brief|quick|"
    r"interview|viva|class|study|mode|algorithm|method|approach|function|structure|data"
    r")\b",
    flags=re.IGNORECASE,
)
GENERIC_TOPICS = {
    "it",
    "this",
    "that",
    "concept",
    "topic",
    "question",
    "example",
    "explanation",
}
REQUEST_CACHE_TTL_SECONDS = 300.0
REQUEST_CACHE_MAX_ITEMS = 256
REQUEST_TRACKER_LOCK = Lock()


@dataclass(frozen=True)
class ChatIntentPreferences:
    """Parsed teaching preferences from a learner message."""

    mode: str = "standard"
    response_depth: str = "normal"
    response_mode: str = "auto"
    code_required: bool = False
    code_language: str = "Python"
    language: str | None = None


@dataclass
class ChatRequestTracker:
    """Track a chat request so duplicate request IDs do not create duplicate responses."""

    event: Event
    created_at: float
    response: schemas.ChatResponse | None = None
    error_status: int | None = None
    error_detail: str | None = None


REQUEST_TRACKERS: dict[str, ChatRequestTracker] = {}


def extract_topic(message: str) -> str:
    """Return only the concept/topic, without prompt or mode wording."""
    print(f"[CHAT ENDPOINT] Extracting topic from original message: '{message}'")
    topics, _ = parse_chat_intent(message=message)
    extracted_topic = topics[0] if len(topics) == 1 else ""
    print(f"[CHAT ENDPOINT] Extracted topic: '{extracted_topic}'")
    return extracted_topic


def parse_chat_intent(
    message: str,
    requested_topic: str | None = None,
) -> tuple[list[str], ChatIntentPreferences]:
    """Extract clean concept topics and adaptive teaching preferences."""
    source_text = message.strip()
    detected_code_language = _detect_code_language(source_text)
    detected_response_mode = _detect_response_mode(source_text)
    preferences = ChatIntentPreferences(
        mode=_detect_mode(source_text),
        response_depth=_detect_response_depth(source_text, detected_response_mode),
        response_mode=detected_response_mode,
        code_required=_detect_code_required(
            source_text,
            code_language_detected=detected_code_language is not None,
            response_mode=detected_response_mode,
        ),
        code_language=normalize_code_language(detected_code_language or "Python"),
        language=_detect_message_language(source_text),
    )

    if requested_topic and requested_topic.strip():
        return _extract_topics(requested_topic), preferences

    return _extract_topics(source_text), preferences


def _detect_mode(message: str) -> str:
    for mode, pattern in MODE_PATTERNS:
        if re.search(pattern, message, flags=re.IGNORECASE):
            return mode

    return "standard"


def _detect_response_depth(message: str, response_mode: str) -> str:
    if response_mode in {"detailed", "notes", "code"}:
        return "detailed"

    if response_mode in {"short", "interview"}:
        return "normal"

    if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in DEPTH_PATTERNS):
        return "detailed"

    return "normal"


def _detect_response_mode(message: str) -> str:
    if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in INTERVIEW_PATTERNS):
        return "interview"

    if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in NOTES_PATTERNS):
        return "notes"

    if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in CODE_PATTERNS):
        return "code"

    if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in SHORT_PATTERNS):
        return "short"

    if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in DEPTH_PATTERNS):
        return "detailed"

    return "auto"


def _detect_code_required(message: str, code_language_detected: bool, response_mode: str) -> bool:
    if response_mode == "code":
        return True

    if code_language_detected:
        return True

    return any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in CODE_PATTERNS)


def _detect_code_language(message: str) -> str | None:
    for language, patterns in CODE_LANGUAGE_PATTERNS:
        if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in patterns):
            return language

    return None


def _detect_message_language(message: str) -> str | None:
    for language, patterns in LANGUAGE_REQUEST_PATTERNS:
        if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in patterns):
            return language

    if re.search(r"[\u0900-\u097F]", message):
        return "Hindi"

    if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in HINGLISH_PATTERNS):
        return "Hinglish"

    if re.search(r"[A-Za-z]", message):
        return "English"

    return None


def _extract_topics(text: str) -> list[str]:
    """Split repeated prompts and return clean concept names only."""
    normalized_text = text.strip()
    if not normalized_text:
        return []

    command_split_text = COMMAND_PATTERN.sub("|", normalized_text)
    command_segments = [segment.strip() for segment in command_split_text.split("|") if segment.strip()]
    segments = command_segments if command_segments else [normalized_text]

    topics: list[str] = []
    for segment in segments:
        for candidate in _split_possible_topic_list(segment):
            cleaned_topic = _clean_topic(candidate)
            if cleaned_topic and cleaned_topic not in topics:
                topics.append(cleaned_topic)

    return topics


def _split_possible_topic_list(text: str) -> list[str]:
    """Catch obvious multi-topic prompts such as 'stack and recursion'."""
    if re.search(r"\s(?:and|or)\s|[,;/]", text, flags=re.IGNORECASE):
        return [part.strip() for part in re.split(r"\s+(?:and|or)\s+|[,;/]", text, flags=re.IGNORECASE)]

    return [text]


def _clean_topic(value: str) -> str:
    """Remove instruction, mode, and filler words from a topic candidate."""
    return clean_core_topic(value)


def _resolve_response_depth(payload_depth: str, detected_depth: str, response_mode: str) -> str:
    if payload_depth != "normal":
        return payload_depth

    if response_mode in {"detailed", "notes", "code"}:
        return "detailed"

    if response_mode in {"short", "interview"}:
        return "normal"

    return detected_depth


def _resolve_code_required(
    payload_code_required: bool | None,
    detected_code_required: bool,
    payload_code_language: str | None,
    response_mode: str,
) -> bool:
    if response_mode == "code":
        return True

    if payload_code_language:
        return True

    if payload_code_required is None:
        return detected_code_required

    return payload_code_required


def _get_request_tracker(request_id: str) -> tuple[ChatRequestTracker, bool]:
    now = monotonic()
    with REQUEST_TRACKER_LOCK:
        expired_ids = [
            cache_key
            for cache_key, tracker in REQUEST_TRACKERS.items()
            if tracker.event.is_set() and now - tracker.created_at > REQUEST_CACHE_TTL_SECONDS
        ]
        for cache_key in expired_ids:
            REQUEST_TRACKERS.pop(cache_key, None)

        tracker = REQUEST_TRACKERS.get(request_id)
        if tracker is not None:
            return tracker, False

        if len(REQUEST_TRACKERS) >= REQUEST_CACHE_MAX_ITEMS:
            oldest_request_id = min(
                REQUEST_TRACKERS,
                key=lambda cache_key: REQUEST_TRACKERS[cache_key].created_at,
            )
            REQUEST_TRACKERS.pop(oldest_request_id, None)

        tracker = ChatRequestTracker(event=Event(), created_at=now)
        REQUEST_TRACKERS[request_id] = tracker
        return tracker, True


def _complete_request_tracker(
    request_id: str,
    *,
    response: schemas.ChatResponse | None = None,
    error_status: int | None = None,
    error_detail: str | None = None,
) -> None:
    with REQUEST_TRACKER_LOCK:
        tracker = REQUEST_TRACKERS.get(request_id)
        if tracker is None:
            return

        tracker.response = response
        tracker.error_status = error_status
        tracker.error_detail = error_detail
        tracker.event.set()


def _wait_for_tracked_response(request_id: str, tracker: ChatRequestTracker) -> schemas.ChatResponse:
    if not tracker.event.wait(timeout=30):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This request is already being processed. Please wait for the first response.",
        )

    if tracker.response is not None:
        return tracker.response

    if tracker.error_status is not None:
        raise HTTPException(status_code=tracker.error_status, detail=tracker.error_detail or "Request failed.")

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This request is already being processed. Please wait for the first response.",
    )


@router.post("/chat", response_model=schemas.ChatResponse, status_code=status.HTTP_200_OK)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    """Receive a user query and return an adaptive explanation."""
    user_id = payload.user_id.strip()
    message = payload.message.strip()
    request_id = (payload.request_id or "").strip() or f"chat_{uuid4().hex}"
    model_name = get_openai_model()

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id cannot be empty.")

    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message cannot be empty.")

    tracker, should_process = _get_request_tracker(request_id)
    if not should_process:
        return _wait_for_tracked_response(request_id, tracker)

    resolved_language = normalize_language(None)
    try:
        print(
            "[CHAT REQUEST] "
            f"request_id={request_id}, user_id={user_id}, model={model_name}, "
            f"message_preview={message[:120]!r}"
        )

        try:
            user = db.query(models.User).filter(models.User.user_id == user_id).first()
            if user is None:
                user = models.User(user_id=user_id)
                db.add(user)
                db.commit()
                db.refresh(user)
        except Exception as exc:
            db.rollback()
            print(
                "[CHAT DB ERROR] "
                f"request_id={request_id}, stage=user_lookup, error_type={type(exc).__name__}"
            )
            raise

        resolved_language = normalize_language(user.preferred_language)
        level = get_user_level(db=db, user_id=user.user_id)
        
        # Use clean keyword-based topic extraction
        detected_topic = extract_topic(message)
        
        # If user provided an explicit topic, use that instead
        if payload.topic:
            detected_topic = extract_topic(payload.topic)
        
        # Parse intent for mode, depth, response preferences (not for topic)
        _, intent = parse_chat_intent(
            message=message,
            requested_topic=payload.topic,
        )
        
        mode = intent.mode if payload.mode == "standard" else payload.mode
        response_mode = normalize_response_mode(
            intent.response_mode if payload.response_mode == "auto" else payload.response_mode
        )
        response_depth = _resolve_response_depth(
            payload_depth=payload.response_depth,
            detected_depth=intent.response_depth,
            response_mode=response_mode,
        )
        code_language = normalize_code_language(payload.code_language or intent.code_language)
        code_required = _resolve_code_required(
            payload_code_required=payload.code_required,
            detected_code_required=intent.code_required,
            payload_code_language=payload.code_language,
            response_mode=response_mode,
        )

        # Check if topic is unclear (empty string)
        if not detected_topic:
            response = schemas.ChatResponse(
                response=UNCLEAR_TOPIC_RESPONSE,
                explanation=UNCLEAR_TOPIC_RESPONSE,
                level=level,
                topic="",
                language=resolved_language,
                mode=mode,
                response_depth=response_depth,
                response_mode=response_mode,
                request_id=request_id,
            )
            _complete_request_tracker(request_id, response=response)
            return response

        topic = detected_topic
        language = normalize_language(user.preferred_language)
        resolved_language = language
        weak_areas = _get_topic_weak_areas(db=db, user_id=user.user_id, topic=topic)
        print(
            "[CHAT RESOLVED] "
            f"request_id={request_id}, topic={topic}, level={level}, "
            f"mode={mode}, response_mode={response_mode}, language={language}"
        )

        explanation = None
        error_type = None
        try:
            explanation = generate_explanation(
                topic=topic,
                user_message=message,
                level=level,
                language=language,
                mode=mode,
                response_depth=response_depth,
                response_mode=response_mode,
                code_required=code_required,
                code_language=code_language,
                weak_areas=weak_areas,
            )
            print(f"[CHAT PROVIDER OK] request_id={request_id}, topic={topic}, model={model_name}")
        except MissingAPIKeyError as exc:
            print(
                "[CHAT PROVIDER ERROR] "
                f"request_id={request_id}, model={model_name}, error_type={type(exc).__name__}"
            )
            explanation = "AI provider failed. Please check backend logs."
            error_type = "provider_error"
        except AIServiceError as exc:
            cause = exc.__cause__
            safe_error_type = type(cause).__name__ if cause is not None else type(exc).__name__
            print(
                "[CHAT PROVIDER ERROR] "
                f"request_id={request_id}, model={model_name}, error_type={safe_error_type}"
            )
            explanation = "AI provider failed. Please check backend logs."
            error_type = "provider_error"
        except Exception as exc:
            print(
                "[CHAT PROVIDER ERROR] "
                f"request_id={request_id}, model={model_name}, error_type={type(exc).__name__}"
            )
            explanation = "AI provider failed. Please check backend logs."
            error_type = "provider_error"

        if not explanation:
            print(f"[CHAT PROVIDER ERROR] request_id={request_id}, model={model_name}, error_type=EmptyResponse")
            explanation = "AI provider failed. Please check backend logs."
            error_type = "provider_error"

        try:
            db.add(
                models.ChatHistory(
                    user_id=user.user_id,
                    topic=normalize_topic_text(topic, fallback="topic").strip().lower(),
                    user_message=message,
                    ai_response=explanation,
                    learner_level=level,
                    language=language,
                )
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            print(
                "[CHAT DB ERROR] "
                f"request_id={request_id}, stage=history_save, error_type={type(exc).__name__}"
            )

        response = schemas.ChatResponse(
            response=explanation,
            explanation=explanation,
            level=level,
            topic=topic,
            language=language,
            mode=mode,
            response_depth=response_depth,
            response_mode=response_mode,
            request_id=request_id,
            error_type=error_type,
        )
        _complete_request_tracker(request_id, response=response)
        return response
    except HTTPException as exc:
        print(f"[HTTP ERROR] {exc.status_code}: {exc.detail}")
        _complete_request_tracker(
            request_id,
            error_status=exc.status_code,
            error_detail=str(exc.detail),
        )
        raise
    except Exception as exc:
        db.rollback()
        print(f"[CRITICAL ERROR] request_id={request_id}, error_type={type(exc).__name__}")
        fallback_response = schemas.ChatResponse(
            response="Request failed. Please check backend logs.",
            explanation="Request failed. Please check backend logs.",
            level="beginner",
            topic=normalize_topic_text(payload.topic or "general", fallback="general"),
            language=resolved_language,
            mode="standard",
            response_depth="normal",
            response_mode="auto",
            request_id=request_id,
            error_type="server_error",
        )
        _complete_request_tracker(request_id, response=fallback_response)
        return fallback_response


def _get_topic_weak_areas(db: Session, user_id: str, topic: str) -> list[str]:
    progress = (
        db.query(models.ConceptProgress)
        .filter(
            models.ConceptProgress.user_id == user_id,
            models.ConceptProgress.topic == topic.strip().lower(),
        )
        .first()
    )
    if progress is None or not progress.weak_points:
        return []

    try:
        weak_points = json.loads(progress.weak_points)
    except json.JSONDecodeError:
        weak_points = [point.strip() for point in progress.weak_points.split(",")]

    if not isinstance(weak_points, list):
        return []

    return [str(point).strip() for point in weak_points if str(point).strip()]
