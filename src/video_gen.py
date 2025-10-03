"""Video composition utilities leveraging ffmpeg with graceful fallbacks."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List


def _simulate_video(output_path: Path, source_image: Path) -> Path:
    """Create a lightweight placeholder video file when ffmpeg is unavailable."""
    placeholder_text = (
        "Simulated video output. Install ffmpeg to generate real footage from the source image.\n"
        f"Source image: {source_image}\n"
    )
    output_path.write_text(placeholder_text, encoding="utf-8")
    return output_path


def stitch_video(images: List[str], output: str = "output.mp4") -> str:
    """Stitch a sequence of still images into a single mp4 clip.

    When ffmpeg is unavailable the function produces a simulated clip so the
    pipeline can keep running in local test mode.
    """

    if not images:
        raise ValueError("images must contain at least one file path")

    image_paths = [Path(path).expanduser().resolve() for path in images]
    for image_path in image_paths:
        if not image_path.is_file():
            raise ValueError(f"Image file not found: {image_path}")

    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_binary = shutil.which("ffmpeg")
    if not ffmpeg_binary:
        return str(_simulate_video(output_path, image_paths[0]))

    command: List[str] = [ffmpeg_binary, "-y"]

    for image_path in image_paths:
        command.extend(["-loop", "1", "-t", "3", "-i", str(image_path)])

    stream_refs = "".join(f"[{idx}:v]" for idx in range(len(image_paths)))
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
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        stderr_output = exc.stderr.decode(errors="replace") if exc.stderr else ""
        print(f"ffmpeg failed ({stderr_output}). Writing simulated clip instead.")
        return str(_simulate_video(output_path, image_paths[0]))

    return str(output_path)
