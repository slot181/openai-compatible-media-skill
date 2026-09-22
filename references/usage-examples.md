# Usage Examples

## Configure image model defaults

Set the exact model IDs supported by your provider in the environment inherited by the scripts. For the provider model used in this project:

```bash
export OPENAPI_OPENAI_IMAGE_MODEL='openai/gpt-image-2.5-flare'
export OPENAPI_OPENAI_EDIT_IMAGE_MODEL='openai/gpt-image-2.5-flare'
```

Generation with this provider model has been verified; editing availability must also be supported by the provider. These exports apply to the current shell and its child processes. For an agent runner, set the variables in that runner's environment. An explicit JSON `model` takes priority; omitting it without the corresponding environment variable now produces an error instead of selecting `gpt-image-1`.

## 1. Generate an image with only the required field

```bash
python3 {baseDir}/scripts/generate_image.py <<'EOF'
{"prompt":"A cozy rainy-night street in Shenzhen, neon reflections on wet pavement, cinematic lighting, ultra detailed"}
EOF
```

Use this after configuring `OPENAPI_OPENAI_IMAGE_MODEL`, when the user did not request explicit model or format overrides.

To diagnose a provider exposing the exact model ID `openai/gpt-image-2.5-flare`, use a minimal request with your existing API credentials and base URL in the environment:

```bash
OPENAPI_REQUEST_TIMEOUT=180 python3 {baseDir}/scripts/generate_image.py <<'EOF'
{"prompt":"A red ceramic cup on a plain white background", "model":"openai/gpt-image-2.5-flare"}
EOF
```

Keep the `openai/` prefix only if your provider uses it. The heredoc closes stdin; progress is written to stderr and the result to stdout. See `openai-images.md` for interpreting timeout stages.

To allow a slower generation 300 seconds per blocking network operation for this invocation:

```bash
python3 {baseDir}/scripts/generate_image.py <<'EOF'
{
  "prompt": "A red ceramic cup on a plain white background",
  "model": "openai/gpt-image-2.5-flare",
  "timeout_seconds": 300
}
EOF
```

`timeout_seconds` overrides the environment timeout without changing it and is never sent to the provider. It also works with `edit_image.py`, covering the API request and any source image/mask downloads. Use a positive fractional value such as `0.2` with a local mock server to test timeouts. Other omitted options remain absent from the API request.

## 2. Generate an image with explicit OpenAI-style options

```bash
python3 {baseDir}/scripts/generate_image.py <<'EOF'
{
  "prompt": "A black-haired young woman in a white silk dress standing by a window, moonlight, soft shadows, elegant composition, ultra detailed",
  "model": "openai/gpt-image-1.5",
  "size": "1024x1536",
  "quality": "high",
  "output_format": "png",
  "background": "opaque"
}
EOF
```

Use the supported API fields and optional local `timeout_seconds`. For dimensions, use only `size`; `width`, `height`, and `aspect_ratio` are rejected. Do not add steps, cfg, sampler, or other Stable-Diffusion-only parameters.

## 3. Edit an image without a mask

```bash
python3 {baseDir}/scripts/edit_image.py <<'EOF'
{
  "image": "/absolute/path/to/source.png",
  "prompt": "Replace the background with a warm sunset sky while keeping the subject unchanged",
  "size": "1024x1024",
  "quality": "high",
  "output_format": "png"
}
EOF
```

Use this when the whole image can be reinterpreted and the user did not provide a separate mask.

## 4. Edit an image with a mask

```bash
python3 {baseDir}/scripts/edit_image.py <<'EOF'
{
  "image": "/absolute/path/to/source.png",
  "mask": "/absolute/path/to/mask.png",
  "prompt": "Change only the clothes to a black formal suit, preserve pose, face, and background",
  "size": "1024x1536",
  "quality": "high",
  "output_format": "png"
}
EOF
```

Use `mask` when only a specific region should change.

### Generate a new image from multiple references

```bash
python3 {baseDir}/scripts/edit_image.py <<'EOF'
{
  "image": [
    "/absolute/path/person.png",
    "/absolute/path/clothing.png",
    "https://example.com/background.png"
  ],
  "prompt": "Create a new full-body photograph of the person from image 1 wearing the clothes from image 2, in the setting from image 3. Preserve the person's facial features and the clothing design, with consistent lighting and perspective.",
  "model": "openai/gpt-image-2.5-flare",
  "timeout_seconds": 300
}
EOF
```

Replace the reference paths/URL with accessible images. Supply 1–16 images in the intended order; local paths and HTTP/HTTPS URLs can be mixed. A single string is still accepted for existing single-image calls. A mask is optional and, if supplied, applies to the first image only. Unspecified size, quality, and other API options remain unset. The input array is separate from `n`, which controls how many output images to generate.

## 5. Generate speech with environment defaults

```bash
python3 {baseDir}/scripts/generate_speech.py <<'EOF'
{"input":"喂，收到没？我给你随手捏了一条语音。"}
EOF
```

Use this when the user just wants a spoken line and does not care about model, voice, or speed.

## 6. Generate speech with explicit overrides

```bash
python3 {baseDir}/scripts/generate_speech.py <<'EOF'
{
  "input": "这次我用指定音色和语速来生成。",
  "model": "siliconflow/CosyVoice2-0.5B",
  "voice": "speech:archive_enya:clwxruin3000dgqkiqphbjb2q:kdulevexvhiaxhrkxjgz",
  "speed": 1.0
}
EOF
```

Only pass `model`, `voice`, or `speed` when the user explicitly requests them or when verification requires them.

## 7. Transcribe a local audio file

```bash
python3 {baseDir}/scripts/transcribe_audio.py <<'EOF'
{"file":"/absolute/path/to/audio.mp3"}
EOF
```

## 8. Transcribe an audio URL

```bash
python3 {baseDir}/scripts/transcribe_audio.py <<'EOF'
{"file":"https://example.com/audio.mp3"}
EOF
```

## 9. Recommended execution flow

### Image generation

1. Read `openai-images.md` when image parameters matter.
2. Build the final prompt yourself.
3. Keep parameters inside the supported OpenAI-style field set.
4. For text-only generation, call `generate_image.py` with one complete JSON object via stdin. If the user supplies reference images, follow the workflow below with `edit_image.py`.

### Image editing and generation from references

1. Put the source path/URL or ordered array of 1–16 paths/URLs in `image`.
2. Add `mask` only when the edit must stay localized; it applies to the first reference.
3. Build a prompt that describes each reference's role, the desired composition or changes, and what must stay.
4. Call `edit_image.py` with one complete JSON object via stdin.

### Speech generation

1. Put the spoken content into `input`.
2. Use environment defaults unless the user asked for a specific model, voice, or speed.
3. Call `generate_speech.py` with one complete JSON object via stdin.

### Transcription

1. Put the local path or URL into `file`.
2. Call `transcribe_audio.py` with one complete JSON object via stdin.
