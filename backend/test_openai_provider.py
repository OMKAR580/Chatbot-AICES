"""Small OpenAI provider smoke test for local backend diagnostics."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.ai_service import get_openai_model


PROXY_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


def _load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def _clear_proxy_environment() -> None:
    for key in PROXY_KEYS:
        os.environ.pop(key, None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the configured OpenAI provider.")
    parser.add_argument(
        "--ignore-proxy",
        action="store_true",
        help="Temporarily clear proxy environment variables before calling OpenAI.",
    )
    args = parser.parse_args()

    _load_environment()
    if args.ignore_proxy:
        _clear_proxy_environment()

    configured_proxies = {key: os.getenv(key) for key in PROXY_KEYS if os.getenv(key)}
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = get_openai_model()

    print(f"OPENAI_API_KEY={'configured' if api_key else 'missing'}")
    print(f"OPENAI_MODEL={model_name}")
    print(f"PROXY_VARS={configured_proxies or 'none'}")

    if not api_key:
        print("RESULT=error")
        print("ERROR_TYPE=MissingAPIKey")
        print("ERROR_MESSAGE=OPENAI_API_KEY is not set.")
        return 1

    client = OpenAI(api_key=api_key)
    print(f"BASE_URL={client.base_url}")

    try:
        response = client.responses.create(
            model=model_name,
            input="Reply with exactly OK.",
        )
    except Exception as exc:
        print("RESULT=error")
        print(f"ERROR_TYPE={type(exc).__name__}")
        print(f"ERROR_MESSAGE={exc}")
        cause = getattr(exc, "__cause__", None)
        if cause is not None:
            print(f"CAUSE_TYPE={type(cause).__name__}")
            print(f"CAUSE_MESSAGE={cause}")
        return 1

    print("RESULT=success")
    print(f"OUTPUT={(response.output_text or '').strip()!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
