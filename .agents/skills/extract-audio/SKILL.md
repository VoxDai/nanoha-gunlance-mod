---
name: extract-audio
description: "Extract complete audio tracks or a named channel from local audio/video media, optionally limited to a time range, and save a verified PCM WAV in output/. Use for source-media clipping; do not use for extracting WEM media from NBNK SoundBanks."
---

# Extract Audio

Use the project Conda environment and the bundled helper:

```sh
conda run -n nanoha-gunlance-mod python \
  .agents/skills/extract-audio/scripts/extract_audio.py inspect INPUT

conda run -n nanoha-gunlance-mod python \
  .agents/skills/extract-audio/scripts/extract_audio.py extract INPUT \
  [--start TIME] [--end TIME] [--stream-index N] [--channel FC] \
  [-o OUTPUT.wav] [--overwrite]
```

## Selection Rules

- Inspect the media before extraction and report the chosen stream index, language, codec, sample rate, and channel
  layout.
- A stream index is the global FFmpeg stream index shown by `inspect`, not its ordinal among audio streams. An explicit
  `--stream-index` is strict.
- Without an explicit stream, use the first audio stream marked `default`; if none is marked, use the first audio
  stream.
- Without `--channel`, preserve the selected stream's complete channel layout. Do not downmix.
- With a named channel such as `FC`, `FL`, or `FR`, output that channel alone as mono. Prefer the main stream; if it
  lacks the channel, use the first same-language stream that contains it. Stop and report the available layouts if no
  same-language stream contains it.
- Translate natural-language channel names to FFmpeg channel names; for example, central/中央 is `FC`, front-left/左前
  is `FL`, and front-right/右前 is `FR`.

## Time and Output Rules

- Treat `--start` as inclusive and `--end` as exclusive. Accept seconds or `HH:MM:SS[.fraction]`; omitted bounds mean
  the beginning or end of the source.
- Write 24-bit PCM WAV while preserving the selected stream's sample rate. Do not normalize volume, denoise, resample,
  or otherwise process the audio.
- Let the helper choose a descriptive filename in `output/` unless the user supplies `-o`. Never overwrite an existing
  file unless the user explicitly authorizes it and `--overwrite` is passed.
- Report the final path and the helper's verification summary. The helper verifies codec, sample rate, channel layout,
  and sample-exact duration before publishing the output.

This skill prepares ordinary WAV source material. Use `soundbank-workflow` instead for NBNK/WEM extraction, conversion,
replacement, or validation.
