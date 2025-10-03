"""Orchestrator for the auto content generation pipeline."""
from __future__ import annotations

import json
from typing import Any, Dict

from image_gen import generate_image
from llm_prompt import make_prompt
from post_api import post_to_facebook
from video_gen import stitch_video


def run(topic: str = "daily productivity tips") -> None:
    """Execute the full content-generation workflow for the provided topic."""
    result: Dict[str, Any]
    try:
        prompt_text = make_prompt(topic)
        image_output = "out.png"
        video_output = "out.mp4"

        image_path = generate_image(prompt_text, image_output)
        video_path = stitch_video([image_output], video_output)
        facebook_response = post_to_facebook(prompt_text, image_output)

        result = {
            "success": bool(facebook_response.get("success")),
            "topic": topic,
            "prompt": prompt_text,
            "image_path": image_path,
            "video_path": video_path,
            "facebook_response": facebook_response,
        }

        if not facebook_response.get("success"):
            result.setdefault("error", facebook_response.get("error", "Unknown error."))
    except Exception as exc:  # pragma: no cover - defensive safeguard
        result = {"success": False, "error": str(exc)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover - script entry point
    run()
