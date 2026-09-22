# OpenAI Images reference

## Prompt handling

- If the user did not provide an English prompt, build the final prompt yourself.
- If the user described the image in Chinese, first convert it into a final prompt that fits image-model use.
- Keep the final prompt focused on visible content, composition, lighting, style, mood, and important scene details.
- Do not just pass the user's raw Chinese sentence through unchanged when a cleaner image prompt is obviously needed.
- If the user already provided a clear prompt, preserve its intent and only normalize it when necessary.

## Supported generation fields in this skill

- `prompt` required
- `model` optional if `OPENAPI_OPENAI_IMAGE_MODEL` is configured
- `n` optional
- `size` optional
- `quality` optional
- `background` optional
- `output_format` optional
- `moderation` optional
- `timeout_seconds` optional, local only; never sent to the API

## Supported edit fields in this skill

- `image` required: one path/URL string or an ordered array of 1–16 path/URL strings
- `prompt` required
- `mask` optional
- `model` optional if `OPENAPI_OPENAI_EDIT_IMAGE_MODEL` is configured
- `n` optional
- `size` optional
- `quality` optional
- `background` optional
- `output_format` optional
- `timeout_seconds` optional, local only; never sent to the API

## Validation before network access

- Unknown fields are errors and include the supported field names. For example, `format`, `width`, `height`, `aspect_ratio`, `stream`, and `moderation` on edits are not silently ignored.
- `timeout_seconds` must be a positive finite JSON number, including fractional seconds for tests. Booleans and strings are rejected. Omitting it or setting it to `null` uses the environment default.
- `prompt` and an explicitly supplied `model` must be nonempty strings containing non-whitespace text. An invalid explicit model (including `null`) is an error, even if an environment default exists.
- `n` must be a positive JSON integer; booleans, strings, and fractional numbers are rejected. Model-specific count limits remain the provider's responsibility.
- Enum fields must be strings with one of the values below. Optional fields other than `model` may be omitted or set to `null` to leave them unset.
- Editing and reference-based generation require `image`: a nonempty string or an array of 1–16 nonempty strings. Every reference is validated before downloading any input. Local paths and HTTP/HTTPS URLs may be mixed; nested arrays and other URL schemes are unsupported. The optional `mask` remains a single path/URL string. Local files must exist and be readable when used.
- `background: "transparent"` cannot be combined with `output_format: "jpeg"`; choose `png` or `webp`. Omitting the output format leaves the provider default in effect.
- Omitted API options are not filled with local defaults or added to the request. Explicit `auto` values are forwarded as supplied. The model is resolved from JSON or the configured environment default; timeout settings remain local.

## Generate from multiple reference images

The [official image edit endpoint](https://developers.openai.com/api/reference/resources/images/methods/edit) supports generating an edited or extended image from multiple source images and a prompt, with up to 16 inputs for GPT Image models. The [official generation guide](https://developers.openai.com/api/docs/guides/image-generation) shows combining references through `images.edit` and uploading multiple files as `image[]` in multipart requests. It also specifies that a mask applies to the first input image. These references were checked on 2026-09-22.

Use `edit_image.py` with `image: ["/path/subject.png", "/path/style.png"]`. Describe what to use from image 1 and image 2 in the prompt. This can create a new composition using multiple references; it does not require a mask. The array controls input references; `n` independently controls output count.

The script preserves array order and uploads each reference in an `image[]` part to `/v1/images/edits`. The existing single-string input still uploads an `image` part. URL references are downloaded locally first; `timeout_seconds` applies to each download and the API request. Downloaded temporary files are cleaned up on completion or failure; local inputs are preserved.

The model default comes from `OPENAPI_OPENAI_EDIT_IMAGE_MODEL`, including for reference-based generation. `generate_image.py` remains text-only. Official support does not by itself verify a third-party gateway's multi-image implementation.

## Enum constraints

### size
- `1024x1024`
- `1024x1536`
- `1536x1024`
- `auto`
- Other positive `WIDTHxHEIGHT` strings are passed through to the provider. The model determines valid dimensions; newer GPT Image models support additional resolutions.
- Use only `size` for dimensions. The script checks the string format, without enforcing model-specific pixel, edge, or aspect-ratio limits. `width`, `height`, and `aspect_ratio` are not accepted.

### quality
- `low`
- `medium`
- `high`
- `xhigh` (only when supported by the selected model/provider)
- `max` (only when supported by the selected model/provider)
- `auto`

### background
- `transparent`
- `opaque`
- `auto`

### output_format
- `png`
- `webp`
- `jpeg`

### moderation
- `low`
- `auto`

## Endpoint and model compatibility

Image scripts accept `OPENAPI_BASE_URL` as either an origin (for example `https://api.openai.com`) or a base ending in `/v1`. They append `/images/generations` or `/images/edits` after exactly one trailing `/v1`.

Keep the user's exact model ID, including provider prefixes or aliases. An explicit JSON `model` overrides the corresponding environment default: `OPENAPI_OPENAI_IMAGE_MODEL` for generation and `OPENAPI_OPENAI_EDIT_IMAGE_MODEL` for editing. If neither is configured, fail with a configuration error before network access. There is no implicit fallback to `gpt-image-1`, and the editing default is independent of the generation default.

The [official Images API reference](https://developers.openai.com/api/reference/resources/images/methods/generate), checked on 2026-09-22, lists `gpt-image-2.5-sunburst` and `gpt-image-2.5-flare`, which support `xhigh` and `max`. A provider's `gpt-image-2.5` alias must be verified against that provider's documentation; do not silently rename it. Model-specific size and quality compatibility is checked by the server.

## Diagnosing waits and failures

- Supply a complete JSON object and close stdin (EOF), preferably using the heredoc examples. Writing JSON to an open stdin pipe without closing it leaves the script waiting for input before any API request is sent.
- Timeout precedence is JSON `timeout_seconds` → `OPENAPI_REQUEST_TIMEOUT` → `180` seconds. A valid explicit override takes precedence even if the environment value is invalid. The selected timeout applies to API requests, generated-image downloads, and editing input image/mask downloads without changing the environment or the API payload. This is a timeout for blocking network operations, not a total job deadline. Increasing it cannot extend a provider's gateway timeout or the calling tool's execution limit.
- Progress goes to stderr immediately, then every 15 seconds during API requests and generated-image downloads. Stdout contains the final JSON result. Use the last stderr stage to distinguish stdin input, API processing, and image download.
- If the execution tool returns a running session, keep polling that session. A short tool polling window is not an API timeout. Allow enough total execution time for generation plus downloads.
- HTTP failures include the status, a bounded error body, and `x-request-id` when provided. Failures produce `ok: false` and a nonzero exit code. A timeout does not establish whether the provider already generated an image; do not automatically resubmit the generation request.
- These scripts expect synchronous Images API JSON containing a nonempty `data` array. SSE streams and asynchronous task acknowledgements are not supported; verify the provider's endpoint if either is returned.
- For provider diagnosis, start with `prompt` and the exact `model` only. Add optional fields after the minimal request succeeds. Never include API keys in shared logs.
