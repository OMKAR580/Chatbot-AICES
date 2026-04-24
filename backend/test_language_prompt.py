"""Focused prompt checks for explanation language instructions."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.ai_service import build_prompt


def _assert_language_prompt(language: str, expected_instruction: str) -> None:
    prompt = build_prompt(
        topic="Array",
        user_message="Explain array",
        level="beginner",
        language=language,
    )

    assert "You are a helpful technical tutor." in prompt
    assert "Language instruction:" in prompt
    assert expected_instruction in prompt
    assert "Do not switch language." in prompt


def main() -> None:
    _assert_language_prompt("english", "Answer in clear English.")
    _assert_language_prompt("hindi", "Answer in Hindi.")
    _assert_language_prompt(
        "hinglish",
        "Answer in Hinglish (Hindi + English mix using Roman script, not pure Hindi script).",
    )
    print("language prompt tests passed")


if __name__ == "__main__":
    main()
