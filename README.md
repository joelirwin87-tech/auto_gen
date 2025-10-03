# Auto Content Factory

The Auto Content Factory turns a topic into a lightweight social media package: a generated caption, an AI-created image, a short MP4 clip, and a simulated Facebook post. Every component has graceful fallbacks so the project can run end-to-end on a fresh machine.

## Project Structure

- `src/llm_prompt.py` – builds a caption using OpenAI with a local fallback message.
- `src/image_gen.py` – generates an image using the Hugging Face Stable Diffusion 2.1 base pipeline (or a placeholder if the model cannot load).
- `src/video_gen.py` – stitches still images into an MP4 clip using `ffmpeg`, falling back to a simulated file when `ffmpeg` is missing.
- `src/post_api.py` – simulates posting to Facebook while providing a structure for real integrations.
- `src/main.py` – orchestrates the full workflow.

## Quick Start

```bash
cd ~/Desktop
git clone https://github.com/joelirwin87-tech/auto_gen.git
cd auto_gen
python3 -m venv venv
source venv/bin/activate
pip install -r REQUIREMENTS.txt
cd src
python app.py
```

First run will download ~2 GB of Stable Diffusion weights. Subsequent runs use cached files.

### Run the Flask web demo

Launch the lightweight UI to enter prompts manually:

```bash
cd ~/Desktop/auto_gen
source venv/bin/activate
pip install -r REQUIREMENTS.txt
cd src
python app.py
```

Then browse to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) and submit a prompt. The server will run
`generate_image(prompt)` behind the scenes, write the output to `static/out.png`, and the page refresh will
display the newly generated (or placeholder) artwork.

Running the command will download the Stable Diffusion 2.1 base decoder from Hugging Face if it is not already cached. The script writes its outputs to the `src/` directory:

- `static/out.png` – the generated image from the Stable Diffusion pipeline.
- `out.mp4` – a short video clip stitched from the generated image.

If CUDA is available the pipeline will automatically move to the GPU; otherwise it runs entirely on the CPU without further configuration.

## Environment Variables

Copy `.env.example` to `.env` if you want to provide real credentials. Without them the application runs in fully simulated mode.

```bash
cp .env.example .env
```

- `OPENAI_API_KEY` – enables live caption generation via the OpenAI API.
- `FB_PAGE_TOKEN` – allows the Facebook posting step to attempt a real API call.

## Troubleshooting

- The first image generation run can take several minutes while dependencies download. Subsequent runs reuse the cached weights.
- If the Stable Diffusion 2.1 base model cannot be fetched, a placeholder image is produced so the rest of the pipeline still succeeds.
- Install `ffmpeg` and ensure it is on your `PATH` to create real MP4 files. Without it the pipeline emits a simulated text file in place of the video.
- Run `python3 main.py --help` from the `src/` directory for CLI usage details.
