"""Focused smoke tests for topic extraction and prompt relevance."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.routes.chat import parse_chat_intent
from backend.services.ai_service import build_prompt


TEST_CASES = (
    ("explain CNN model in machine learning", "CNN / Convolutional Neural Network"),
    ("explain linked list in depth", "Linked List"),
    ("explain binary search technically", "Binary Search"),
    ("explain array with code and output", "Array"),
    ("teach recursion simply", "Recursion"),
)


def main() -> None:
    for message, expected_topic in TEST_CASES:
        topics, _ = parse_chat_intent(message)
        assert topics == [expected_topic], f"{message!r} -> {topics!r}, expected {[expected_topic]!r}"

    prompt = build_prompt(
        topic="CNN / Convolutional Neural Network",
        user_message="explain CNN model in machine learning",
        level="beginner",
        language="English",
        mode="standard",
        response_depth="normal",
        response_mode="auto",
        code_required=False,
        code_language="Python",
        weak_areas=None,
    )
    assert "User question: explain CNN model in machine learning" in prompt
    assert "Detected topic: CNN / Convolutional Neural Network" in prompt
    print("topic extraction tests passed")


if __name__ == "__main__":
    main()
