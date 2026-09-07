#!/usr/bin/env python3
import json
import os
from datetime import datetime
from urllib.request import Request, urlopen

from common import api_base_url, auth_headers, json_input, json_output, audio_output_dir, write_binary, sanitize_filename

if __name__ == "__main__":
    args = json_input()
    text = args.get("input")
    if not text or not isinstance(text, str):
        raise ValueError("input is required")

    model = args.get("model") or os.getenv("OPENAPI_GENERAL_SPEECH_MODEL", "tts-1")
    voice = args.get("voice") or os.getenv("OPENAPI_GENERAL_SPEECH_VOICE", "alloy")
    speed = args.get("speed")
    if speed is None:
        speed = float(os.getenv("OPENAPI_GENERAL_SPEECH_SPEED", "1.0"))

    body = {
        "model": model,
        "input": text,
        "voice": voice,
        "speed": speed,
        "response_format": "mp3",
    }
    req = Request(
        f"{api_base_url()}/v1/audio/speech",
        data=json.dumps(body).encode("utf-8"),
        headers=auth_headers({"Content-Type": "application/json"}),
        method="POST",
    )
    with urlopen(req) as resp:
        audio = resp.read()

    filename = f"speech-{sanitize_filename(text, 32)}-{datetime.now().strftime('%H%M%S')}.mp3"
    out = audio_output_dir() / filename
    write_binary(out, audio)
    json_output({"ok": True, "model": model, "voice": voice, "speed": speed, "path": str(out)})
