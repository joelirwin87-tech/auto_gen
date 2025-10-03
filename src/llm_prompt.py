"""Prompt generator module leveraging OpenAI's chat completions API."""
from __future__ import annotations

import os
import sys
from typing import Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback when python-dotenv missing
    def load_dotenv(*_: object, **__: object) -> bool:  # type: ignore
        return False

try:  # Lazy import so the module still works without openai installed.
    from openai import OpenAI
except Exception:  # pragma: no cover - defensive guard for environments missing openai
    OpenAI = None  # type: ignore


load_dotenv()


DEFAULT_FALLBACK = "Test caption"


def _create_client() -> Optional[OpenAI]:
    """Instantiate an OpenAI client with the API key from the environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as exc:  # pragma: no cover - library level failure
        print(f"Failed to initialise OpenAI client: {exc}")
        return None


CLIENT: Optional[OpenAI] = _create_client()


def make_prompt(topic: str) -> str:
    """Generate a catchy social media post idea for the provided topic."""
    if not isinstance(topic, str):
        raise TypeError("Topic must be a string.")

    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("Topic cannot be empty.")

    fallback = DEFAULT_FALLBACK

    if CLIENT is None:
        return fallback

    try:
        response = CLIENT.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"Create a catchy social media post idea about {normalized_topic}",
                }
            ],
        )

        if not getattr(response, "choices", None):
            return fallback

        choice = response.choices[0]
        message = getattr(choice, "message", None)
        content = getattr(message, "content", None)
        if not isinstance(content, str):
            return fallback

        return content.strip() or fallback
    except Exception as error:  # Broad catch to ensure resilience against API issues.
        print(f"Failed to generate prompt via OpenAI: {error}")
        return fallback


def _main() -> None:
    """CLI entry point for quick manual testing."""
    topic_arg = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not topic_arg:
        print("Usage: python src/llm_prompt.py <topic>")
        sys.exit(1)

    prompt = make_prompt(topic_arg)
    print(prompt)


if __name__ == "__main__":
    _main()
