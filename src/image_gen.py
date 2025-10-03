"""Image generation utilities backed by Hugging Face diffusers."""
from __future__ import annotations

import base64
import logging
import textwrap
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

try:
    import torch
except Exception:  # pragma: no cover - minimal environments without torch
    class _TorchStub:
        float32 = "float32"

        class _Cuda:
            @staticmethod
            def is_available() -> bool:
                return False

        cuda = _Cuda()

    torch = _TorchStub()  # type: ignore


try:
    from diffusers import StableDiffusionPipeline
except Exception:  # pragma: no cover - diffusers optional for fallback mode
    StableDiffusionPipeline = None  # type: ignore


try:  # Pillow is optional thanks to encoded placeholder fallbacks.
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - occurs on minimal environments
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore


logger = logging.getLogger(__name__)


PIPELINE_ID = "stabilityai/stable-diffusion-2-1-base"

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_PATH = (BASE_DIR / "static" / "out.png").resolve()


@lru_cache(maxsize=1)
def get_T2I_pipeline() -> "StableDiffusionPipeline":
    """Instantiate the Stable Diffusion pipeline on the CPU."""

    if StableDiffusionPipeline is None:
        raise RuntimeError("diffusers is not installed. Unable to load Stable Diffusion pipeline.")

    pipe = StableDiffusionPipeline.from_pretrained(
        PIPELINE_ID,
        torch_dtype=torch.float32,
    )
    pipe.to("cpu")
    return pipe


def _resolve_device(requested_device: Optional[str]) -> str:
    """Return a valid torch device string, selecting GPU automatically when possible."""
    if requested_device in (None, "", "auto"):
        if getattr(torch, "cuda", None) and torch.cuda.is_available():
            return "cuda:0"
        return "cpu"

    if requested_device != "cpu" and getattr(torch, "cuda", None):
        if torch.cuda.is_available():
            return requested_device
        logger.warning("CUDA requested but not available. Falling back to CPU.")

    return "cpu"


def _ensure_output_path(path: Path) -> Path:
    """Create parent directories for the output path if needed."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _save_first_image(images: List, output_path: Path) -> Optional[Path]:
    """Persist the first PIL image from the list to disk as PNG."""
    if not images:
        return None
    image = images[0]
    try:
        image.save(output_path, format="PNG")
        return output_path
    except Exception as exc:  # pragma: no cover - pillow level errors are rare
        logger.error("Failed to save generated image: %s", exc, exc_info=True)
        return None


PLACEHOLDER_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PVqSxwAAAABJRU5ErkJggg=="
)


def _placeholder_image(prompt: str, output_path: Path) -> Path:
    """Generate a simple placeholder PNG when Stable Diffusion is unavailable."""
    if Image is None or ImageDraw is None or ImageFont is None:
        output_path.write_bytes(base64.b64decode(PLACEHOLDER_PNG))
        return output_path

    width, height = 1024, 1024
    image = Image.new("RGB", (width, height), color="#1f2933")
    draw = ImageDraw.Draw(image)
    title = "Stable Diffusion placeholder"
    wrapped_prompt = textwrap.fill(prompt, width=40)
    message = f"{title}\n\n{wrapped_prompt}"

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", size=36)
    except Exception:  # pragma: no cover - default font fallback
        font = ImageFont.load_default()

    text_bbox = draw.multiline_textbbox((0, 0), message, font=font, align="center")
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((width - text_width) / 2, (height - text_height) / 2)
    draw.multiline_text(position, message, font=font, fill="#f8fafc", align="center")

    image.save(output_path, format="PNG")
    return output_path


def _generate_with_sd(prompt: str, output_path: Path, device: str) -> Optional[Path]:
    try:
        pipeline = get_T2I_pipeline()
    except Exception as exc:  # pragma: no cover - triggered when diffusers unavailable
        logger.error("Failed to load Stable Diffusion pipeline: %s", exc, exc_info=True)
        return None

    try:
        pipeline.to(device)
        images = pipeline(
            prompt=prompt,
            num_inference_steps=25,
            guidance_scale=7.5,
        ).images
    except Exception as exc:  # pragma: no cover - pipeline failures depend on env
        logger.error("Stable Diffusion pipeline failed: %s", exc, exc_info=True)
        return None

    saved_path = _save_first_image(images, output_path)
    if saved_path is None:
        logger.error("Stable Diffusion pipeline did not return any images.")
    return saved_path


def generate_image(prompt: str, device: Optional[str] = "auto") -> str:
    """Generate an image and persist it to the default static output path."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string.")

    output_file = _ensure_output_path(DEFAULT_OUTPUT_PATH)
    if device is not None and not isinstance(device, str):
        raise ValueError("device must be a string identifier or None.")

    selected_device = _resolve_device(device)

    generated_path = _generate_with_sd(prompt, output_file, selected_device)
    if generated_path is not None:
        return str(generated_path)

    logger.info("Using placeholder image generator due to Stable Diffusion unavailability.")
    placeholder_path = _placeholder_image(prompt, output_file)
    return str(placeholder_path)
