"""AI integration service for adaptive explanations and quizzes."""

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
SUPPORTED_LANGUAGES = {"English", "Hindi", "Hinglish"}
SUPPORTED_MODES = {"standard", "simpler", "example", "technical", "quiz"}
SUPPORTED_RESPONSE_DEPTHS = {"normal", "detailed"}
SUPPORTED_RESPONSE_MODES = {"auto", "short", "detailed", "notes", "code", "interview"}
SUPPORTED_CODE_LANGUAGES = {"Python", "Java", "C"}
SECTION_HEADING_ALIASES = {
    "Definition": ("definition",),
    "In-depth Explanation": ("in-depth explanation", "detailed explanation", "explanation"),
    "Technical View": ("technical view", "deeper technical view", "technical explanation"),
    "Real-life Example": ("real-life example", "real life example", "real-life intuition", "intuition", "example"),
    "Code Example": ("code example", "python example", "java example", "c example"),
    "Output": ("output", "expected output"),
    "Dry Run": ("dry run", "step-by-step dry run", "walkthrough", "step-by-step explanation"),
    "Interview Points": ("interview points", "important points", "key points"),
    "Common Mistakes": ("common mistakes", "mistakes", "edge cases"),
    "Summary": ("summary", "final summary", "short summary", "quick wrap-up", "takeaway"),
}


class AIServiceError(Exception):
    """Raised when the AI provider cannot generate a response."""


class MissingAPIKeyError(AIServiceError):
    """Raised when the OpenAI API key is missing."""


def build_prompt(
    topic: str,
    level: str,
    language: str,
    mode: str = "standard",
    response_depth: str = "normal",
    response_mode: str = "auto",
    code_required: bool = False,
    code_language: str = "Python",
    weak_areas: list[str] | None = None,
) -> str:
    """Build a strict tutor prompt that follows the AICES teaching contract."""
    normalized_language = normalize_language(language)
    normalized_mode = mode if mode in SUPPORTED_MODES else "standard"
    normalized_response_mode = normalize_response_mode(response_mode)
    normalized_response_depth = _resolve_response_depth(
        response_depth=response_depth,
        response_mode=normalized_response_mode,
    )
    normalized_code_language = normalize_code_language(code_language)
    weak_area_text = ", ".join(weak_areas or [])
    effective_response_mode = _get_effective_response_mode(
        response_mode=normalized_response_mode,
        response_depth=normalized_response_depth,
        code_required=code_required,
    )
    prompt_mode_label = _get_prompt_mode_label(effective_response_mode)

    return (
        "You are AICES, an AI tutor that explains concepts like ChatGPT with high-quality structured notes.\n\n"
        "Your goal is:\n"
        "* Always give COMPLETE, structured, high-quality explanations\n"
        "* Never give vague or template-like responses\n"
        "* Always include real content: definition, explanation, examples, and code when needed\n\n"
        "INPUT VARIABLES\n"
        f"* User Query Topic: {topic}\n"
        f"* Learner Level: {level}\n"
        f"* Mode: {prompt_mode_label}\n"
        f"* Language: {normalized_language}\n"
        f"* Preferred code language: {normalized_code_language}\n"
        f"* Weak areas to reinforce if relevant: {weak_area_text or 'none'}\n\n"
        "CORE RULES (VERY IMPORTANT)\n"
        "1. NEVER use placeholder text like:\n"
        "* `concept best understood by...`\n"
        "* `replace with example...`\n"
        "* `sample code...`\n"
        "2. ALWAYS give real explanation, real examples, and real code when applicable.\n"
        f"3. Stay on the EXACT topic asked: `{topic}`. Do not generalize, rename it, or drift away from it.\n"
        "4. The output must feel like ChatGPT notes: clean, structured, useful, and readable.\n"
        "5. Do NOT repeat the user's question back.\n\n"
        "LEVEL ADAPTATION\n"
        f"{_get_level_adaptation_contract(level)}\n\n"
        "MODE ADAPTATION\n"
        f"{_get_mode_output_contract(effective_response_mode, normalized_code_language)}\n\n"
        "LANGUAGE ADAPTATION\n"
        f"{_get_language_output_contract(normalized_language)}\n\n"
        "OUTPUT STYLE\n"
        "* Use headings and clear spacing for readability\n"
        "* Use bullet points where they help study clarity\n"
        "* Avoid long, boring paragraphs\n"
        "* Keep the answer structured and content-rich, not robotic\n"
        f"* {normalized_mode.capitalize()} mode hint: {_get_mode_guidance(normalized_mode)}\n\n"
        "FINAL CHECK BEFORE OUTPUT\n"
        "Before finalizing the answer, silently verify:\n"
        "✔ No placeholder text\n"
        "✔ Proper structure\n"
        "✔ Real explanation\n"
        "✔ Learner level applied correctly\n"
        "✔ Mode applied correctly\n"
        "If anything is missing, regenerate the response before answering."
    )


def _get_code_guidance(
    code_required: bool,
    code_language: str,
    response_depth: str,
    mode: str,
    response_mode: str,
) -> str:
    if code_required or response_mode == "code":
        return (
            f"Code is required. Use {code_language} for the example, include the exact expected output, "
            "and explain the code step by step with a dry run."
        )

    if response_depth == "detailed":
        return (
            f"If code will genuinely make the concept easier to learn, include one clean example in {code_language} "
            "with output and a walkthrough. Do not force code for purely theoretical concepts."
        )

    if mode == "technical":
        return f"If implementation details would help, you may include one concise {code_language} example."

    return "Do not force code unless it clearly improves the explanation."


def _get_effective_response_mode(
    response_mode: str,
    response_depth: str,
    code_required: bool,
) -> str:
    normalized_response_mode = normalize_response_mode(response_mode)
    if normalized_response_mode == "auto":
        if code_required:
            return "code"
        if response_depth == "normal":
            return "detailed"
        return "detailed"

    return normalized_response_mode


def _get_prompt_mode_label(response_mode: str) -> str:
    return "with_code" if response_mode == "code" else response_mode


def _get_level_adaptation_contract(level: str) -> str:
    normalized_level = (level or "beginner").strip().lower()
    if normalized_level == "advanced":
        return (
            "* Use technical language.\n"
            "* Include deeper explanation.\n"
            "* Add complexity analysis.\n"
            "* Mention edge cases.\n"
            "* Add internal working details."
        )

    return (
        "* Use very simple language.\n"
        "* Explain like you are teaching a friend.\n"
        "* Use short sentences.\n"
        "* Use analogies and real-life examples.\n"
        "* Add one small practical example.\n"
        "* Explain step by step.\n"
        "* Avoid heavy jargon.\n"
        "* Avoid formal textbook tone.\n"
        "* Focus on clarity over depth."
    )


def _get_mode_output_contract(response_mode: str, code_language: str) -> str:
    if response_mode == "short":
        return (
            "Use this format:\n"
            "* `## Topic Name`\n"
            "* `**Definition:**`\n"
            "* `**Key points:**` with 2 to 3 useful bullets only."
        )

    if response_mode == "notes":
        return (
            "Use this STRICT format:\n"
            "* `## Topic Name`\n"
            "* `**Definition:**`\n"
            "* `**In-depth explanation:**`\n"
            "* `**Deeper technical view:**`\n"
            "* `**Operations and complexity:**`\n"
            "* `**Real-life intuition:**`\n"
            "* `**Why we use it:**`\n"
            "* `**Important points / interview points:**`\n"
            "* `**Common mistakes / edge cases:**`\n"
            "* `**Key points to remember:**`\n"
            "* `**Final takeaway:**`"
        )

    if response_mode == "code":
        return (
            "Use the NOTES format and ADD these exact sections:\n"
            "* `**Code example:**` with real working code in "
            f"{code_language}\n"
            "* `**Expected output:**` with real output\n"
            "* `**Step-by-step dry run:**` with a numbered explanation"
        )

    if response_mode == "interview":
        return (
            "Focus on:\n"
            "* crisp definition\n"
            "* complexity\n"
            "* edge cases and common traps\n"
            "* 2 to 3 interview questions\n"
            "* a short interview-ready takeaway"
        )

    return (
        "Give a full explanation with real content.\n"
        "* Definition\n"
        "* In-depth explanation\n"
        "* Deeper technical view\n"
        "* Real-life example or intuition\n"
        "* Important points\n"
        "* Common mistakes or edge cases\n"
        "* Final takeaway\n"
        "Code is optional unless it is truly helpful."
    )


def _get_language_output_contract(language: str) -> str:
    normalized_language = normalize_language(language)
    if normalized_language == "Hinglish":
        return (
            "* Mix Hindi and English naturally.\n"
            "* Keep technical terms in English.\n"
            "* Use a friendly teaching tone, not forced slang.\n"
            "* Example tone: `Array ek linear data structure hai jisme har value ek fixed jagah par hoti hai.`"
        )

    if normalized_language == "Hindi":
        return (
            "* Explain in simple Hindi.\n"
            "* Keep technical terms in English only where needed for clarity."
        )

    return "* Use clear professional English."


def _get_level_guidance(level: str) -> str:
    level_guidance = {
        "beginner": "Use simple words, small steps, and beginner-friendly examples.",
        "intermediate": "Balance intuition with correct terminology and practical reasoning.",
        "advanced": "Include deeper technical detail, complexity, tradeoffs, and implementation nuance.",
    }
    return level_guidance.get(level, level_guidance["beginner"])


