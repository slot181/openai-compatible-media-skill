# Usage Examples

## 1. Generate an image with only the required field

```bash
python3 {baseDir}/scripts/generate_image.py <<'EOF'
{"prompt":"A cozy rainy-night street in Shenzhen, neon reflections on wet pavement, cinematic lighting, ultra detailed"}
EOF
```

Use this when the user only cares about the image itself and did not request explicit model or format overrides.

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

Use only supported OpenAI-style fields. Do not invent width, height, steps, cfg, sampler, or other Stable-Diffusion-only parameters.

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
4. Call `generate_image.py` with one complete JSON object via stdin.

### Image editing

1. Confirm the source image path or URL.
2. Add `mask` only when the edit must stay localized.
3. Build a precise edit prompt that describes what changes and what must stay.
4. Call `edit_image.py` with one complete JSON object via stdin.

### Speech generation

1. Put the spoken content into `input`.
2. Use environment defaults unless the user asked for a specific model, voice, or speed.
3. Call `generate_speech.py` with one complete JSON object via stdin.

### Transcription

1. Put the local path or URL into `file`.
2. Call `transcribe_audio.py` with one complete JSON object via stdin.
