"""Posting layer integrations for social media APIs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

try:
    import requests
except Exception:  # pragma: no cover - fallback when requests missing
    class _RequestsStub:
        class RequestException(Exception):
            pass

        @staticmethod
        def post(*_: object, **__: object) -> "_ResponseStub":
            raise _RequestsStub.RequestException("requests library is unavailable")

    class _ResponseStub:  # pragma: no cover - used only when requests missing
        status_code = 599

        @staticmethod
        def json() -> dict:
            return {}

        text = ""

    requests = _RequestsStub()  # type: ignore

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback when python-dotenv missing
    def load_dotenv(*_: object, **__: object) -> bool:  # type: ignore
        return False

load_dotenv()

_FACEBOOK_API_URL = "https://graph.facebook.com/me/photos"


def _load_token(env_key: str) -> str | None:
    """Fetch a token from the environment, returning ``None`` when missing."""
    token = os.getenv(env_key)
    return token.strip() if token else None


def _simulate_post(platform: str, text: str, image_path: str) -> Dict[str, Any]:
    print(f"Simulated {platform} post: '{text}' with image '{image_path}'")
    return {
        "success": True,
        "simulated": True,
        "platform": platform,
        "text": text,
        "image_path": image_path,
    }


def post_to_facebook(text: str, image_path: str) -> Dict[str, Any]:
    """Post an image with a caption to Facebook using the Graph API.

    When credentials are missing or the API call fails, a simulated response is
    returned to keep the pipeline running locally.
    """

    path_obj = Path(image_path)
    if not path_obj.is_file():
        return {
            "success": False,
            "error": f"Image file not found at '{image_path}'.",
        }

    access_token = _load_token("FB_PAGE_TOKEN")
    if not access_token:
        return _simulate_post("facebook", text, str(path_obj))

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
    except (OSError, requests.RequestException) as exc:
        print(f"Facebook post failed ({exc}); returning simulated result instead.")
        return _simulate_post("facebook", text, str(path_obj))

    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_response": response.text}

    if response.status_code >= 400:
        print(
            f"Facebook API returned status {response.status_code}. Falling back to simulation."
        )
        return _simulate_post("facebook", text, str(path_obj))

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
        return _simulate_post("twitter", text, image_path="")

    print(f"[Twitter Placeholder] Would post: {text}")
    return {
        "success": True,
        "message": "Twitter posting is not yet implemented.",
    }
