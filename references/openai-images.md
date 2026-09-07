# OpenAI Images reference

## Prompt handling

- If the user did not provide an English prompt, build the final prompt yourself.
- If the user described the image in Chinese, first convert it into a final prompt that fits image-model use.
- Keep the final prompt focused on visible content, composition, lighting, style, mood, and important scene details.
- Do not just pass the user's raw Chinese sentence through unchanged when a cleaner image prompt is obviously needed.
- If the user already provided a clear prompt, preserve its intent and only normalize it when necessary.

## Supported generation fields in this skill

- `prompt` required
- `model` optional
- `n` optional
- `size` optional
- `quality` optional
- `background` optional
- `output_format` optional
- `moderation` optional

## Supported edit fields in this skill

- `image` required
- `prompt` required
- `mask` optional
- `model` optional
- `n` optional
- `size` optional
- `quality` optional
- `background` optional
- `output_format` optional

## Enum constraints

### size
- `1024x1024`
- `1024x1536`
- `1536x1024`
- `auto`

### quality
- `low`
- `medium`
- `high`
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

