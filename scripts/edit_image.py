#!/usr/bin/env python3
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from common import api_base_url, auth_headers, json_input, json_output, resolve_local_or_url, save_base64_image

ALLOWED_SIZE = {"1024x1024", "1024x1536", "1536x1024", "auto"}
ALLOWED_QUALITY = {"low", "medium", "high", "auto"}
ALLOWED_BACKGROUND = {"transparent", "opaque", "auto"}
ALLOWED_OUTPUT_FORMAT = {"png", "webp", "jpeg"}


def validate_enum(name, value, allowed):
    if value is not None and value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")


def post_multipart(url: str, fields: dict, files: list):
    boundary = "----OpenClawOpenAPIMediaBoundary"
    body = bytearray()
    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        body.extend(str(v).encode())
        body.extend(b"\r\n")
    for field_name, file_path, mime in files:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
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
    image = args.get("image")
    prompt = args.get("prompt")
    if not image or not isinstance(image, str):
        raise ValueError("image is required")
    if not prompt or not isinstance(prompt, str):
        raise ValueError("prompt is required")

    model = args.get("model") or os.getenv("OPENAPI_OPENAI_EDIT_IMAGE_MODEL", "gpt-image-1")
    size = args.get("size")
    quality = args.get("quality")
    background = args.get("background")
    output_format = args.get("output_format")
    n = args.get("n")
    mask = args.get("mask")

    validate_enum("size", size, ALLOWED_SIZE)
    validate_enum("quality", quality, ALLOWED_QUALITY)
    validate_enum("background", background, ALLOWED_BACKGROUND)
    validate_enum("output_format", output_format, ALLOWED_OUTPUT_FORMAT)

    image_path, image_temp = resolve_local_or_url(image)
    mask_path = None
    mask_temp = False
    if mask:
        mask_path, mask_temp = resolve_local_or_url(mask)

    fields = {"prompt": prompt, "model": model}
    if size is not None:
        fields["size"] = size
    if quality is not None:
        fields["quality"] = quality
    if background is not None:
        fields["background"] = background
    if output_format is not None:
        fields["output_format"] = output_format
    if n is not None:
        fields["n"] = n

    files = [("image", image_path, "application/octet-stream")]
    if mask_path is not None:
        files.append(("mask", mask_path, "application/octet-stream"))

    try:
        data = post_multipart(f"{api_base_url()}/v1/images/edits", fields, files)
    finally:
        if image_temp and image_path.exists():
            image_path.unlink(missing_ok=True)
        if mask_path is not None and mask_temp and mask_path.exists():
            mask_path.unlink(missing_ok=True)

    results = []
    for i, item in enumerate(data.get("data", [])):
        if item.get("b64_json"):
            saved = save_base64_image(item["b64_json"], "edited", prompt, output_format)
            results.append({"index": i, "path": str(saved)})
        else:
            results.append({"index": i, "error": "No b64_json returned"})

    json_output({"ok": True, "model": model, "mask_used": bool(mask), "results": results})
