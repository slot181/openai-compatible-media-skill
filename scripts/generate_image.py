#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.request import Request, urlopen

from common import api_base_url, auth_headers, json_input, json_output, save_base64_image, write_binary, image_output_dir, sanitize_filename, guess_extension_from_format

ALLOWED_SIZE = {"1024x1024", "1024x1536", "1536x1024", "auto"}
ALLOWED_QUALITY = {"low", "medium", "high", "auto"}
ALLOWED_BACKGROUND = {"transparent", "opaque", "auto"}
ALLOWED_OUTPUT_FORMAT = {"png", "webp", "jpeg"}
ALLOWED_MODERATION = {"low", "auto"}


def validate_enum(name, value, allowed):
    if value is not None and value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")


if __name__ == "__main__":
    args = json_input()
    prompt = args.get("prompt")
    if not prompt or not isinstance(prompt, str):
        raise ValueError("prompt is required")

    model = args.get("model") or __import__("os").getenv("OPENAPI_OPENAI_IMAGE_MODEL", "gpt-image-1")
    size = args.get("size")
    quality = args.get("quality")
    background = args.get("background")
    output_format = args.get("output_format")
    moderation = args.get("moderation")
    n = args.get("n")

    validate_enum("size", size, ALLOWED_SIZE)
    validate_enum("quality", quality, ALLOWED_QUALITY)
    validate_enum("background", background, ALLOWED_BACKGROUND)
    validate_enum("output_format", output_format, ALLOWED_OUTPUT_FORMAT)
    validate_enum("moderation", moderation, ALLOWED_MODERATION)

    body = {"prompt": prompt, "model": model}
    if size is not None:
        body["size"] = size
    if quality is not None:
        body["quality"] = quality
    if background is not None:
        body["background"] = background
    if output_format is not None:
        body["output_format"] = output_format
    if moderation is not None:
        body["moderation"] = moderation
    if n is not None:
        body["n"] = n

    req = Request(
        f"{api_base_url()}/v1/images/generations",
        data=json.dumps(body).encode("utf-8"),
        headers=auth_headers({"Content-Type": "application/json"}),
        method="POST",
    )
    with urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    results = []
    for i, item in enumerate(data.get("data", [])):
        if item.get("b64_json"):
            saved = save_base64_image(item["b64_json"], "generated", prompt, output_format)
            results.append({"index": i, "path": str(saved), "revised_prompt": item.get("revised_prompt")})
        elif item.get("url"):
            ext = guess_extension_from_format(output_format, Path(item["url"]).suffix or ".png")
            filename = f"generated-{sanitize_filename(prompt, 40)}-{i+1}{ext}"
            out = image_output_dir() / filename
            with urlopen(item["url"]) as r:
                write_binary(out, r.read())
            results.append({"index": i, "path": str(out), "url": item["url"], "revised_prompt": item.get("revised_prompt")})
        else:
            results.append({"index": i, "error": "No image data returned"})

    json_output({"ok": True, "model": model, "results": results, "raw_created": data.get("created")})
