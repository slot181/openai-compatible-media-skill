---
name: openai-compatible-media
description: Generate images from text or multiple reference images, edit images with optional mask, create speech, and transcribe audio through bundled local scripts that call OpenAI-compatible APIs. Use when the user wants OpenAI-format image generation/editing or OpenAI-compatible TTS/STT. Image parameters are restricted to the OpenAI-style request format.
---

# openai-compatible-media

## Core rules

- Work according to the relevant workflow and parameter constraints.
- For image generation and editing, build the final prompt yourself from the user's request instead of passing raw user wording through unchanged when a cleaner prompt is obviously needed.
- For speech and transcription, map user intent to the script input fields directly and use environment defaults when the user did not request specific overrides.
- Pass absolute local paths when possible.
- All media files produced, downloaded, or processed under this skill must adhere to the standard `media/` directory structure under the user's workspace CWD as established on 2026-04-06:
  - Images (generation, edits, stable diffusion outputs, screenshots, frame pulls) go under `media/image/`.
  - Audio files (TTS outputs, recordings, voice transcribes, downloads) go under `media/audio/`.
  - Video files (scraped videos, recordings, exports) go under `media/video/`.
  - Texts (transcripts, OCR results, subtitles, prompts) go under `media/text/`.
- Never create transient or duplicate directories like `generated-images/`, `output/`, or `exports/` unless explicitly specified. Tool-specific outputs can create secondary nesting (e.g., `media/image/sd-image-gen/` or `media/audio/tts/`).
- Call the bundled scripts with JSON via stdin so the request shape is explicit and complete.
- For images, pass `model` explicitly or configure the corresponding model environment variable below. There is no built-in fallback model. Unsupported JSON fields and invalid parameter combinations fail before any image download or API request; read `references/openai-images.md` for the accepted fields.
- Use `edit_image.py` for generation from reference images as well as edits. Its `image` accepts one path/URL or an ordered array of 1–16 paths/URLs. Preserve the reference order and describe each image's role in the prompt. An optional mask applies to the first image. See `references/usage-examples.md` for a multi-image request.
- Image scripts accept local `timeout_seconds` to override `OPENAPI_REQUEST_TIMEOUT` for one invocation; it is never sent to the API. Leave unrequested API options unset. Express dimensions only with `size` (`WIDTHxHEIGHT` or `auto`); the provider checks model-specific limits.
- Close stdin after the JSON (use a heredoc or input file). Image scripts report progress on stderr and final JSON on stdout; continue polling an existing running session instead of submitting the same generation again. For timeout diagnosis, read `references/openai-images.md`.

## Scripts

- Generate images from text: `{baseDir}/scripts/generate_image.py`
- Edit images or generate from one/multiple reference images: `{baseDir}/scripts/edit_image.py`
- Generate speech: `{baseDir}/scripts/generate_speech.py`
- Transcribe audio: `{baseDir}/scripts/transcribe_audio.py`

## Env

Required:
- `OPENAPI_API_KEY`

Optional:
- `OPENAPI_BASE_URL` (image scripts accept an origin or a base ending in `/v1`)
- `OPENAPI_REQUEST_TIMEOUT` (image requests/downloads: default network timeout in seconds, fallback `180`; overridden by JSON `timeout_seconds`; not a total job deadline)
- `OPENAPI_OPENAI_IMAGE_MODEL` (generation default; required when JSON omits `model`)
- `OPENAPI_OPENAI_EDIT_IMAGE_MODEL` (editing default; required when JSON omits `model`)
- `OPENAPI_GENERAL_SPEECH_MODEL`
- `OPENAPI_GENERAL_TRANSCRIPTION_MODEL`
- `OPENAPI_GENERAL_SPEECH_VOICE`
- `OPENAPI_GENERAL_SPEECH_SPEED`
- `OPENAPI_IMAGE_OUTPUT_DIR`
- `OPENAPI_AUDIO_OUTPUT_DIR`

## Read next

- `references/openai-images.md`
- `references/openai-audio.md`
- `references/usage-examples.md`
