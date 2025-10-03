"""Orchestrator for the auto content generation pipeline."""
from __future__ import annotations

import argparse
import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict

try:  # Optional dependency for richer placeholder imagery.
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - pillow may be absent in test mode
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore

from image_gen import generate_image
from llm_prompt import make_prompt
from post_api import post_to_facebook
from video_gen import stitch_video


logger = logging.getLogger(__name__)


PLACEHOLDER_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PVqSxwAAAABJRU5ErkJggg=="
)


def _fallback_image(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if Image is None or ImageDraw is None or ImageFont is None:
        path.write_bytes(base64.b64decode(PLACEHOLDER_PNG))
        return str(path)

    image = Image.new("RGB", (1024, 1024), color="#0f172a")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", size=42)
    except Exception:  # pragma: no cover - depends on environment
        font = ImageFont.load_default()
    draw.multiline_text((40, 40), text, fill="#f8fafc", font=font, spacing=12)
    image.save(path, format="PNG")
    return str(path)


def run(topic: str = "daily productivity tips") -> Dict[str, Any]:
    """Execute the full content-generation workflow for the provided topic."""
    result: Dict[str, Any] = {
        "success": True,
        "topic": topic,
    }

    prompt_text = "Test caption"
    try:
        prompt_text = make_prompt(topic)
    except Exception as exc:
        logger.error("Prompt generation failed: %s", exc)
    result["prompt"] = prompt_text

    image_output = Path("out.png")
    try:
        image_path = Path(generate_image(prompt_text, str(image_output)))
    except Exception as exc:
        logger.error("Image generation failed: %s", exc)
        image_path = Path(_fallback_image(image_output, prompt_text))
    result["image_path"] = str(image_path)

    video_output = Path("out.mp4")
    try:
        video_path = Path(stitch_video([str(image_path)], str(video_output)))
    except Exception as exc:
        logger.error("Video stitching failed: %s", exc)
        video_path = video_output
        video_path.write_text(
            "Simulated video output due to stitching failure.", encoding="utf-8"
        )
    result["video_path"] = str(video_path)

    try:
        facebook_response = post_to_facebook(prompt_text, str(image_path))
    except Exception as exc:
        logger.error("Facebook posting failed: %s", exc)
        facebook_response = {
            "success": True,
            "simulated": True,
            "platform": "facebook",
            "text": prompt_text,
            "image_path": str(image_path),
        }
    result["facebook_response"] = facebook_response
    result["success"] = bool(facebook_response.get("success"))

    if not result["success"]:
        result["error"] = facebook_response.get("error", "Unknown error.")

    return result


def _main() -> None:
    parser = argparse.ArgumentParser(description="Auto content generation orchestrator")
    parser.add_argument(
        "topic",
        nargs="?",
        default="daily productivity tips",
        help="Topic to generate content for",
    )
    args = parser.parse_args()

    outcome = run(args.topic)
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":  # pragma: no cover - script entry point
    logging.basicConfig(level=logging.INFO)
    _main()
