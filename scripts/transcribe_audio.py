#!/usr/bin/env python3
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from common import api_base_url, auth_headers, json_input, json_output, resolve_local_or_url, infer_mime


def post_multipart(url: str, fields: dict, file_field: str, file_path: Path):
    boundary = "----OpenClawOpenAPIMediaBoundary"
    body = bytearray()
    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        body.extend(str(v).encode())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode())
    body.extend(f"Content-Type: {infer_mime(file_path)}\r\n\r\n".encode())
    body.extend(file_path.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    req = Request(
        url,
        data=bytes(body),
        headers=auth_headers({"Content-Type": f"multipart/form-data; boundary={boundary}"}),
        method="POST",
    )
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    args = json_input()
    file_value = args.get("file")
    if not file_value or not isinstance(file_value, str):
        raise ValueError("file is required")

    model = args.get("model") or os.getenv("OPENAPI_GENERAL_TRANSCRIPTION_MODEL", "gpt-4o-transcribe")
    file_path, temp = resolve_local_or_url(file_value)
    try:
        data = post_multipart(
            f"{api_base_url()}/v1/audio/transcriptions",
            {"model": model},
            "file",
            file_path,
        )
    finally:
        if temp and file_path.exists():
            file_path.unlink(missing_ok=True)

    json_output({"ok": True, "model": model, "text": data.get("text", "")})
