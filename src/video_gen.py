"""Video composition utilities leveraging ffmpeg."""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import List


def stitch_video(images: List[str], output: str = "output.mp4") -> str:
    """Stitch a sequence of still images into a single mp4 clip.

    Each image is displayed for 3 seconds. The resulting video is encoded using
    H.264 via ffmpeg. Raises an :class:`Exception` if ffmpeg is missing or the
    process fails for any reason.

    Args:
        images: Paths to the image files in the desired presentation order.
        output: Destination path for the generated mp4 file.

    Returns:
        The absolute path to the generated video file.

    Raises:
        ValueError: If ``images`` is empty or any provided image path is
            invalid.
        Exception: If ffmpeg is unavailable or the subprocess exits with a
            non-zero status.
    """

    if not images:
        raise ValueError("images must contain at least one file path")

    image_paths = [Path(path).expanduser().resolve() for path in images]
    for image_path in image_paths:
        if not image_path.is_file():
            raise ValueError(f"Image file not found: {image_path}")

    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command: List[str] = ["ffmpeg", "-y"]

    for image_path in image_paths:
        command.extend(["-loop", "1", "-t", "3", "-i", str(image_path)])

    stream_refs = ''.join(f"[{idx}:v]" for idx in range(len(image_paths)))
    filter_complex = f"{stream_refs}concat=n={len(image_paths)}:v=1:a=0[v]"

    command.extend([
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ])

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:  # pragma: no cover - dependent on environment
        raise Exception("ffmpeg executable not found. Please install ffmpeg to stitch videos.") from exc
    except subprocess.CalledProcessError as exc:
        stderr_output = exc.stderr.decode(errors="replace") if exc.stderr else ""
        raise Exception(f"ffmpeg failed with exit code {exc.returncode}: {stderr_output}") from exc

    return str(output_path)
