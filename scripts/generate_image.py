#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request

from common import auth_headers, json_output, save_base64_image, write_binary, image_output_dir, sanitize_filename, guess_extension_from_format

from image_api import image_endpoint, image_input, read_response, request_images, run_cli, validate_image_args


def main():
    args = validate_image_args(image_input())
    prompt = args["prompt"]
    model = args["model"]
    size = args.get("size")
    quality = args.get("quality")
    background = args.get("background")
    output_format = args.get("output_format")
    moderation = args.get("moderation")
    n = args.get("n")
    timeout = args["timeout_seconds"]

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
        image_endpoint("generations"),
        data=json.dumps(body).encode("utf-8"),
        headers=auth_headers({"Content-Type": "application/json"}),
        method="POST",
    )
    data = request_images(req, timeout_seconds=timeout)

    results = []
    for i, item in enumerate(data.get("data", [])):
        if item.get("b64_json"):
            saved = save_base64_image(item["b64_json"], "generated", prompt, output_format)
            results.append({"index": i, "path": str(saved), "revised_prompt": item.get("revised_prompt")})
        elif item.get("url"):
            ext = guess_extension_from_format(output_format, Path(urlsplit(item["url"]).path).suffix or ".png")
            filename = f"generated-{sanitize_filename(prompt, 40)}-{i+1}{ext}"
            out = image_output_dir() / filename
            write_binary(out, read_response(item["url"], f"Download image {i + 1}", timeout_seconds=timeout))
            results.append({"index": i, "path": str(out), "url": item["url"], "revised_prompt": item.get("revised_prompt")})
        else:
            results.append({"index": i, "error": "No image data returned"})

    json_output({"ok": True, "model": model, "results": results, "raw_created": data.get("created")})


if __name__ == "__main__":
    run_cli(main)