def _get_mode_guidance(mode: str) -> str:
    mode_guidance = {
        "technical": "Include operations, complexity, tradeoffs, and implementation details where meaningful.",
        "simpler": "Keep the explanation especially easy to follow and lean on analogies.",
        "example": "Use rich real-life and practical examples to anchor the explanation.",
        "standard": "Balance explanation, intuition, and one helpful example.",
        "quiz": "Focus on concept clarity rather than quiz generation.",
    }
    return mode_guidance.get(mode, mode_guidance["standard"])


def _get_response_mode_guidance(response_mode: str) -> str:
    response_mode_guidance = {
        "auto": "Choose the most helpful structure naturally without mentioning format decisions.",
        "short": "Keep it concise and high-signal, with only the most useful explanation and one small example.",
        "detailed": "Teach like full study notes with depth, clarity, and strong explanation flow.",
        "notes": "Make the answer especially easy to revise from, using tidy mini-sections where helpful.",
        "code": "Make code central to the explanation and include code, exact output, and a dry run.",
        "interview": "Keep it crisp and interview-oriented: definition, working idea, complexity, pitfalls, and recall points.",
    }
    return response_mode_guidance.get(response_mode, response_mode_guidance["auto"])


def _get_heading_instruction(response_mode: str, code_required: bool) -> str:
    if response_mode == "short":
        return (
            "Use proper markdown headings with blank lines between sections. "
            "At minimum, use `## Definition`, `## In-depth Explanation`, `## Real-life Example`, and `## Summary`. "
            "If you include code, also use `## Code Example`, `## Output`, and `## Dry Run`. "
            "Do not write inline headings like `Definition An array is...`."
        )

    if response_mode == "interview":
        return (
            "Use proper markdown headings with blank lines between sections. "
            "Use these exact headings when relevant: `## Definition`, `## Technical View`, `## Interview Points`, "
            "`## Common Mistakes`, and `## Summary`. "
            "If code is shown, also use `## Code Example`, `## Output`, and `## Dry Run`."
        )

    code_clause = (
        "Because code is required, include all of these exact headings in order: "
        "`## Definition`, `## In-depth Explanation`, `## Technical View`, `## Real-life Example`, "
        "`## Code Example`, `## Output`, `## Dry Run`, `## Interview Points`, `## Common Mistakes`, `## Summary`."
        if code_required or response_mode == "code"
        else "Use these exact headings in order whenever relevant: "
        "`## Definition`, `## In-depth Explanation`, `## Technical View`, `## Real-life Example`, "
        "`## Interview Points`, `## Common Mistakes`, `## Summary`. "
        "If you include code, also add `## Code Example`, `## Output`, and `## Dry Run`."
    )

    return (
        "Use proper markdown headings with blank lines between sections. "
        f"{code_clause} Do not compress a heading and its content onto one line."
    )


def _get_language_guidance(language: str) -> str:
    language_guidance = {
        "English": "Write in natural English.",
        "Hindi": "Write in natural Hindi using Devanagari, while keeping common programming terms in English when that is clearer.",
        "Hinglish": "Write in natural Hinglish using simple Roman-script Hindi mixed with common English programming terms. Do not force slang.",
    }
    return language_guidance.get(language, language_guidance["English"])


def build_quiz_prompt(topic: str, level: str, language: str, count: int) -> str:
    """Build a structured quiz generation prompt."""
    normalized_language = normalize_language(language)
    difficulty_guidance = {
        "beginner": "simple conceptual MCQs with everyday wording",
        "intermediate": "logic-based MCQs that test reasoning and flow",
        "advanced": "technical MCQs covering edge cases, complexity, and implementation details",
    }
    guidance = difficulty_guidance.get(level, difficulty_guidance["beginner"])

    return (
        f"You are an AI tutor. Generate exactly {count} multiple-choice questions on {topic}.\n"
        f"Use {normalized_language}. If Hindi, use natural Devanagari Hindi with English programming terms where needed.\n"
        f"Match difficulty to a {level} learner: {guidance}.\n"
        "Rules:\n"
        "* Each question must have 4 options.\n"
        "* Cover different subtopics or angles of the concept.\n"
        "* Avoid repetition.\n"
        "Return valid JSON only, with this exact shape:\n"
        "{\n"
        f'  "topic": "{topic}",\n'
        '  "questions": [\n'
        "    {\n"
        '      "question": "question text",\n'
        '      "options": ["option A text", "option B text", "option C text", "option D text"],\n'
        '      "answer": "A"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Do not wrap the JSON in markdown."
    )


def build_feedback_prompt(
    topic: str,
    score: int,
    weak_area: str,
    level: str,
    language: str = "Hinglish",
) -> str:
    """Build a structured feedback prompt after quiz evaluation."""
    normalized_language = normalize_language(language)
    return (
        f"A learner completed a quiz about {topic}.\n"
        f"Score: {score}%.\n"
        f"New learner level: {level}.\n"
        f"Weak area: {weak_area}.\n"
        f"Write in {normalized_language}. Keep it one short, encouraging feedback message with the next study focus.\n"
        'Return valid JSON only: {"feedback": "message"}'
    )


