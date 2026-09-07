# OpenAI audio reference

## Speech behavior

- Input field: `input`
- Optional overrides: `model`, `voice`, `speed`
- Output format in this skill: `mp3`
- Saved under dated audio folders

## Transcription behavior

- Input field: `file`
- Accept local path or HTTP(S) URL
- Temporary downloads are removed after request completion
- Returns transcribed `text`
