"""Prompt generator module leveraging OpenAI's chat completions API."""
from __future__ import annotations

import os
import sys
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def _create_client() -> OpenAI:
    """Instantiate an OpenAI client with the API key from the environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception(
            "Missing OPENAI_API_KEY environment variable. Please add it to your .env file."
        )
    return OpenAI(api_key=api_key)


CLIENT_INIT_ERROR: Optional[Exception] = None
try:
    CLIENT = _create_client()
except Exception as error:  # Preserve initialization errors for later reporting.
    CLIENT = None
    CLIENT_INIT_ERROR = error


def make_prompt(topic: str) -> str:
    """Generate a catchy social media post idea for the provided topic."""
    if CLIENT is None:
        # Re-raise the initialization error or a generic message if unavailable.
        raise CLIENT_INIT_ERROR or Exception(
            "OpenAI client is not initialized due to missing API key."
        )

    if not isinstance(topic, str):
        raise TypeError("Topic must be a string.")

    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("Topic cannot be empty.")

    fallback = f"Share an engaging social media post inspired by {normalized_topic}."

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

        if not response.choices:
            return fallback

        content = response.choices[0].message.content
        if not content:
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
