# Auto Content Factory – AGENTS.md

## Overview
Goal: Local desktop pipeline that generates social content automatically.
Flow: Topic → Text Prompt → Kandinsky Image → Video Stitch → Post to Socials.

Each agent works in its own branch, submits a PR, then Stitcher merges.

---

## Agents

### Agent 1: Prompt Generator
- File: `src/llm_prompt.py`
- Task: Produce catchy post ideas from input topic.
- Use OpenAI API (gpt-4o-mini) with .env key.
- Expose `make_prompt(topic: str) -> str`.

### Agent 2: Image Generator
- File: `src/image_gen.py`
- Task: Wrap the Hugging Face Kandinsky pipeline (`get_T2I_pipeline`) to produce PNG from text.
- Save file path and return.
- Expose `generate_image(prompt: str, output_path: str) -> str`.

### Agent 3: Video Composer
- File: `src/video_gen.py`
- Task: Convert list of images into a short mp4 using ffmpeg.
- No GUI, purely ffmpeg call.
- Expose `stitch_video(images: list[str], output: str) -> str`.

### Agent 4: Posting Layer
- File: `src/post_api.py`
- Task: Implement posting to Facebook + placeholder for Twitter/Instagram.
- Must read tokens from `.env`.
- Expose `post_to_facebook(text: str, image_path: str) -> dict`.

### Agent 5: Orchestrator
- File: `src/main.py`
- Task: Glue all agents together.
- Input: topic string.
- Pipeline: make_prompt → generate_image → stitch_video → post_to_facebook.
- Print result JSON to console.

---

## Stitcher Agent
- Merge all PRs.
- Ensure import paths correct.
- Verify `python src/main.py` runs end-to-end.
- Run `pip install -r requ
