#!/usr/bin/env python3
from urllib.request import Request

from common import auth_headers, infer_mime, json_output, resolve_local_or_url, save_base64_image

from image_api import image_endpoint, image_input, request_images, run_cli, validate_image_args


def post_multipart(url: str, fields: dict, files: list, *, timeout_seconds=None):
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
    return request_images(req, timeout_seconds=timeout_seconds)


def main():
    args = validate_image_args(image_input(), editing=True)
    image = args["image"]
    references = image if isinstance(image, list) else [image]
    prompt = args["prompt"]
    model = args["model"]
    size = args.get("size")
    quality = args.get("quality")
    background = args.get("background")
    output_format = args.get("output_format")
    n = args.get("n")
    mask = args.get("mask")
    timeout = args["timeout_seconds"]

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

    temporary_paths = []
    try:
        files = []
        # Preserve the input order: reference numbers and masks depend on it.
        image_field = "image[]" if isinstance(image, list) else "image"
        for reference in references:
            image_path, image_temp = resolve_local_or_url(reference, timeout_seconds=timeout)
            if image_temp:
                temporary_paths.append(image_path)
            files.append((image_field, image_path, infer_mime(image_path)))
        if mask:
            mask_path, mask_temp = resolve_local_or_url(mask, timeout_seconds=timeout)
            if mask_temp:
                temporary_paths.append(mask_path)
            files.append(("mask", mask_path, infer_mime(mask_path)))
        data = post_multipart(image_endpoint("edits"), fields, files, timeout_seconds=timeout)
    finally:
        for path in temporary_paths:
            path.unlink(missing_ok=True)

    results = []
    for i, item in enumerate(data.get("data", [])):
        if item.get("b64_json"):
            saved = save_base64_image(item["b64_json"], "edited", prompt, output_format)
            results.append({"index": i, "path": str(saved)})
        else:
            raise ValueError("Image editing requires b64_json in the response; this provider returned only a URL")

    json_output({"ok": True, "model": model, "mask_used": bool(mask), "results": results})


if __name__ == "__main__":
    run_cli(main)
