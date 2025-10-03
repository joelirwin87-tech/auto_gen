"""Flask application exposing a simple text-to-image demo."""
from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import Optional

from flask import Flask, render_template, request, url_for

from image_gen import generate_image


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DEFAULT_IMAGE = STATIC_DIR / "out.png"


def _ensure_static_dir(path: Path) -> Path:
    """Guarantee that the static directory exists before writes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


_ensure_static_dir(DEFAULT_IMAGE)

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(STATIC_DIR),
)
app.config["TEMPLATES_AUTO_RELOAD"] = True

logger = logging.getLogger(__name__)


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    """Render the home page, generating an image when the form is submitted."""
    prompt_value = ""
    image_url: Optional[str] = None
    error_message: Optional[str] = None

    if request.method == "POST":
        prompt_value = request.form.get("prompt", "").strip()
        if not prompt_value:
            error_message = "Please provide a prompt before generating an image."
        else:
            try:
                generated_path = Path(generate_image(prompt_value))
                if not generated_path.exists():
                    raise FileNotFoundError(generated_path)

                if generated_path.resolve() != DEFAULT_IMAGE.resolve():
                    try:
                        shutil.copy2(generated_path, DEFAULT_IMAGE)
                        image_path = DEFAULT_IMAGE
                    except Exception as copy_error:
                        raise RuntimeError(
                            f"Failed to copy generated file to {DEFAULT_IMAGE}"
                        ) from copy_error
                else:
                    image_path = generated_path
                # Bust browser cache by appending timestamp query parameter.
                cache_buster = int(time.time())
                image_url = url_for("static", filename=image_path.name) + f"?v={cache_buster}"
            except Exception as exc:  # pragma: no cover - runtime feedback for UI
                logger.exception("Stable Diffusion image generation failed: %s", exc)
                error_message = "Unable to generate image. Please try again."

    # Display the most recent image even when the request is GET only.
    if image_url is None and DEFAULT_IMAGE.exists():
        cache_buster = int(time.time())
        image_url = url_for("static", filename=DEFAULT_IMAGE.name) + f"?v={cache_buster}"

    return render_template(
        "index.html",
        prompt_value=prompt_value,
        image_url=image_url,
        error_message=error_message,
    )


@app.route("/health", methods=["GET"])
def healthcheck() -> tuple[str, int]:
    """Simple health endpoint useful for diagnostics."""
    return "ok", 200


if __name__ == "__main__":  # pragma: no cover - CLI execution
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000, debug=False)
