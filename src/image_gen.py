"""Image generation utilities built around Kandinsky-3 with resilient fallbacks."""
from __future__ import annotations

import base64
import logging
import sys
import textwrap
from pathlib import Path
from typing import List, Optional

try:
    import torch
except Exception:  # pragma: no cover - minimal environments without torch
    class _TorchStub:
        float16 = "float16"
        float32 = "float32"

        class _Cuda:
            @staticmethod
            def is_available() -> bool:
                return False

        cuda = _Cuda()

    torch = _TorchStub()  # type: ignore


try:  # Pillow is optional thanks to encoded placeholder fallbacks.
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - occurs on minimal environments
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore


logger = logging.getLogger(__name__)


ROOT_DIR = Path(__file__).resolve().parents[1]
KANDINSKY_SRC = ROOT_DIR / "kandinsky3_src"
if KANDINSKY_SRC.is_dir():  # Make the locally cloned repo importable.
    sys.path.insert(0, str(KANDINSKY_SRC))
else:
    logger.warning(
        "kandinsky3_src directory not found. Falling back to placeholder image generation."
    )

try:  # Import lazily so the module continues to work when Kandinsky is absent.
    from kandinsky3 import get_T2I_pipeline  # type: ignore
except Exception:  # pragma: no cover - best effort fallback
    get_T2I_pipeline = None  # type: ignore
    logger.warning(
        "Unable to import kandinsky3.get_T2I_pipeline. Placeholder images will be used."
    )


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
    """Generate a simple placeholder PNG when Kandinsky is unavailable."""
    if Image is None or ImageDraw is None or ImageFont is None:
        output_path.write_bytes(base64.b64decode(PLACEHOLDER_PNG))
        return output_path

    width, height = 1024, 1024
    image = Image.new("RGB", (width, height), color="#1f2933")
    draw = ImageDraw.Draw(image)
    title = "Kandinsky placeholder"
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


def _generate_with_kandinsky(prompt: str, output_path: Path, device: str) -> Optional[Path]:
    if get_T2I_pipeline is None:
        return None

    dtype_map = {
        "unet": torch.float16 if device != "cpu" else torch.float32,
        "text_encoder": torch.float16 if device != "cpu" else torch.float32,
        "movq": torch.float32,
    }

    try:
        pipeline = get_T2I_pipeline(device=device, dtype_map=dtype_map)
        images = pipeline.generate_text2img(prompt=prompt, batch_size=1)
    except Exception as exc:  # pragma: no cover - pipeline failures depend on env
        logger.error("Kandinsky pipeline failed: %s", exc, exc_info=True)
        return None

    saved_path = _save_first_image(images, output_path)
    if saved_path is None:
        logger.error("Kandinsky pipeline did not return any images.")
    return saved_path


def generate_image(
    prompt: str, output_path: str, device: Optional[str] = "auto"
) -> str:
    """Generate an image using Kandinsky-3 and persist it to ``output_path``."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string.")
    if not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("output_path must be a non-empty string path.")

    output_file = _ensure_output_path(Path(output_path).expanduser().resolve())
    if device is not None and not isinstance(device, str):
        raise ValueError("device must be a string identifier or None.")

    selected_device = _resolve_device(device)

    generated_path = _generate_with_kandinsky(prompt, output_file, selected_device)
    if generated_path is not None:
        return str(generated_path)

    logger.info("Using placeholder image generator due to Kandinsky unavailability.")
    placeholder_path = _placeholder_image(prompt, output_file)
    return str(placeholder_path)
