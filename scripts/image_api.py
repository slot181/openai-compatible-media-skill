"""Shared transport and diagnostics for the synchronous Images API."""

import json
import os
import re
import sys
import threading
import time
from contextlib import contextmanager
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

from common import api_base_url, eprint, json_input, json_output, request_timeout


def image_endpoint(operation):
    base = api_base_url()
    if not base.endswith("/v1"):
        base += "/v1"
    return f"{base}/images/{operation}"


@contextmanager
def progress(stage):
    started = time.monotonic()
    done = threading.Event()
    eprint(f"[image] {stage}", flush=True)

    def report():
        while not done.wait(15):
            eprint(f"[image] {stage}: waiting ({time.monotonic() - started:.0f}s elapsed)", flush=True)

    worker = threading.Thread(target=report, daemon=True)
    worker.start()
    try:
        yield
    finally:
        done.set()
        worker.join()


def safe_error(text):
    key = os.getenv("OPENAPI_API_KEY")
    if key:
        text = text.replace(key, "<redacted>")
    return text


def read_response(request, stage, *, timeout_seconds=None):
    timeout = request_timeout(timeout_seconds)
    with progress(f"{stage} (network timeout {timeout:g}s)"):
        try:
            with urlopen(request, timeout=timeout) as response:
                if response.headers.get_content_type() == "text/event-stream":
                    raise ValueError(f"{stage}: received an SSE stream; this script expects a synchronous Images API JSON response")
                return response.read()
        except HTTPError as exc:
            with exc:
                try:
                    detail = exc.read(8192).decode("utf-8", errors="replace")
                except (OSError, HTTPException):
                    detail = "Could not read the HTTP error body"
                request_id = exc.headers.get("x-request-id")
            suffix = f"; request_id={request_id}" if request_id else ""
            raise RuntimeError(safe_error(f"{stage}: HTTP {exc.code}{suffix}: {detail}")) from None
        except (TimeoutError, URLError) as exc:
            reason = getattr(exc, "reason", exc)
            raise RuntimeError(
                safe_error(f"{stage}: network failure (timeout {timeout:g}s per blocking operation): {reason}. "
                           "Check the endpoint, provider status, timeout_seconds and OPENAPI_REQUEST_TIMEOUT. No automatic retry was made.")
            ) from None


def request_images(request, *, timeout_seconds=None):
    endpoint = urlsplit(request.full_url)
    stage = f"POST {endpoint.scheme}://{endpoint.hostname}{endpoint.path}"
    raw = read_response(request, stage, timeout_seconds=timeout_seconds)
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Images API returned a non-JSON response; check the endpoint and gateway") from None
    if not isinstance(data, dict):
        raise ValueError("Images API response must be a JSON object")
    if data.get("error"):
        raise ValueError(safe_error(f"Images API error: {json.dumps(data['error'], ensure_ascii=False)}"))
    items = data.get("data")
    if not isinstance(items, list) or not items:
        raise ValueError("Images API returned no images in data; an asynchronous task response is not supported")
    if any(not isinstance(item, dict) or not (item.get("b64_json") or item.get("url")) for item in items):
        raise ValueError("Images API returned an item without b64_json or url")
    eprint(f"[image] API returned {len(items)} image(s); saving results", flush=True)
    return data


def validate_size(value):
    # Model-specific resolution limits are checked by the provider, including aliases.
    if value is not None and value != "auto":
        if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]*x[1-9][0-9]*", value):
            raise ValueError("size must be auto or WIDTHxHEIGHT (for example 1024x1024)")


def require_text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def validate_image_reference(name, value):
    require_text(name, value)
    try:
        parsed = urlsplit(value)
        if parsed.scheme:
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise ValueError
            # Accessing port also validates malformed port numbers.
            parsed.port
    except ValueError:
        raise ValueError(f"{name} must be a local file path or a valid HTTP/HTTPS URL") from None


def validate_image_args(args, *, editing=False):
    allowed = {"prompt", "model", "n", "size", "quality", "background", "output_format", "timeout_seconds"}
    allowed.update({"image", "mask"} if editing else {"moderation"})
    unknown = set(args) - allowed
    if unknown:
        raise ValueError(f"Unsupported parameter(s): {', '.join(sorted(unknown))}. "
                         f"Supported parameters: {', '.join(sorted(allowed))}")

    require_text("prompt", args.get("prompt"))
    model_env = "OPENAPI_OPENAI_EDIT_IMAGE_MODEL" if editing else "OPENAPI_OPENAI_IMAGE_MODEL"
    if "model" in args:
        model = args["model"]
        require_text("model", model)
    else:
        model = os.getenv(model_env)
        if not model or not model.strip():
            raise ValueError(f"No image model configured; pass model or set {model_env}")

    n = args.get("n")
    if n is not None and (type(n) is not int or n <= 0):
        raise ValueError("n must be a positive integer (not a boolean)")
    validate_size(args.get("size"))
    enums = {
        "quality": {"low", "medium", "high", "xhigh", "max", "auto"},
        "background": {"transparent", "opaque", "auto"},
        "output_format": {"png", "webp", "jpeg"},
        "moderation": {"low", "auto"},
    }
    for name, values in enums.items():
        value = args.get(name)
        if value is not None and (not isinstance(value, str) or value not in values):
            raise ValueError(f"{name} must be one of: {', '.join(sorted(values))}")
    if args.get("background") == "transparent" and args.get("output_format") == "jpeg":
        raise ValueError("background=transparent requires output_format=png or webp; JPEG cannot store transparency")

    if editing:
        image = args.get("image")
        if isinstance(image, list):
            if not 1 <= len(image) <= 16:
                raise ValueError("image must contain between 1 and 16 input images")
            for index, reference in enumerate(image):
                validate_image_reference(f"image[{index}]", reference)
        else:
            validate_image_reference("image", image)
        if args.get("mask") is not None:
            validate_image_reference("mask", args["mask"])
    return {**args, "model": model, "timeout_seconds": request_timeout(args.get("timeout_seconds"))}


def image_input():
    if sys.stdin.isatty():
        raise ValueError("Pass one JSON object via stdin using a heredoc or file redirection")
    eprint("[image] Reading JSON from stdin (input must end with EOF)", flush=True)
    args = json_input()
    if not isinstance(args, dict):
        raise ValueError("Input must be a JSON object")
    return args


def run_cli(main):
    try:
        main()
    except (ValueError, RuntimeError, OSError, HTTPException) as exc:
        message = safe_error(str(exc))
        eprint(f"[image] {message}", flush=True)
        json_output({"ok": False, "error": message})
        sys.exit(1)
