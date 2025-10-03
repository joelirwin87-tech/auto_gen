# Auto Content Factory

A local-first pipeline that turns a topic into a social media package consisting of a generated prompt, an AI-created image, a short video clip, and a simulated social post. The project is designed to run without real API credentials while still allowing you to plug them in later for live publishing.

## Project Structure

- `src/llm_prompt.py` – builds a caption using OpenAI (with a graceful fallback when the API is unavailable).
- `src/image_gen.py` – generates an image via a locally cloned copy of Kandinsky-3 or a placeholder fallback.
- `src/video_gen.py` – stitches one or more images into an MP4 clip with ffmpeg, simulating the result if ffmpeg cannot run.
- `src/post_api.py` – simulates posting to Facebook and can be extended to real API calls when credentials are available.
- `src/main.py` – orchestrates the full workflow.

## Prerequisites

1. **Clone Kandinsky-3 locally**

   ```bash
   git clone https://github.com/ai-forever/Kandinsky-3.git kandinsky3_src
   ```

   The repository must live next to this README so the image generator can import the pipeline implementation. If you cannot or do not want to clone the repository, the pipeline will fall back to generating a simple placeholder image instead.

2. **Set up a virtual environment and install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment variables**

   Copy `.env.example` to `.env` and populate it with any real credentials you want to use. When keys are missing, the system will operate entirely in local test mode.

   ```bash
   cp .env.example .env
   ```

## Running the Pipeline Locally

Run the orchestrator with a topic string. Without valid API keys or Kandinsky-3 installed, the run will still succeed using simulated fallbacks.

```bash
python src/main.py "future of remote work"
```

On success you will see:

- `out.png` – the generated (or placeholder) image.
- `out.mp4` – a video stitched from the image.
- Console output showing the simulated Facebook post payload.

## Using Real APIs Later

- **OpenAI**: Set `OPENAI_API_KEY` in `.env`. The prompt generator will automatically switch from the fallback caption to live completions.
- **Facebook**: Provide `FB_PAGE_TOKEN` in `.env`. The posting module will attempt a real request and surface the API response.
- **Other networks**: Extend `src/post_api.py` with real implementations. The current structure is modular to keep integrations isolated and easy to test.

## Troubleshooting

- If Kandinsky-3 generation fails, inspect the console logs. The module will explain why it fell back to a placeholder image.
- Ensure `ffmpeg` is installed and available on your PATH to get a real MP4. Without it, the pipeline emits a simulated clip file so downstream steps still succeed.
- Run `python src/main.py --help` for additional CLI usage details.
