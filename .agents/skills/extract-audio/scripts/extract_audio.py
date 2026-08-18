#!/usr/bin/env python3
"""Inspect media audio streams and extract a verified 24-bit PCM WAV."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


class ExtractionError(RuntimeError):
    """Raised for user-facing extraction failures."""


def require_tool(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise ExtractionError(
            f"{name} was not found on PATH; run this helper in the "
            "nanoha-gunlance-mod Conda environment"
        )
    return executable


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def probe_media(path: Path) -> dict[str, Any]:
    ffprobe = require_tool("ffprobe")
    completed = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            (
                "stream=index,codec_name,sample_rate,channels,channel_layout,duration:"
                "stream_disposition=default:stream_tags=language,title:format=duration"
            ),
            "-of",
            "json",
            str(path),
        ]
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "ffprobe did not provide an error message"
        raise ExtractionError(f"could not inspect {path}: {detail}")
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"ffprobe returned invalid JSON: {exc}") from exc
    if not data.get("streams"):
        raise ExtractionError(f"no audio streams found in {path}")
    return data


def load_channel_layouts() -> tuple[set[str], dict[str, set[str]]]:
    ffmpeg = require_tool("ffmpeg")
    completed = run_command([ffmpeg, "-hide_banner", "-layouts"])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "ffmpeg did not provide an error message"
        raise ExtractionError(f"could not read FFmpeg channel layouts: {detail}")

    valid_channels: set[str] = set()
    layouts: dict[str, set[str]] = {}
    section = ""
    output = f"{completed.stdout}\n{completed.stderr}"
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line == "Individual channels:":
            section = "channels"
            continue
        if line == "Standard channel layouts:":
            section = "layouts"
            continue
        if not line or line.startswith("NAME"):
            continue
        parts = line.split()
        if section == "channels" and parts:
            valid_channels.add(parts[0].upper())
        elif section == "layouts" and len(parts) >= 2:
            layouts[parts[0]] = {item.upper() for item in parts[1].split("+")}
    if not valid_channels or not layouts:
        raise ExtractionError("could not parse FFmpeg channel layout information")
    return valid_channels, layouts


def channel_set(stream: dict[str, Any], layouts: dict[str, set[str]]) -> set[str]:
    return layouts.get(stream.get("channel_layout", ""), set())


def stream_language(stream: dict[str, Any]) -> str:
    return str(stream.get("tags", {}).get("language", "und"))


def is_default(stream: dict[str, Any]) -> bool:
    return int(stream.get("disposition", {}).get("default", 0)) == 1


def main_stream(streams: list[dict[str, Any]]) -> dict[str, Any]:
    return next((stream for stream in streams if is_default(stream)), streams[0])


def select_stream(
        streams: list[dict[str, Any]],
        stream_index: int | None,
        channel: str | None,
        layouts: dict[str, set[str]],
) -> dict[str, Any]:
    if stream_index is not None:
        selected = next(
            (stream for stream in streams if int(stream["index"]) == stream_index), None
        )
        if selected is None:
            available = ", ".join(str(stream["index"]) for stream in streams)
            raise ExtractionError(
                f"audio stream index {stream_index} was not found; available: {available}"
            )
        if channel and channel not in channel_set(selected, layouts):
            layout = selected.get("channel_layout", "unknown")
            raise ExtractionError(
                f"audio stream {stream_index} ({layout}) does not contain channel {channel}"
            )
        return selected

    selected = main_stream(streams)
    if not channel or channel in channel_set(selected, layouts):
        return selected

    language = stream_language(selected)
    fallback = next(
        (
            stream
            for stream in streams
            if stream_language(stream) == language
               and channel in channel_set(stream, layouts)
        ),
        None,
    )
    if fallback is not None:
        return fallback

    available = "; ".join(
        f"stream {stream['index']}: {stream.get('channel_layout', 'unknown')} "
        f"({stream_language(stream)})"
        for stream in streams
    )
    raise ExtractionError(
        f"no {language} audio stream contains channel {channel}; available: {available}"
    )


def parse_time(value: str | None, label: str) -> Decimal | None:
    if value is None:
        return None
    parts = value.split(":")
    if not 1 <= len(parts) <= 3:
        raise ExtractionError(
            f"invalid {label} time {value!r}; use seconds or HH:MM:SS[.fraction]"
        )
    try:
        total = Decimal("0")
        multiplier = Decimal("1")
        for part in reversed(parts):
            component = Decimal(part)
            if component < 0:
                raise ExtractionError(f"{label} time must not be negative")
            total += component * multiplier
            multiplier *= 60
        if len(parts) > 1 and any(Decimal(part) >= 60 for part in parts[1:]):
            raise ExtractionError(
                f"invalid {label} time {value!r}; minute/second fields must be below 60"
            )
    except InvalidOperation as exc:
        raise ExtractionError(
            f"invalid {label} time {value!r}; use seconds or HH:MM:SS[.fraction]"
        ) from exc
    return total


def media_duration(data: dict[str, Any], selected: dict[str, Any]) -> Decimal | None:
    raw = selected.get("duration") or data.get("format", {}).get("duration")
    if raw in (None, "N/A"):
        return None
    try:
        return Decimal(str(raw))
    except InvalidOperation:
        return None


def validate_range(
        start: Decimal | None, end: Decimal | None, duration: Decimal | None
) -> tuple[Decimal, Decimal | None]:
    effective_start = start or Decimal("0")
    if end is not None and end <= effective_start:
        raise ExtractionError("end time must be later than start time")
    if duration is not None:
        tolerance = Decimal("0.001")
        if effective_start >= duration:
            raise ExtractionError(
                f"start time {effective_start} is outside media duration {duration}"
            )
        if end is not None and end > duration + tolerance:
            raise ExtractionError(f"end time {end} exceeds media duration {duration}")
    return effective_start, end


def format_seconds(value: Decimal) -> str:
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def time_slug(value: Decimal) -> str:
    milliseconds = int((value * 1000).to_integral_value(rounding=ROUND_HALF_UP))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    slug = f"{hours:02d}-{minutes:02d}-{seconds:02d}"
    return f"{slug}.{millis:03d}" if millis else slug


def default_output_path(
        input_path: Path,
        start: Decimal,
        end: Decimal | None,
        stream_index: int,
        channel: str | None,
) -> Path:
    project_root = Path(__file__).resolve().parents[4]
    safe_stem = re.sub(r"[^\w.-]+", "_", input_path.stem, flags=re.UNICODE).strip("_")
    range_label = (
        "full"
        if start == 0 and end is None
        else f"{time_slug(start)}-{time_slug(end) if end is not None else 'end'}"
    )
    channel_label = f"_{channel}" if channel else ""
    return (
            project_root
            / "output"
            / f"{safe_stem}_{range_label}_stream{stream_index}{channel_label}.wav"
    )


def print_streams(data: dict[str, Any]) -> None:
    streams = data["streams"]
    primary = main_stream(streams)
    print("Audio streams:")
    for stream in streams:
        markers = []
        if is_default(stream):
            markers.append("default")
        if stream is primary:
            markers.append("main")
        marker = f" [{', '.join(markers)}]" if markers else ""
        title = stream.get("tags", {}).get("title")
        title_text = f", title={title}" if title else ""
        print(
            f"  stream {stream['index']}{marker}: codec={stream.get('codec_name', 'unknown')}, "
            f"language={stream_language(stream)}, rate={stream.get('sample_rate', 'unknown')} Hz, "
            f"channels={stream.get('channels', 'unknown')}, "
            f"layout={stream.get('channel_layout', 'unknown')}{title_text}"
        )


def verify_output(
        path: Path,
        selected: dict[str, Any],
        channel: str | None,
        target_samples: int | None,
) -> dict[str, Any]:
    ffprobe = require_tool("ffprobe")
    completed = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_name,sample_rate,channels,channel_layout,duration_ts,time_base",
            "-of",
            "json",
            str(path),
        ]
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "ffprobe did not provide an error message"
        raise ExtractionError(f"could not verify temporary WAV: {detail}")
    try:
        stream = json.loads(completed.stdout)["streams"][0]
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        raise ExtractionError("ffprobe returned incomplete WAV verification data") from exc

    expected_rate = int(selected["sample_rate"])
    expected_channels = 1 if channel else int(selected["channels"])
    if stream.get("codec_name") != "pcm_s24le":
        raise ExtractionError(f"unexpected output codec: {stream.get('codec_name')}")
    if int(stream.get("sample_rate", 0)) != expected_rate:
        raise ExtractionError(
            f"output sample rate {stream.get('sample_rate')} does not match source {expected_rate}"
        )
    if int(stream.get("channels", 0)) != expected_channels:
        raise ExtractionError(
            f"output channels {stream.get('channels')} does not match expected {expected_channels}"
        )
    if channel and stream.get("channel_layout") != "mono":
        raise ExtractionError(
            f"single-channel output has unexpected layout {stream.get('channel_layout')}"
        )
    expected_layout = selected.get("channel_layout")
    if not channel and expected_layout and stream.get("channel_layout") != expected_layout:
        raise ExtractionError(
            f"output layout {stream.get('channel_layout')} does not match source {expected_layout}"
        )
    if target_samples is not None and int(stream.get("duration_ts", -1)) != target_samples:
        raise ExtractionError(
            f"output contains {stream.get('duration_ts')} samples; expected {target_samples}"
        )
    return stream


def extract(args: argparse.Namespace) -> None:
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file():
        raise ExtractionError(f"input file does not exist: {input_path}")

    data = probe_media(input_path)
    valid_channels, layouts = load_channel_layouts()
    channel = args.channel.upper() if args.channel else None
    if channel and channel not in valid_channels:
        choices = ", ".join(sorted(valid_channels))
        raise ExtractionError(f"unknown channel {channel!r}; valid FFmpeg channels: {choices}")

    selected = select_stream(data["streams"], args.stream_index, channel, layouts)
    start = parse_time(args.start, "start")
    end = parse_time(args.end, "end")
    effective_start, end = validate_range(
        start, end, media_duration(data, selected)
    )

    try:
        sample_rate = int(selected["sample_rate"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ExtractionError("selected stream does not report a valid sample rate") from exc
    target_samples = None
    if end is not None:
        target_samples = int(
            ((end - effective_start) * sample_rate).to_integral_value(
                rounding=ROUND_HALF_UP
            )
        )
        if target_samples <= 0:
            raise ExtractionError("selected time range is shorter than one output sample")

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_output_path(
            input_path, effective_start, end, int(selected["index"]), channel
        )
    )
    if output_path.suffix.lower() != ".wav":
        raise ExtractionError(f"output path must end in .wav: {output_path}")
    if output_path.exists() and not args.overwrite:
        raise ExtractionError(
            f"output already exists: {output_path}; pass --overwrite only with explicit authorization"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print_streams(data)
    print(
        f"Selected stream {selected['index']}: language={stream_language(selected)}, "
        f"codec={selected.get('codec_name', 'unknown')}, rate={sample_rate} Hz, "
        f"layout={selected.get('channel_layout', 'unknown')}"
    )
    if channel:
        print(f"Selected channel: {channel} (mono output)")

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
                prefix=f".{output_path.stem}.",
                suffix=".wav",
                dir=output_path.parent,
                delete=False,
        ) as handle:
            temporary = Path(handle.name)

        ffmpeg = require_tool("ffmpeg")
        command = [ffmpeg, "-hide_banner", "-loglevel", "error"]
        if effective_start > 0:
            command.extend(["-ss", format_seconds(effective_start)])
        command.extend(
            [
                "-i",
                str(input_path),
                "-map",
                f"0:{selected['index']}",
                "-vn",
                "-sn",
                "-dn",
            ]
        )
        filters = []
        if channel:
            filters.append(f"pan=mono|c0={channel}")
        if target_samples is not None:
            filters.append(f"atrim=end_sample={target_samples}")
        if filters:
            filters.append("asetpts=PTS-STARTPTS")
            command.extend(["-af", ",".join(filters)])
        command.extend(["-c:a", "pcm_s24le", "-y", str(temporary)])

        completed = run_command(command)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or "ffmpeg did not provide an error message"
            raise ExtractionError(f"ffmpeg extraction failed: {detail}")

        verified = verify_output(temporary, selected, channel, target_samples)
        os.replace(temporary, output_path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    print(f"Output: {output_path}")
    print(
        f"Verified: codec={verified['codec_name']}, rate={verified['sample_rate']} Hz, "
        f"channels={verified['channels']}, layout={verified.get('channel_layout', 'unknown')}, "
        f"samples={verified.get('duration_ts', 'unknown')}"
    )


def inspect(args: argparse.Namespace) -> None:
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file():
        raise ExtractionError(f"input file does not exist: {input_path}")
    print_streams(probe_media(input_path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect media audio streams or extract a verified 24-bit PCM WAV."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="list audio streams and layouts")
    inspect_parser.add_argument("input", help="input audio or video file")
    inspect_parser.set_defaults(func=inspect)

    extract_parser = subparsers.add_parser(
        "extract", help="extract an audio track or channel"
    )
    extract_parser.add_argument("input", help="input audio or video file")
    extract_parser.add_argument(
        "--start", help="inclusive start time in seconds or HH:MM:SS"
    )
    extract_parser.add_argument(
        "--end", help="exclusive end time in seconds or HH:MM:SS"
    )
    extract_parser.add_argument(
        "--stream-index", type=int, help="strict global FFmpeg audio stream index"
    )
    extract_parser.add_argument(
        "--channel", help="single FFmpeg channel name such as FC, FL, or FR"
    )
    extract_parser.add_argument("-o", "--output", help="output .wav path")
    extract_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing output after verification",
    )
    extract_parser.set_defaults(func=extract)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ExtractionError as exc:
        parser.exit(1, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