def generate_explanation(
    topic: str,
    level: str,
    language: str,
    mode: str = "standard",
    response_depth: str = "normal",
    response_mode: str = "auto",
    code_required: bool = False,
    code_language: str = "Python",
    weak_areas: list[str] | None = None,
) -> str:
    """Generate an adaptive explanation using the OpenAI Responses API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        if _requires_openai():
            raise MissingAPIKeyError("OPENAI_API_KEY is missing. Set it before calling /chat.")

        return _fallback_explanation(
            topic=topic,
            level=level,
            language=language,
            mode=mode,
            response_depth=response_depth,
            response_mode=response_mode,
            code_required=code_required,
            code_language=code_language,
            weak_areas=weak_areas,
        )

    client = OpenAI(api_key=api_key)
    prompt = build_prompt(
        topic=topic,
        level=level,
        language=language,
        mode=mode,
        response_depth=response_depth,
        response_mode=response_mode,
        code_required=code_required,
        code_language=code_language,
        weak_areas=weak_areas,
    )

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=prompt,
        )
    except Exception as exc:
        raise AIServiceError("Failed to generate explanation from the AI provider.") from exc

    output_text = (response.output_text or "").strip()
    if not output_text:
        raise AIServiceError("AI provider returned an empty explanation.")

    return _normalize_explanation_markdown(output_text)


def _normalize_explanation_markdown(output_text: str) -> str:
    """Clean heading spacing and normalize common section labels into markdown headings."""
    cleaned_text = output_text.replace("\r\n", "\n").strip()
    if not cleaned_text:
        return cleaned_text

    processed_lines: list[str] = []
    for raw_line in cleaned_text.split("\n"):
        stripped_line = raw_line.strip()
        replaced = False
        if stripped_line:
            for canonical_heading, aliases in SECTION_HEADING_ALIASES.items():
                alias_pattern = "|".join(re.escape(alias) for alias in aliases)
                match = re.match(
                    rf"^(?:#+\s*)?(?:{alias_pattern})\s*:?\s*(.*)$",
                    stripped_line,
                    flags=re.IGNORECASE,
                )
                if match:
                    processed_lines.append(f"## {canonical_heading}")
                    inline_content = match.group(1).strip()
                    if inline_content:
                        processed_lines.append("")
                        processed_lines.append(inline_content)
                    replaced = True
                    break

        if not replaced:
            processed_lines.append(raw_line.rstrip())

    normalized_text = "\n".join(processed_lines)
    normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text)
    normalized_text = re.sub(r"([^\n])\n(##\s+)", r"\1\n\n\2", normalized_text)
    normalized_text = re.sub(r"(?m)^(##\s+[^\n]+)\n(?!\n)", r"\1\n\n", normalized_text)
    return normalized_text.strip()


def generate_quiz(topic: str, level: str, language: str, count: int = 5) -> dict[str, Any]:
    """Generate and normalize a multiple-choice quiz."""
    question_count = max(3, min(15, int(count or 5)))
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        if _requires_openai():
            raise MissingAPIKeyError("OPENAI_API_KEY is missing. Set it before calling /quiz.")

        return _fallback_quiz(topic=topic, level=level, count=question_count)

    client = OpenAI(api_key=api_key)
    prompt = build_quiz_prompt(topic=topic, level=level, language=language, count=question_count)

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=prompt,
        )
    except Exception as exc:
        raise AIServiceError("Failed to generate quiz from the AI provider.") from exc

    output_text = (response.output_text or "").strip()
    if not output_text:
        return _fallback_quiz(topic=topic, level=level, count=question_count)

    try:
        raw_payload = _parse_json_value(output_text)
        return _normalize_quiz_payload(raw_payload, topic=topic, level=level, count=question_count)
    except ValueError:
        return _fallback_quiz(topic=topic, level=level, count=question_count)


def generate_feedback(
    topic: str,
    score: int,
    weak_area: str,
    level: str,
    language: str = "Hinglish",
) -> str:
    """Generate concise adaptive feedback, with a deterministic fallback."""
    fallback_feedback = _fallback_feedback(
        topic=topic,
        score=score,
        weak_area=weak_area,
        level=level,
        language=language,
    )
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback_feedback

    client = OpenAI(api_key=api_key)
    prompt = build_feedback_prompt(
        topic=topic,
        score=score,
        weak_area=weak_area,
        level=level,
        language=language,
    )

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=prompt,
        )
    except Exception:
        return fallback_feedback

    output_text = (response.output_text or "").strip()
    if not output_text:
        return fallback_feedback

    try:
        raw_payload = _parse_json_payload(output_text)
    except ValueError:
        return output_text

    feedback = str(raw_payload.get("feedback", "")).strip()
    return feedback or fallback_feedback


def _parse_json_payload(output_text: str) -> dict[str, Any]:
    payload = _parse_json_value(output_text)
    if not isinstance(payload, dict):
        raise ValueError("AI response JSON must be an object.")

    return payload


def _parse_json_value(output_text: str) -> Any:
    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError:
        start_index = min(
            [index for index in (output_text.find("{"), output_text.find("[")) if index != -1],
            default=-1,
        )
        end_index = max(output_text.rfind("}"), output_text.rfind("]"))
        if start_index == -1 or end_index == -1 or end_index <= start_index:
            raise ValueError("AI response did not contain JSON.") from None
        try:
            payload = json.loads(output_text[start_index : end_index + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("AI response contained malformed JSON.") from exc

    return payload


def normalize_language(language: str | None) -> str:
    """Normalize user-facing language choices to supported labels."""
    cleaned_language = (language or "Hinglish").strip().lower()
    language_map = {
        "english": "English",
        "hindi": "Hindi",
        "hinglish": "Hinglish",
    }
    return language_map.get(cleaned_language, "Hinglish")


def normalize_response_mode(response_mode: str | None) -> str:
    """Normalize response mode to the supported labels."""
    cleaned_response_mode = (response_mode or "auto").strip().lower()
    response_mode_map = {
        "auto": "auto",
        "short": "short",
        "detailed": "detailed",
        "notes": "notes",
        "code": "code",
        "with_code": "code",
        "with code": "code",
        "interview": "interview",
    }
    normalized_response_mode = response_mode_map.get(cleaned_response_mode, "auto")
    return normalized_response_mode if normalized_response_mode in SUPPORTED_RESPONSE_MODES else "auto"


def normalize_code_language(code_language: str | None) -> str:
    """Normalize requested code language to the supported display label."""
    cleaned_code_language = (code_language or "Python").strip().lower()
    code_language_map = {
        "python": "Python",
        "java": "Java",
        "c": "C",
    }
    normalized_code_language = code_language_map.get(cleaned_code_language, "Python")
    return normalized_code_language if normalized_code_language in SUPPORTED_CODE_LANGUAGES else "Python"


def _resolve_response_depth(response_depth: str, response_mode: str) -> str:
    normalized_response_mode = normalize_response_mode(response_mode)
    if normalized_response_mode in {"detailed", "notes", "code"}:
        return "detailed"

    if normalized_response_mode in {"short", "interview"}:
        return "normal"

    return response_depth if response_depth in SUPPORTED_RESPONSE_DEPTHS else "normal"


def _requires_openai() -> bool:
    return os.getenv("AICES_REQUIRE_OPENAI", "false").strip().lower() in {"1", "true", "yes"}


def _normalize_quiz_payload(raw_payload: Any, topic: str, level: str, count: int) -> dict[str, Any]:
    if isinstance(raw_payload, list):
        raw_questions = raw_payload
        payload_topic = topic
    elif isinstance(raw_payload, dict):
        raw_questions = raw_payload.get("questions", [])
        payload_topic = str(raw_payload.get("topic") or topic).strip() or topic
    else:
        raise ValueError("Quiz payload must be a JSON object or list.")

    if not isinstance(raw_questions, list):
        raise ValueError("Quiz questions must be a list.")

    questions = []
    for raw_question in raw_questions:
        if not isinstance(raw_question, dict):
            continue

        question_text = str(raw_question.get("question", "")).strip()
        raw_options = raw_question.get("options", [])
        correct_answer = str(raw_question.get("correct_answer") or raw_question.get("answer") or "").strip()

        if not question_text or not isinstance(raw_options, list):
            continue

        options = [str(option).strip() for option in raw_options if str(option).strip()]
        options = options[:4]
        corrected_answer = _align_correct_answer(options=options, correct_answer=correct_answer)

        if len(options) < 2 or not corrected_answer:
            continue

        questions.append(
            {
                "question": question_text,
                "options": options,
                "correct_answer": corrected_answer,
            }
        )

    if len(questions) < count:
        return _fallback_quiz(topic=topic, level=level, count=count)

    return {
        "topic": payload_topic,
        "questions": questions[:count],
    }


def _align_correct_answer(options: list[str], correct_answer: str) -> str:
    if correct_answer in options:
        return correct_answer

    normalized_correct_answer = correct_answer.strip().lower()
    option_labels = {"a": 0, "b": 1, "c": 2, "d": 3}
    if normalized_correct_answer in option_labels:
        option_index = option_labels[normalized_correct_answer]
        if option_index < len(options):
            return options[option_index]

    for option in options:
        if option.strip().lower() == normalized_correct_answer:
            return option

    return ""


def _fallback_quiz(topic: str, level: str, count: int = 5) -> dict[str, Any]:
    cleaned_topic = topic.strip() or "the topic"
    question_bank = _get_fallback_quiz_bank(cleaned_topic, level)
    question_count = max(3, min(15, int(count or 5)))
    return {"topic": cleaned_topic, "questions": question_bank[:question_count]}


def _get_fallback_quiz_bank(cleaned_topic: str, level: str) -> list[dict[str, Any]]:
    if level == "advanced":
        return [
            {
                "question": f"Which angle is most important when stress-testing {cleaned_topic}?",
                "options": [
                    "Boundary inputs and failure paths",
                    "Only the happy path",
                    "UI color choices",
                    "Random memorized facts",
                ],
                "correct_answer": "Boundary inputs and failure paths",
            },
            {
                "question": f"What should an advanced explanation of {cleaned_topic} usually include?",
                "options": [
                    "Complexity, tradeoffs, and edge cases",
                    "Only a one-line definition",
                    "No examples",
                    "Only keywords",
                ],
                "correct_answer": "Complexity, tradeoffs, and edge cases",
            },
            {
                "question": f"Why do implementation details matter in {cleaned_topic}?",
                "options": [
                    "They affect correctness and performance",
                    "They never change behavior",
                    "They remove the need for testing",
                    "They make the concept unrelated to code",
                ],
                "correct_answer": "They affect correctness and performance",
            },
            {
                "question": f"When comparing two approaches for {cleaned_topic}, what should you examine first?",
                "options": [
                    "Correctness assumptions and tradeoffs",
                    "Which one has more comments",
                    "Which one looks shorter",
                    "Which one uses more keywords",
                ],
                "correct_answer": "Correctness assumptions and tradeoffs",
            },
            {
                "question": f"What is the value of complexity analysis in {cleaned_topic}?",
                "options": [
                    "It shows how the solution scales with input size",
                    "It guarantees bug-free code",
                    "It replaces dry runs",
                    "It matters only for very small inputs",
                ],
                "correct_answer": "It shows how the solution scales with input size",
            },
            {
                "question": f"What should you verify before optimizing an implementation of {cleaned_topic}?",
                "options": [
                    "That the current version is already correct",
                    "That the variable names are long",
                    "That the output is colorful",
                    "That comments are removed",
                ],
                "correct_answer": "That the current version is already correct",
            },
            {
                "question": f"What kind of bug is especially common in technical implementations of {cleaned_topic}?",
                "options": [
                    "Edge-case handling mistakes",
                    "Using too many headings",
                    "Adding extra spaces",
                    "Writing shorter explanations",
                ],
                "correct_answer": "Edge-case handling mistakes",
            },
            {
                "question": f"Why should you test unusual inputs for {cleaned_topic}?",
                "options": [
                    "They reveal cases where logic can break",
                    "They make the question easier",
                    "They remove the need for analysis",
                    "They are useful only for beginners",
                ],
                "correct_answer": "They reveal cases where logic can break",
            },
            {
                "question": f"What does a good dry run of {cleaned_topic} help uncover?",
                "options": [
                    "State changes and hidden assumptions",
                    "Only formatting issues",
                    "How many headings are present",
                    "Whether the code uses tabs",
                ],
                "correct_answer": "State changes and hidden assumptions",
            },
            {
                "question": f"If {cleaned_topic} relies on a precondition, what should you do in an interview?",
                "options": [
                    "State the precondition clearly before solving",
                    "Ignore it and continue",
                    "Assume the interviewer already knows",
                    "Hide it inside the final answer",
                ],
                "correct_answer": "State the precondition clearly before solving",
            },
            {
                "question": f"What is the best reason to discuss tradeoffs in {cleaned_topic}?",
                "options": [
                    "Different constraints may favor different solutions",
                    "Tradeoffs make definitions unnecessary",
                    "Tradeoffs matter only in theory",
                    "Tradeoffs replace testing",
                ],
                "correct_answer": "Different constraints may favor different solutions",
            },
            {
                "question": f"What should you inspect when performance is poor in {cleaned_topic}?",
                "options": [
                    "The most expensive repeated step",
                    "Only the app theme",
                    "Only the variable names",
                    "Only the final print statement",
                ],
                "correct_answer": "The most expensive repeated step",
            },
            {
                "question": f"Why do edge cases matter in interview questions on {cleaned_topic}?",
                "options": [
                    "They show whether you really understand the logic",
                    "They are never discussed",
                    "They make definitions shorter",
                    "They only affect UI",
                ],
                "correct_answer": "They show whether you really understand the logic",
            },
            {
                "question": f"What does an invariant help you do while reasoning about {cleaned_topic}?",
                "options": [
                    "Track what must remain true at each step",
                    "Avoid all examples",
                    "Replace the final answer",
                    "Skip correctness checks",
                ],
                "correct_answer": "Track what must remain true at each step",
            },
            {
                "question": f"What makes an advanced answer on {cleaned_topic} stand out?",
                "options": [
                    "Clear logic, complexity, and edge-case discussion",
                    "Very long unrelated theory",
                    "Only memorized keywords",
                    "Avoiding concrete examples",
                ],
                "correct_answer": "Clear logic, complexity, and edge-case discussion",
            },
        ]

    if level == "intermediate":
        return [
            {
                "question": f"What is the best way to understand the logic of {cleaned_topic}?",
                "options": [
                    "Trace each step with a small example",
                    "Memorize without testing",
                    "Skip the reason behind each step",
                    "Only read the final answer",
                ],
                "correct_answer": "Trace each step with a small example",
            },
            {
                "question": f"Why are examples useful when learning {cleaned_topic}?",
                "options": [
                    "They show how the concept behaves in practice",
                    "They replace the concept itself",
                    "They hide mistakes automatically",
                    "They make rules unnecessary",
                ],
                "correct_answer": "They show how the concept behaves in practice",
            },
            {
                "question": f"What should you check after applying {cleaned_topic} logic?",
                "options": [
                    "Whether the result follows from each step",
                    "Whether the answer looks long",
                    "Whether the topic name is repeated",
                    "Whether no assumptions were written",
                ],
                "correct_answer": "Whether the result follows from each step",
            },
            {
                "question": f"What should you identify before solving a problem using {cleaned_topic}?",
                "options": [
                    "The input, output, and rule being applied",
                    "Only the color of the code editor",
                    "Only the final print statement",
                    "Only the topic name",
                ],
                "correct_answer": "The input, output, and rule being applied",
            },
            {
                "question": f"Why is a dry run useful for {cleaned_topic}?",
                "options": [
                    "It shows how values change step by step",
                    "It removes the need for definitions",
                    "It guarantees the code is optimal",
                    "It matters only after deployment",
                ],
                "correct_answer": "It shows how values change step by step",
            },
            {
                "question": f"What is a common mistake while studying {cleaned_topic}?",
                "options": [
                    "Memorizing steps without understanding why they work",
                    "Testing with a small example",
                    "Writing short notes",
                    "Checking the output",
                ],
                "correct_answer": "Memorizing steps without understanding why they work",
            },
            {
                "question": f"Why should you look at edge cases in {cleaned_topic}?",
                "options": [
                    "They reveal where the usual flow may fail",
                    "They are only for advanced learners",
                    "They make the topic unrelated to logic",
                    "They are useful only for UI design",
                ],
                "correct_answer": "They reveal where the usual flow may fail",
            },
            {
                "question": f"What does a good explanation of {cleaned_topic} usually connect?",
                "options": [
                    "Definition, working idea, and one example",
                    "Only theory with no example",
                    "Only code with no idea",
                    "Only output with no process",
                ],
                "correct_answer": "Definition, working idea, and one example",
            },
            {
                "question": f"When reviewing {cleaned_topic}, what should you focus on first?",
                "options": [
                    "The core rule that drives each step",
                    "Making the answer longer",
                    "Adding decorative symbols",
                    "Ignoring incorrect assumptions",
                ],
                "correct_answer": "The core rule that drives each step",
            },
            {
                "question": f"What does checking a small test case help you confirm in {cleaned_topic}?",
                "options": [
                    "That your reasoning matches the actual result",
                    "That the file name is correct",
                    "That the explanation is short",
                    "That the topic is easy",
                ],
                "correct_answer": "That your reasoning matches the actual result",
            },
            {
                "question": f"What is the benefit of comparing two examples of {cleaned_topic}?",
                "options": [
                    "It shows what changes and what stays consistent",
                    "It removes the need for practice",
                    "It makes all edge cases disappear",
                    "It replaces the definition",
                ],
                "correct_answer": "It shows what changes and what stays consistent",
            },
            {
                "question": f"What should you do if your output for {cleaned_topic} is wrong?",
                "options": [
                    "Go step by step and find where the logic changed",
                    "Assume the question is wrong",
                    "Skip testing",
                    "Change all options randomly",
                ],
                "correct_answer": "Go step by step and find where the logic changed",
            },
            {
                "question": f"Why is a real example helpful for {cleaned_topic}?",
                "options": [
                    "It turns the idea into something easier to picture",
                    "It makes the concept less precise",
                    "It removes the need for code",
                    "It only matters in design projects",
                ],
                "correct_answer": "It turns the idea into something easier to picture",
            },
            {
                "question": f"What should you keep in mind while revising {cleaned_topic}?",
                "options": [
                    "Key steps, one example, and one common mistake",
                    "Only the title of the topic",
                    "Only one definition word",
                    "Only the longest option",
                ],
                "correct_answer": "Key steps, one example, and one common mistake",
            },
            {
                "question": f"What makes an answer on {cleaned_topic} more convincing?",
                "options": [
                    "Explaining both the idea and how it behaves on an example",
                    "Using more filler words",
                    "Repeating the same sentence",
                    "Avoiding all reasoning",
                ],
                "correct_answer": "Explaining both the idea and how it behaves on an example",
            },
        ]

    return [
        {
            "question": f"What is the main goal when first learning {cleaned_topic}?",
            "options": [
                "Understand the core idea in simple words",
                "Memorize advanced formulas immediately",
                "Avoid examples",
                "Skip the basics",
            ],
            "correct_answer": "Understand the core idea in simple words",
        },
        {
            "question": f"Which learning method is best for a beginner studying {cleaned_topic}?",
            "options": [
                "Use a simple example and explain each step",
                "Jump directly to rare edge cases",
                "Ignore mistakes",
                "Only read definitions",
            ],
            "correct_answer": "Use a simple example and explain each step",
        },
        {
            "question": f"What should you do if {cleaned_topic} feels confusing?",
            "options": [
                "Break it into smaller parts",
                "Stop practicing",
                "Assume it cannot be learned",
                "Memorize random answers",
            ],
            "correct_answer": "Break it into smaller parts",
        },
        {
            "question": f"Why is a real-life analogy useful for {cleaned_topic}?",
            "options": [
                "It makes the idea easier to imagine",
                "It replaces the actual concept",
                "It removes the need to think",
                "It only matters in exams",
            ],
            "correct_answer": "It makes the idea easier to imagine",
        },
        {
            "question": f"What does a small worked example help you see in {cleaned_topic}?",
            "options": [
                "How the idea works step by step",
                "Only the final heading",
                "Only the file name",
                "Only the UI colors",
            ],
            "correct_answer": "How the idea works step by step",
        },
        {
            "question": f"Why is it helpful to ask what problem {cleaned_topic} solves?",
            "options": [
                "It tells you why the concept is useful",
                "It makes examples unnecessary",
                "It changes the topic name",
                "It removes the need for output",
            ],
            "correct_answer": "It tells you why the concept is useful",
        },
        {
            "question": f"What is a good first step before writing code for {cleaned_topic}?",
            "options": [
                "Understand the idea with a tiny example",
                "Start optimizing immediately",
                "Skip the explanation",
                "Memorize random syntax",
            ],
            "correct_answer": "Understand the idea with a tiny example",
        },
        {
            "question": f"What should beginner notes on {cleaned_topic} contain?",
            "options": [
                "Definition, one example, and key points",
                "Only hard interview tricks",
                "Only long theory",
                "Only code with no explanation",
            ],
            "correct_answer": "Definition, one example, and key points",
        },
        {
            "question": f"Why is step-by-step explanation important for {cleaned_topic}?",
            "options": [
                "It shows what happens at each stage",
                "It makes the concept more confusing",
                "It removes the final answer",
                "It matters only for experts",
            ],
            "correct_answer": "It shows what happens at each stage",
        },
        {
            "question": f"What should you check after reading an example of {cleaned_topic}?",
            "options": [
                "Whether you can explain the flow in your own words",
                "Whether the answer is long",
                "Whether the topic has a fancy name",
                "Whether the code editor theme changed",
            ],
            "correct_answer": "Whether you can explain the flow in your own words",
        },
        {
            "question": f"What is the safest way to remember {cleaned_topic} for exams or interviews?",
            "options": [
                "Link the definition with one small example",
                "Memorize only the title",
                "Skip practice entirely",
                "Read only advanced edge cases",
            ],
            "correct_answer": "Link the definition with one small example",
        },
        {
            "question": f"Why is practice helpful while learning {cleaned_topic}?",
            "options": [
                "It turns the explanation into understanding",
                "It removes the need for examples",
                "It guarantees perfection after one try",
                "It matters only after deployment",
            ],
            "correct_answer": "It turns the explanation into understanding",
        },
        {
            "question": f"What is a common beginner mistake in {cleaned_topic}?",
            "options": [
                "Trying to memorize without understanding the flow",
                "Asking simple questions",
                "Using small examples",
                "Reading key points",
            ],
            "correct_answer": "Trying to memorize without understanding the flow",
        },
        {
            "question": f"What should you focus on when a code example of {cleaned_topic} is shown?",
            "options": [
                "How each line connects to the concept",
                "Only the color of the code block",
                "Only the number of lines",
                "Only the final semicolon",
            ],
            "correct_answer": "How each line connects to the concept",
        },
        {
            "question": f"What does real understanding of {cleaned_topic} look like?",
            "options": [
                "You can explain it simply and walk through one example",
                "You know only one difficult word",
                "You can copy code without reading it",
                "You avoid all questions about it",
            ],
            "correct_answer": "You can explain it simply and walk through one example",
        },
    ]


def _fallback_explanation(
    topic: str,
    level: str,
    language: str,
    mode: str,
    response_depth: str,
    response_mode: str,
    code_required: bool,
    code_language: str,
    weak_areas: list[str] | None,
) -> str:
    return _format_fallback_explanation(
        topic=topic,
        level=level,
        language=language,
        mode=mode,
        response_depth=response_depth,
        response_mode=response_mode,
        code_required=code_required,
        code_language=code_language,
        weak_areas=weak_areas,
    )


def _format_fallback_explanation(
    topic: str,
    level: str,
    language: str,
    mode: str,
    response_depth: str,
    response_mode: str,
    code_required: bool,
    code_language: str,
    weak_areas: list[str] | None,
) -> str:
    cleaned_topic = topic.strip() or "this concept"
    normalized_language = normalize_language(language)
    normalized_level = (level or "beginner").strip().lower()
    normalized_response_mode = normalize_response_mode(response_mode)
    normalized_response_depth = _resolve_response_depth(response_depth, normalized_response_mode)
    normalized_code_language = normalize_code_language(code_language)
    normalized_code_required = code_required or normalized_response_mode == "code"
    weak_area_text = ", ".join(weak_areas or [])
    details = _get_concept_details(cleaned_topic)

    if normalized_response_mode == "short":
        body = _format_compact_fallback_explanation(
            details=details,
            level=level,
            mode=mode,
            code_required=normalized_code_required,
            code_language=normalized_code_language,
            response_mode=normalized_response_mode,
        )
    elif normalized_response_mode == "interview":
        body = _format_interview_fallback_explanation(
            details=details,
            level=level,
            mode=mode,
            code_required=normalized_code_required,
            code_language=normalized_code_language,
        )
    elif normalized_response_depth == "detailed":
        body = _format_detailed_fallback_explanation(
            details=details,
            level=level,
            mode=mode,
            response_mode=normalized_response_mode,
            code_required=normalized_code_required,
            code_language=normalized_code_language,
        )
    else:
        body = _format_compact_fallback_explanation(
            details=details,
            level=level,
            mode=mode,
            code_required=normalized_code_required,
            code_language=normalized_code_language,
            response_mode=normalized_response_mode,
        )

    if weak_area_text:
        body += f"\n\nFocus area: spend extra time on {weak_area_text} while revising this topic."

    if normalized_language == "Hinglish" and normalized_level == "beginner":
        body = (
            "Chalo is concept ko aise samajhte hain jaise friend ko samjha rahe ho.\n\n"
            f"{body}"
        )
    elif normalized_language == "Hinglish":
        body = f"Chalo is concept ko step by step samajhte hain.\n\n{body}"
    elif normalized_language == "Hindi":
        body = f"Chaliye is concept ko step by step samajhte hain.\n\n{body}"

    return _normalize_explanation_markdown(body)


def _fallback_intro_line(title: str, response_mode: str = "auto") -> str:
    lowered_title = title.strip().lower() or "this concept"
    if response_mode == "notes":
        return f"Let's build a clean understanding of {lowered_title} step by step."

    if response_mode == "interview":
        return f"Let's look at {lowered_title} the way an interviewer expects you to explain it."

    return f"Let's understand {lowered_title} step by step."


def _compose_study_note(
    title: str,
    sections: list[tuple[str, str]],
) -> str:
    blocks = [f"## {title}"]
    for label, content in sections:
        cleaned_content = (content or "").strip()
        if cleaned_content:
            blocks.append(f"**{label}:**\n{cleaned_content}")

    return "\n\n".join(blocks)


def _get_interview_questions(title: str) -> str:
    lowered_title = title.strip().lower() or "this topic"
    return (
        f"- What is {lowered_title} and where is it used?\n"
        f"- What is the time or space complexity associated with {lowered_title}?\n"
        f"- What common mistake do candidates make while explaining or implementing {lowered_title}?"
    )


def _format_compact_fallback_explanation(
    details: dict[str, str],
    level: str,
    mode: str,
    code_required: bool,
    code_language: str,
    response_mode: str,
) -> str:
    is_beginner = level == "beginner" or mode == "simpler"
    definition = details["simple_definition"] if is_beginner else details["definition"]
    explanation = details["simple"] if is_beginner else details["standard"]
    key_points = details["key_points"]

    if response_mode == "short":
        return _compose_study_note(
            title=details["title"],
            sections=[
                ("Definition", definition),
                ("Key points", key_points),
            ],
        )

    if mode == "technical":
        technical_view = (
            f"{details['technical']}\n\n{details['operations']}\n{details['complexity']}"
        )
    else:
        technical_view = f"{details['technical']}\n\n{details['complexity']}"

    if is_beginner:
        explanation = (
            f"{details['simple']}\n\n"
            f"Small example: {details['example']}"
        )
        real_life_example = f"{details['analogy']}\n\nSmall example: {details['example']}"
    else:
        real_life_example = f"{details['analogy']}\n\nExample: {details['example']}"

    sections = [
        ("Definition", definition),
        ("In-depth explanation", explanation),
        ("Deeper technical view", technical_view),
        ("Real-life intuition", real_life_example),
        ("Key points to remember", key_points),
        ("Final takeaway", details["takeaway"]),
    ]

    if code_required:
        code_material = _get_code_material(details=details, code_language=code_language)
        if code_material:
            sections.extend(
                [
                    ("Code example", f"```{code_material['fence_language']}\n{code_material['code_example']}\n```"),
                    ("Expected output", f"```text\n{code_material['code_output']}\n```"),
                    ("Step-by-step dry run", code_material["code_walkthrough"]),
                ]
            )

    return _compose_study_note(title=details["title"], sections=sections)


def _format_detailed_fallback_explanation(
    details: dict[str, str],
    level: str,
    mode: str,
    response_mode: str,
    code_required: bool,
    code_language: str,
) -> str:
    is_beginner = level == "beginner" or mode == "simpler"
    definition = details["simple_definition"] if is_beginner else details["definition"]
    if is_beginner:
        explanation_core = (
            f"{details['simple']}\n\n"
            f"Chhota real example: {details['example']}"
        )
        technical_view = (
            "Ab basic idea clear hai, to technical side ko simple words me dekhte hain.\n\n"
            f"{details['technical']}"
        )
    else:
        explanation_core = details["standard"]
        technical_view = details["technical"]
    code_material = _get_code_material(details=details, code_language=code_language)
    sections: list[tuple[str, str]] = [
        ("Definition", definition),
        ("In-depth explanation", explanation_core),
        ("Deeper technical view", technical_view),
        ("Operations and complexity", f"{details['operations']}\n{details['complexity']}"),
        (
            "Real-life intuition",
            f"{details['analogy']}\n\n{'Small example' if is_beginner else 'Example'}: {details['example']}",
        ),
        ("Why we use it", details["uses"]),
    ]

    if code_material and (code_required or response_mode in {"detailed", "notes", "code"}):
        sections.extend(
            [
                ("Code example", f"```{code_material['fence_language']}\n{code_material['code_example']}\n```"),
                ("Expected output", f"```text\n{code_material['code_output']}\n```"),
                ("Step-by-step dry run", code_material["code_walkthrough"]),
            ]
        )

    sections.extend(
        [
            ("Important points / interview points", details["interview_points"]),
            ("Common mistakes / edge cases", details["common_mistakes"]),
            ("Key points to remember", details["key_points"]),
            ("Final takeaway", details["takeaway"]),
        ]
    )

    return _compose_study_note(title=details["title"], sections=sections)


def _format_interview_fallback_explanation(
    details: dict[str, str],
    level: str,
    mode: str,
    code_required: bool,
    code_language: str,
) -> str:
    definition = details["simple_definition"] if level == "beginner" or mode == "simpler" else details["definition"]
    sections: list[tuple[str, str]] = [
        ("Definition", definition),
        ("Complexity", details["complexity"]),
        ("Technical view", details["technical"]),
        ("Edge cases / common traps", details["common_mistakes"]),
        ("Interview points", details["interview_points"]),
        ("Interview questions", _get_interview_questions(details["title"])),
        ("Final takeaway", details["takeaway"]),
    ]

    if code_required:
        code_material = _get_code_material(details=details, code_language=code_language)
        if code_material:
            sections.extend(
                [
                    ("Code example", f"```{code_material['fence_language']}\n{code_material['code_example']}\n```"),
                    ("Expected output", f"```text\n{code_material['code_output']}\n```"),
                    ("Step-by-step dry run", code_material["code_walkthrough"]),
                ]
            )

    return _compose_study_note(title=details["title"], sections=sections)


def _get_code_material(details: dict[str, str], code_language: str) -> dict[str, str] | None:
    topic_key = details.get("concept_key", details["title"].strip().lower())
    normalized_code_language = normalize_code_language(code_language)
    fence_languages = {"Python": "python", "Java": "java", "C": "c"}

    if normalized_code_language == "Python" and details.get("code_example", "").strip():
        return {
            "language": "Python",
            "fence_language": "python",
            "code_example": details["code_example"],
            "code_output": details["code_output"],
            "code_walkthrough": details["code_walkthrough"],
        }

    alternate_examples = {
        ("array", "Java"): {
            "code_example": (
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        int[] numbers = {10, 20, 30, 40};\n"
                "        System.out.println(\"First element: \" + numbers[0]);\n"
                "        System.out.println(\"Third element: \" + numbers[2]);\n"
                "        numbers[1] = 25;\n"
                "        System.out.println(\"Updated array: \" + java.util.Arrays.toString(numbers));\n"
                "    }\n"
                "}"
            ),
            "code_output": "First element: 10\nThird element: 30\nUpdated array: [10, 25, 30, 40]",
            "code_walkthrough": (
                "1. We create an integer array with four values.\n"
                "2. `numbers[0]` and `numbers[2]` access elements directly by index.\n"
                "3. `numbers[1] = 25` updates the second element.\n"
                "4. `Arrays.toString(numbers)` prints the whole array in a readable form."
            ),
        },
        ("array", "C"): {
            "code_example": (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int numbers[] = {10, 20, 30, 40};\n"
                "    numbers[1] = 25;\n\n"
                "    printf(\"First element: %d\\n\", numbers[0]);\n"
                "    printf(\"Third element: %d\\n\", numbers[2]);\n"
                "    printf(\"Updated array: [%d, %d, %d, %d]\\n\", numbers[0], numbers[1], numbers[2], numbers[3]);\n"
                "    return 0;\n"
                "}"
            ),
            "code_output": "First element: 10\nThird element: 30\nUpdated array: [10, 25, 30, 40]",
            "code_walkthrough": (
                "1. We declare an integer array with four values.\n"
                "2. Each element is accessed by its index, starting from `0`.\n"
                "3. `numbers[1] = 25` changes the second element.\n"
                "4. `printf` prints individual values to show the updated array."
            ),
        },
        ("linked list", "Java"): {
            "code_example": (
                "class Node {\n"
                "    int data;\n"
                "    Node next;\n\n"
                "    Node(int data) {\n"
                "        this.data = data;\n"
                "    }\n"
                "}\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Node head = new Node(10);\n"
                "        head.next = new Node(20);\n"
                "        head.next.next = new Node(30);\n\n"
                "        Node current = head;\n"
                "        while (current != null) {\n"
                "            System.out.println(current.data);\n"
                "            current = current.next;\n"
                "        }\n"
                "    }\n"
                "}"
            ),
            "code_output": "10\n20\n30",
            "code_walkthrough": (
                "1. `Node` stores the data and the link to the next node.\n"
                "2. `head` points to the first node.\n"
                "3. The next assignments connect `10 -> 20 -> 30`.\n"
                "4. The loop starts at the head and keeps following `next` until it reaches `null`."
            ),
        },
        ("linked list", "C"): {
            "code_example": (
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "struct Node {\n"
                "    int data;\n"
                "    struct Node* next;\n"
                "};\n\n"
                "int main() {\n"
                "    struct Node* first = malloc(sizeof(struct Node));\n"
                "    struct Node* second = malloc(sizeof(struct Node));\n"
                "    struct Node* third = malloc(sizeof(struct Node));\n\n"
                "    first->data = 10; first->next = second;\n"
                "    second->data = 20; second->next = third;\n"
                "    third->data = 30; third->next = NULL;\n\n"
                "    struct Node* current = first;\n"
                "    while (current != NULL) {\n"
                "        printf(\"%d\\n\", current->data);\n"
                "        current = current->next;\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "code_output": "10\n20\n30",
            "code_walkthrough": (
                "1. Each node stores a value and a pointer to the next node.\n"
                "2. We create three nodes and connect them in order.\n"
                "3. The loop starts from the first node and follows `next` until it reaches `NULL`."
            ),
        },
        ("stack", "Java"): {
            "code_example": (
                "import java.util.Stack;\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Stack<Integer> stack = new Stack<>();\n"
                "        stack.push(10);\n"
                "        stack.push(20);\n"
                "        stack.push(30);\n\n"
                "        System.out.println(\"Top element: \" + stack.peek());\n"
                "        System.out.println(\"Removed: \" + stack.pop());\n"
                "        System.out.println(\"Stack now: \" + stack);\n"
                "    }\n"
                "}"
            ),
            "code_output": "Top element: 30\nRemoved: 30\nStack now: [10, 20]",
            "code_walkthrough": (
                "1. We create a `Stack<Integer>`.\n"
                "2. `push()` adds elements to the top.\n"
                "3. `peek()` reads the current top value.\n"
                "4. `pop()` removes that top value and returns it."
            ),
        },
        ("stack", "C"): {
            "code_example": (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int stack[3];\n"
                "    int top = -1;\n\n"
                "    stack[++top] = 10;\n"
                "    stack[++top] = 20;\n"
                "    stack[++top] = 30;\n\n"
                "    printf(\"Top element: %d\\n\", stack[top]);\n"
                "    printf(\"Removed: %d\\n\", stack[top--]);\n"
                "    printf(\"Stack now: [%d, %d]\\n\", stack[0], stack[1]);\n"
                "    return 0;\n"
                "}"
            ),
            "code_output": "Top element: 30\nRemoved: 30\nStack now: [10, 20]",
            "code_walkthrough": (
                "1. `top` keeps track of the current top index.\n"
                "2. `++top` moves up and stores the new value.\n"
                "3. `stack[top]` reads the current top element.\n"
                "4. `top--` removes the latest value, which shows LIFO behavior."
            ),
        },
        ("recursion", "Java"): {
            "code_example": (
                "public class Main {\n"
                "    static int factorial(int n) {\n"
                "        if (n == 1) {\n"
                "            return 1;\n"
                "        }\n"
                "        return n * factorial(n - 1);\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        System.out.println(factorial(4));\n"
                "    }\n"
                "}"
            ),
            "code_output": "24",
            "code_walkthrough": (
                "1. `factorial(4)` calls `factorial(3)`.\n"
                "2. The calls continue until `factorial(1)` hits the base case.\n"
                "3. Then the answers return upward and multiply together to give `24`."
            ),
        },
        ("recursion", "C"): {
            "code_example": (
                "#include <stdio.h>\n\n"
                "int factorial(int n) {\n"
                "    if (n == 1) {\n"
                "        return 1;\n"
                "    }\n"
                "    return n * factorial(n - 1);\n"
                "}\n\n"
                "int main() {\n"
                "    printf(\"%d\\n\", factorial(4));\n"
                "    return 0;\n"
                "}"
            ),
            "code_output": "24",
            "code_walkthrough": (
                "1. Each function call waits for a smaller call to finish.\n"
                "2. `factorial(1)` is the base case and returns `1`.\n"
                "3. The earlier calls multiply their values on the way back, producing `24`."
            ),
        },
        ("binary search", "Java"): {
            "code_example": (
                "public class Main {\n"
                "    static int binarySearch(int[] arr, int target) {\n"
                "        int low = 0;\n"
                "        int high = arr.length - 1;\n\n"
                "        while (low <= high) {\n"
                "            int mid = (low + high) / 2;\n"
                "            if (arr[mid] == target) return mid;\n"
                "            if (arr[mid] < target) {\n"
                "                low = mid + 1;\n"
                "            } else {\n"
                "                high = mid - 1;\n"
                "            }\n"
                "        }\n"
                "        return -1;\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                "        int[] numbers = {1, 3, 5, 7, 9};\n"
                "        System.out.println(binarySearch(numbers, 7));\n"
                "    }\n"
                "}"
            ),
            "code_output": "3",
            "code_walkthrough": (
                "1. `low` and `high` mark the current search range.\n"
                "2. `mid` checks the middle position.\n"
                "3. If the middle value is too small, we move right; otherwise we move left.\n"
                "4. The function returns index `3` when it finds `7`."
            ),
        },
        ("binary search", "C"): {
            "code_example": (
                "#include <stdio.h>\n\n"
                "int binarySearch(int arr[], int size, int target) {\n"
                "    int low = 0;\n"
                "    int high = size - 1;\n\n"
                "    while (low <= high) {\n"
                "        int mid = (low + high) / 2;\n"
                "        if (arr[mid] == target) return mid;\n"
                "        if (arr[mid] < target) {\n"
                "            low = mid + 1;\n"
                "        } else {\n"
                "            high = mid - 1;\n"
                "        }\n"
                "    }\n"
                "    return -1;\n"
                "}\n\n"
                "int main() {\n"
                "    int numbers[] = {1, 3, 5, 7, 9};\n"
                "    printf(\"%d\\n\", binarySearch(numbers, 5, 7));\n"
                "    return 0;\n"
                "}"
            ),
            "code_output": "3",
            "code_walkthrough": (
                "1. `low` and `high` track the current search range.\n"
                "2. Each loop checks the middle element.\n"
                "3. The code removes half the range after each comparison.\n"
                "4. When `7` is found, the function returns index `3`."
            ),
        },
    }

    alternate_material = alternate_examples.get((topic_key, normalized_code_language))
    if alternate_material:
        return {
            "language": normalized_code_language,
            "fence_language": fence_languages.get(normalized_code_language, "text"),
            **alternate_material,
        }

    return None


def _get_concept_details(topic: str) -> dict[str, str]:
    key = " ".join(topic.lower().strip().split())
    aliases = {
        "arrays": "array",
        "linked lists": "linked list",
        "stacks": "stack",
        "queue data structure": "queue",
        "queues": "queue",
        "recursive function": "recursion",
        "binary searching": "binary search",
    }
    key = aliases.get(key, key)

    concepts = {
        "array": {
            "title": "Array",
            "definition": "An array is a linear data structure that stores multiple values in contiguous positions and lets us access elements by index.",
            "simple_definition": "An array is like a row of boxes where each box has a number called an index.",
            "simple": "Each value sits in a fixed position, so if you know the index, you can reach that value quickly.",
            "standard": "Arrays keep related data together in order. Because each position is indexed, reading an element is very fast, especially when you already know where to look.",
            "analogy": "Think of cinema seats in one row. Every seat has a position number, so you can directly go to seat 5 without checking every other seat first.",
            "example": "Marks of students, temperatures of a week, or prices of products can all be stored in an array when order matters.",
            "technical": "Arrays are usually stored in contiguous memory. That is why random access by index is O(1), but inserting in the middle can require shifting elements.",
            "operations": "- access arr[i]\n- update arr[i] = value\n- traverse each element\n- insert/delete may require shifting elements",
            "complexity": "Access is O(1), while searching is O(n) in an unsorted array and insertion/deletion in the middle is usually O(n).",
            "uses": "Used when you need ordered storage, fast index-based access, iteration, or a base structure for many algorithms.",
            "code_example": (
                "numbers = [10, 20, 30, 40]\n"
                "print('First element:', numbers[0])\n"
                "print('Third element:', numbers[2])\n"
                "numbers[1] = 25\n"
                "print('Updated array:', numbers)"
            ),
            "code_output": "First element: 10\nThird element: 30\nUpdated array: [10, 25, 30, 40]",
            "code_walkthrough": (
                "1. We create an array-like list with four values.\n"
                "2. `numbers[0]` reads the first position, so it prints `10`.\n"
                "3. `numbers[2]` reads the third position, so it prints `30`.\n"
                "4. `numbers[1] = 25` updates the second element.\n"
                "5. Printing the array shows the modified order `[10, 25, 30, 40]`."
            ),
            "interview_points": (
                "- Arrays support O(1) index access.\n"
                "- They store elements in order and are easy to traverse.\n"
                "- Insertion or deletion in the middle is expensive because elements may need shifting."
            ),
            "common_mistakes": (
                "- Confusing index with value.\n"
                "- Accessing an index that is out of range.\n"
                "- Assuming insertion in the middle is always fast."
            ),
            "key_points": "- Elements are stored in order\n- Each element has an index\n- Great for fast direct access",
            "takeaway": "Use an array when you want ordered data and quick access by position.",
        },
        "linked list": {
            "title": "Linked List",
            "definition": "A linked list is a linear data structure made of nodes, where each node stores data and a reference to the next node.",
            "simple_definition": "A linked list is a chain of boxes where each box tells you where the next box is.",
            "simple": "Instead of keeping all values side by side like an array, a linked list connects one node to the next node using links.",
            "standard": "A linked list stores elements as separate nodes connected by pointers or references. This makes insertion and deletion easier at known positions, but direct index access is slower than an array.",
            "analogy": "Think of a treasure hunt where each clue points to the next clue. You cannot jump straight to the fifth clue until you follow the earlier ones.",
            "example": "Music playlists and browser forward/backward navigation often use linked structures because moving between connected items is natural.",
            "technical": "Each node usually contains `data` and `next`. In doubly linked lists, nodes also keep a `prev` reference. Traversal is O(n), while insertion at the head can be O(1).",
            "operations": "- create a node\n- point one node to the next\n- traverse from head to end\n- insert/delete by changing links",
            "complexity": "Access by position is O(n), while insertion or deletion at the head is O(1).",
            "uses": "Useful when frequent insertion and deletion matter more than random index access.",
            "code_example": (
                "class Node:\n"
                "    def __init__(self, data):\n"
                "        self.data = data\n"
                "        self.next = None\n\n"
                "head = Node(10)\n"
                "head.next = Node(20)\n"
                "head.next.next = Node(30)\n\n"
                "current = head\n"
                "while current:\n"
                "    print(current.data)\n"
                "    current = current.next"
            ),
            "code_output": "10\n20\n30",
            "code_walkthrough": (
                "1. We define a `Node` class that stores data and a link to the next node.\n"
                "2. `head` points to the first node containing `10`.\n"
                "3. The next two statements connect `10 -> 20 -> 30`.\n"
                "4. `current = head` starts traversal from the beginning.\n"
                "5. The loop prints each node's data and moves to the next node until it reaches `None`."
            ),
            "interview_points": (
                "- A linked list stores nodes, not contiguous elements like an array.\n"
                "- Direct access by index is O(n).\n"
                "- Insertion/deletion can be efficient because links are updated instead of shifting many elements."
            ),
            "common_mistakes": (
                "- Forgetting to update links during insertion or deletion.\n"
                "- Losing the head pointer.\n"
                "- Expecting O(1) index access like an array."
            ),
            "key_points": "- Nodes are connected through links\n- Traversal starts from the head\n- Good for flexible insertion and deletion",
            "takeaway": "A linked list trades fast indexed access for flexible node insertion and deletion.",
        },
        "stack": {
            "title": "Stack",
            "definition": "A stack is a linear data structure that follows LIFO: Last In, First Out.",
            "simple_definition": "A stack stores items so the last item added is removed first.",
            "simple": "Think of it like a pile. You add a new item on top, and when you remove something, you remove the top item first.",
            "standard": "A stack has one open end called the top. New elements are pushed onto the top, and removals happen from the same top position.",
            "analogy": "A pile of plates: the last plate placed on top is the first plate you pick up.",
            "example": "Browser Back works like a stack: every page you visit is pushed, and pressing Back pops the latest page.",
            "technical": "A stack maintains a top pointer/index. Push moves the top forward and inserts an item; pop returns the top item and moves the top backward.",
            "operations": "- push(x): add x on top\n- pop(): remove and return top item\n- peek(): read top item\n- isEmpty(): check whether stack has no items",
            "complexity": "push, pop, and peek are usually O(1).",
            "uses": "Function call stack, undo/redo, expression evaluation, DFS, browser history.",
            "code_example": (
                "stack = []\n"
                "stack.append(10)\n"
                "stack.append(20)\n"
                "stack.append(30)\n\n"
                "print('Top element:', stack[-1])\n"
                "print('Removed:', stack.pop())\n"
                "print('Stack now:', stack)"
            ),
            "code_output": "Top element: 30\nRemoved: 30\nStack now: [10, 20]",
            "code_walkthrough": (
                "1. We start with an empty list and use it like a stack.\n"
                "2. `append()` pushes values on top, so the order becomes `[10, 20, 30]`.\n"
                "3. `stack[-1]` reads the current top element, which is `30`.\n"
                "4. `pop()` removes and returns that same top element.\n"
                "5. After removing `30`, the stack still keeps the older values `[10, 20]`."
            ),
            "interview_points": (
                "- Stack follows LIFO order.\n"
                "- Push, pop, and peek are usually O(1).\n"
                "- Common uses include function calls, undo/redo, DFS, and expression evaluation."
            ),
            "common_mistakes": (
                "- Popping from an empty stack without checking first.\n"
                "- Confusing stack order with queue order.\n"
                "- Forgetting that insertion and deletion both happen at the top."
            ),
            "key_points": "- LIFO order\n- Insertion and deletion happen at the top\n- Useful when the most recent item should be handled first",
            "takeaway": "If the newest item must come out first, a stack is usually a good fit.",
        },
        "queue": {
            "title": "Queue",
            "definition": "A queue is a linear data structure that follows FIFO: First In, First Out.",
            "simple_definition": "A queue stores items so the first item added is removed first.",
            "simple": "Items join at the back and leave from the front, just like people waiting in line.",
            "standard": "A queue keeps order by adding new items at the rear and removing old items from the front.",
            "analogy": "A ticket counter line: the person who arrives first gets served first.",
            "example": "Print jobs use a queue: the first document sent to the printer is printed first.",
            "technical": "A queue tracks front and rear positions. Enqueue inserts at rear; dequeue removes from front.",
            "operations": "- enqueue(x): add x at rear\n- dequeue(): remove front item\n- front(): read first item\n- isEmpty(): check if queue is empty",
            "complexity": "enqueue and dequeue are usually O(1) with a proper implementation.",
            "uses": "Scheduling, BFS, print queues, message queues, buffering.",
            "code_example": (
                "from collections import deque\n\n"
                "queue = deque()\n"
                "queue.append('A')\n"
                "queue.append('B')\n"
                "queue.append('C')\n\n"
                "print('Front element:', queue[0])\n"
                "print('Removed:', queue.popleft())\n"
                "print('Queue now:', list(queue))"
            ),
            "code_output": "Front element: A\nRemoved: A\nQueue now: ['B', 'C']",
            "code_walkthrough": (
                "1. We create a queue using `deque`, which is efficient for adding and removing from both ends.\n"
                "2. `append()` adds items at the rear in the order `A`, `B`, `C`.\n"
                "3. `queue[0]` shows the front element, which is the oldest item.\n"
                "4. `popleft()` removes the front item first, so `A` leaves before `B` and `C`.\n"
                "5. The queue keeps the remaining order as `['B', 'C']`."
            ),
            "interview_points": (
                "- Queue follows FIFO order.\n"
                "- Enqueue and dequeue are usually O(1) with the right data structure.\n"
                "- BFS, scheduling, buffering, and task pipelines often use queues."
            ),
            "common_mistakes": (
                "- Using a plain list inefficiently for front removals in Python.\n"
                "- Mixing up FIFO with LIFO.\n"
                "- Forgetting to handle the empty-queue case before dequeue."
            ),
            "key_points": "- FIFO order\n- Insert at rear, remove from front\n- Useful when fairness/order matters",
            "takeaway": "If the oldest item should be handled first, use a queue.",
        },
        "recursion": {
            "title": "Recursion",
            "definition": "Recursion is a technique where a function solves a problem by calling itself on smaller inputs.",
            "simple_definition": "Recursion means a function repeats itself on a smaller version of the same problem.",
            "simple": "Each call does a small part of the work until it reaches a stopping point called the base case.",
            "standard": "A recursive solution needs a base case to stop and a recursive case that moves toward that base case.",
            "analogy": "Opening nested boxes: each box contains a smaller box until you reach the final empty box.",
            "example": "factorial(4) = 4 * factorial(3), then 3 * factorial(2), until factorial(1) returns 1.",
            "technical": "Each recursive call is stored on the call stack. If the base case is missing, recursion can continue until stack overflow.",
            "operations": "- define base case\n- reduce input\n- call the same function\n- combine the returned result",
            "complexity": "Depends on the recurrence; factorial is O(n) time and O(n) call stack space.",
            "uses": "Tree traversal, DFS, divide and conquer, backtracking.",
            "code_example": (
                "def factorial(n):\n"
                "    if n == 1:\n"
                "        return 1\n"
                "    return n * factorial(n - 1)\n\n"
                "print(factorial(4))"
            ),
            "code_output": "24",
            "code_walkthrough": (
                "1. `factorial(4)` is not the base case, so it becomes `4 * factorial(3)`.\n"
                "2. `factorial(3)` becomes `3 * factorial(2)`.\n"
                "3. `factorial(2)` becomes `2 * factorial(1)`.\n"
                "4. `factorial(1)` hits the base case and returns `1`.\n"
                "5. The answers return upward: `2 * 1 = 2`, `3 * 2 = 6`, and `4 * 6 = 24`."
            ),
            "interview_points": (
                "- Every recursive solution needs a base case.\n"
                "- Each call should move toward that base case.\n"
                "- Recursion uses call stack space, so space complexity matters too."
            ),
            "common_mistakes": (
                "- Forgetting the base case.\n"
                "- Reducing the problem incorrectly so recursion never ends.\n"
                "- Ignoring stack overflow risk on very deep inputs."
            ),
            "key_points": "- Must have a base case\n- Input should become smaller\n- Uses call stack memory",
            "takeaway": "Recursion is powerful when a problem naturally breaks into smaller similar problems.",
        },
        "binary search": {
            "title": "Binary Search",
            "definition": "Binary search finds an item in a sorted list by repeatedly halving the search range.",
            "simple_definition": "Binary search quickly finds a value by checking the middle and discarding half the list.",
            "simple": "Look at the middle. If the target is smaller, search left. If bigger, search right.",
            "standard": "Binary search works only when data is sorted. It compares the target with the middle element and narrows the range.",
            "analogy": "Guessing a number from 1 to 100: each guess cuts the possible range in half.",
            "example": "To find 7 in [1, 3, 5, 7, 9], check 5, then search the right half and find 7.",
            "technical": "Maintain low and high pointers, compute mid, compare arr[mid], and update the search boundary.",
            "operations": "- low = 0, high = n - 1\n- mid = (low + high) // 2\n- compare target with arr[mid]\n- move low or high",
            "complexity": "O(log n) time and O(1) space for iterative binary search.",
            "uses": "Searching sorted arrays, lower/upper bound problems, optimization by answer.",
            "code_example": (
                "def binary_search(arr, target):\n"
                "    low = 0\n"
                "    high = len(arr) - 1\n\n"
                "    while low <= high:\n"
                "        mid = (low + high) // 2\n\n"
                "        if arr[mid] == target:\n"
                "            return mid\n"
                "        if arr[mid] < target:\n"
                "            low = mid + 1\n"
                "        else:\n"
                "            high = mid - 1\n\n"
                "    return -1\n\n"
                "numbers = [1, 3, 5, 7, 9]\n"
                "print(binary_search(numbers, 7))"
            ),
            "code_output": "3",
            "code_walkthrough": (
                "1. `low` starts at index `0` and `high` starts at index `4`.\n"
                "2. `mid` becomes `2`, so we compare `arr[2]`, which is `5`, with the target `7`.\n"
                "3. Because `5` is smaller than `7`, the target must be on the right side, so `low` becomes `3`.\n"
                "4. Now `mid` becomes `3`, and `arr[3]` is `7`.\n"
                "5. The function returns index `3`, which is where the target was found."
            ),
            "interview_points": (
                "- Binary search works only on sorted data.\n"
                "- Time complexity is O(log n) because the search space is halved each step.\n"
                "- Off-by-one handling with `low`, `high`, and `mid` is a common interview focus."
            ),
            "common_mistakes": (
                "- Trying to use binary search on an unsorted array.\n"
                "- Updating `low` or `high` incorrectly and causing an infinite loop.\n"
                "- Returning the wrong index because of off-by-one errors."
            ),
            "key_points": "- Requires sorted data\n- Cuts search space in half\n- Much faster than linear search for large sorted lists",
            "takeaway": "Binary search is best when the data is sorted and you need fast lookup.",
        },
    }

    if key in concepts:
        return {"concept_key": key, **concepts[key]}

    title = " ".join(word.capitalize() for word in topic.split()) or "Concept"
    return {
        "concept_key": key,
        "title": title,
        "definition": f"{title} is a computer science concept that should be understood through its meaning, working idea, use cases, and limits.",
        "simple_definition": f"{title} is the idea you are trying to learn, so start by understanding what problem it solves.",
        "simple": f"Learn {title} in small steps: what it means, how it works, and where it is useful.",
        "standard": f"To study {title} well, connect the definition to the process it follows and one concrete use case.",
        "analogy": f"Think of {title} like learning a new tool: first understand what job it does, then see it in action on a small example.",
        "example": f"A good way to study {title} is to trace one tiny example by hand and then test one edge case.",
        "technical": f"For {title}, pay attention to the exact rule, the data it works on, the steps it follows, and the edge cases that can break a naive understanding.",
        "operations": "- identify the input\n- apply the core rule\n- trace the output\n- check edge cases",
        "complexity": "Complexity depends on the exact algorithm or implementation.",
        "uses": "Used when its rules match the problem requirements.",
        "code_example": "",
        "code_output": "",
        "code_walkthrough": "",
        "interview_points": (
            "- Know the definition clearly.\n"
            "- Be ready to explain where it is useful.\n"
            "- Practice tracing a small example by hand."
        ),
        "common_mistakes": (
            "- Memorizing the term without understanding the flow.\n"
            "- Skipping examples and edge cases.\n"
            "- Using the concept in situations where its assumptions do not hold."
        ),
        "key_points": f"- Know what {title} means\n- Understand how it works step by step\n- Connect it to one concrete use case",
        "takeaway": f"You understand {title} best when you connect the idea to one worked example and one edge case.",
    }


def _fallback_feedback(topic: str, score: int, weak_area: str, level: str, language: str) -> str:
    cleaned_topic = topic.strip() or "this topic"
    normalized_language = normalize_language(language)
    if normalized_language == "Hindi":
        if weak_area and weak_area != "none":
            return (
                f"आपने {cleaned_topic} में {score}% स्कोर किया। अगला फोकस {weak_area} पर रखें "
                f"और {level} स्तर के छोटे उदाहरणों से अभ्यास करें।"
            )

        return (
            f"आपने {cleaned_topic} में {score}% स्कोर किया। अच्छी प्रगति है; अब थोड़ा कठिन "
            f"{level} अभ्यास करके mastery मजबूत करें।"
        )

    if normalized_language == "Hinglish":
        if weak_area and weak_area != "none":
            return (
                f"You scored {score}% on {cleaned_topic}. Ab {weak_area} par focus karo, "
                f"then {level} level ke small examples practice karo."
            )

        return (
            f"You scored {score}% on {cleaned_topic}. Good progress; ab thode harder "
            f"{level} questions practice karo to strengthen mastery."
        )

    if weak_area and weak_area != "none":
        return (
            f"You scored {score}% on {cleaned_topic}. Focus next on {weak_area}, "
            f"then try a few smaller examples at {level} level."
        )

    return (
        f"You scored {score}% on {cleaned_topic}. Good progress; keep practicing with "
        f"slightly harder {level} questions to strengthen mastery."
    )
