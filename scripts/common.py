#!/usr/bin/env python3
import base64
import json
import math
import mimetypes
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
from urllib.request import urlopen, Request

DEFAULT_TIMEOUT_SECONDS = 180


def request_timeout(override: Optional[float] = None) -> float:
    if override is not None:
        if type(override) not in (int, float):
            raise ValueError("timeout_seconds must be a positive finite number")
        try:
            timeout = float(override)
        except OverflowError:
            raise ValueError("timeout_seconds must be a positive finite number") from None
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout_seconds must be a positive finite number")
        return timeout
    try:
        timeout = float(os.getenv("OPENAPI_REQUEST_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        raise ValueError("OPENAPI_REQUEST_TIMEOUT must be a positive finite number") from None
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("OPENAPI_REQUEST_TIMEOUT must be a positive finite number")
    return timeout


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _skill_default_image_base() -> Path:
    return skill_root() / "media" / "image" / "openapi"


def _skill_default_audio_base() -> Path:
    return skill_root() / "media" / "audio" / "openapi"


def image_output_dir() -> Path:
    base = os.getenv("OPENAPI_IMAGE_OUTPUT_DIR")
    root = (Path(base).expanduser() / "openapi") if base else _skill_default_image_base()
    out = root / datetime.now().strftime("%Y-%m-%d")
    out.mkdir(parents=True, exist_ok=True)
    return out


def audio_output_dir() -> Path:
    base = os.getenv("OPENAPI_AUDIO_OUTPUT_DIR")
    root = (Path(base).expanduser() / "openapi") if base else _skill_default_audio_base()
    out = root / datetime.now().strftime("%Y-%m-%d")
    out.mkdir(parents=True, exist_ok=True)
    return out


def temp_dir() -> Path:
    path = skill_root() / "media" / "tmp" / "openapi"
    path.mkdir(parents=True, exist_ok=True)
    return path


def api_base_url() -> str:
    return os.getenv("OPENAPI_BASE_URL", "https://api.openai.com").rstrip("/")


def api_key() -> str:
    key = os.getenv("OPENAPI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAPI_API_KEY")
    return key


def sanitize_filename(text: str, max_len: int = 60) -> str:
    text = (text or "file").strip().lower()
    text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._-")
    return (text or "file")[:max_len]


def is_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def download_to_temp(url: str, suffix: Optional[str] = None, *, timeout_seconds: Optional[float] = None) -> Path:
    timeout = request_timeout(timeout_seconds)
    parsed = urlparse(url)
    guessed_suffix = suffix or Path(parsed.path).suffix or ".bin"
    fd, path = tempfile.mkstemp(prefix="openapi_", suffix=guessed_suffix, dir=str(temp_dir()))
    os.close(fd)
    req = Request(url, headers={"User-Agent": "OpenClaw openapi-media skill"})
    try:
        with urlopen(req, timeout=timeout) as resp, open(path, "wb") as f:
            f.write(resp.read())
    except Exception:
        Path(path).unlink(missing_ok=True)
        raise
    return Path(path)


def resolve_local_or_url(path_or_url: str, *, timeout_seconds: Optional[float] = None) -> Tuple[Path, bool]:
    if is_url(path_or_url):
        return download_to_temp(path_or_url, timeout_seconds=timeout_seconds), True
    p = Path(path_or_url).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    return p, False


def guess_extension_from_format(fmt: Optional[str], fallback: str) -> str:
    if fmt == "jpeg":
        return ".jpg"
    if fmt == "webp":
        return ".webp"
    if fmt == "png":
        return ".png"
    return fallback


def write_binary(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def save_base64_image(b64_data: str, prefix: str, prompt: str, output_format: Optional[str] = None) -> Path:
    ext = guess_extension_from_format(output_format, ".png")
    filename = f"{prefix}-{sanitize_filename(prompt, 40)}-{datetime.now().strftime('%H%M%S')}{ext}"
    output_path = image_output_dir() / filename
    write_binary(output_path, base64.b64decode(b64_data))
    return output_path


def json_input() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def json_output(payload: dict):
    print(json.dumps(payload, ensure_ascii=False))


def auth_headers(extra: Optional[dict] = None) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key()}",
    }
    if extra:
        headers.update(extra)
    return headers


def infer_mime(path: Path) -> str:
    return mimetypes.guess_type(str(path))[0] or "application/octet-stream"
