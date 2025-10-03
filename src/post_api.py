"""Posting layer integrations for social media APIs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()

_FACEBOOK_API_URL = "https://graph.facebook.com/me/photos"


def _load_token(env_key: str) -> str | None:
    """Fetch a token from the environment, returning ``None`` when missing."""
    token = os.getenv(env_key)
    return token.strip() if token else None


def post_to_facebook(text: str, image_path: str) -> Dict[str, Any]:
    """Post an image with a caption to Facebook using the Graph API.

    Args:
        text: Caption text for the post.
        image_path: File system path to the image to upload.

    Returns:
        A dictionary representing the JSON response or an error payload.
    """
    access_token = _load_token("FB_PAGE_TOKEN")
    if not access_token:
        return {
            "success": False,
            "error": "Facebook page token missing. Set FB_PAGE_TOKEN in the environment.",
        }

    path_obj = Path(image_path)
    if not path_obj.is_file():
        return {
            "success": False,
            "error": f"Image file not found at '{image_path}'.",
        }

    data = {"caption": text, "access_token": access_token}
    try:
        with path_obj.open("rb") as image_file:
            files = {
                "source": (path_obj.name, image_file, "application/octet-stream"),
            }
            response = requests.post(
                _FACEBOOK_API_URL,
                data=data,
                files=files,
                timeout=30,
            )
    except OSError as exc:
        return {
            "success": False,
            "error": f"Unable to read image file: {exc}",
        }
    except requests.RequestException as exc:
        return {
            "success": False,
            "error": f"Failed to contact Facebook API: {exc}",
        }

    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_response": response.text}

    if response.status_code >= 400:
        return {
            "success": False,
            "error": "Facebook API returned an error.",
            "status_code": response.status_code,
            "response": payload,
        }

    if isinstance(payload, dict):
        payload.setdefault("success", True)
        return payload

    return {
        "success": False,
        "error": "Unexpected response format from Facebook API.",
        "response": payload,
    }


def post_to_twitter(text: str) -> Dict[str, Any]:
    """Placeholder implementation for posting to Twitter."""
    token = _load_token("TWITTER_BEARER_TOKEN")
    if not token:
        return {
            "success": False,
            "error": "Twitter token missing. Set TWITTER_BEARER_TOKEN in the environment.",
        }

    print(f"[Twitter Placeholder] Would post: {text}")
    return {
        "success": True,
        "message": "Twitter posting is not yet implemented.",
    }
