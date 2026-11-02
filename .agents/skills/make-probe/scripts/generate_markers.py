#!/usr/bin/env python3
"""Generate Chinese probe labels using local macOS speech; never installs a Mod."""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import wave


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Command failed: {args[0]}\n{result.stderr.strip()}")


def chinese_number(value: int) -> str:
    digits = '零一二三四五六七八九'
    if value < 10:
        return digits[value]
    tens, ones = divmod(value, 10)
    return (digits[tens] if tens > 1 else '') + '十' + (digits[ones] if ones else '')


def read_pcm(path: Path) -> tuple[bytes, dict]:
    with wave.open(str(path), 'rb') as wav:
        if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getcomptype()) != (48000, 2, 2, 'NONE'):
            raise RuntimeError(f"Expected 48 kHz stereo 16-bit PCM: {path}")
        frames = wav.getnframes()
        pcm = wav.readframes(frames)
    samples = array('h', pcm)
    if sys.byteorder != 'little':
        samples.byteswap()
    peak = max(map(abs, samples), default=0)
    if not frames or len(pcm) != frames * 4 or not peak:
        raise RuntimeError(f"Empty, truncated or silent audio: {path}")
    if peak >= 32767:
        raise RuntimeError(f"Full-scale samples; inspect clipping before use: {path}")
    return pcm, {'sample_rate': 48000, 'channels': 2, 'bits': 16,
                 'frames': frames, 'peak_sample': peak, 'duration_seconds': frames / 48000}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--count', required=True, type=int, help='Number of candidate labels (1–99)')
    parser.add_argument('--voice', default='Tingting', help='Installed zh_CN voice')
    parser.add_argument('--rate', default=200, type=int, help='Speech rate in words per minute')
    args = parser.parse_args()
    if not 1 <= args.count <= 99 or args.rate <= 0:
        parser.error('--count must be 1–99 and --rate must be positive')
    out = args.output_dir.expanduser().resolve()
    if out.exists():
        parser.error(f'Output already exists: {out}; choose a new directory')
    root = next((p for p in Path(__file__).resolve().parents
                 if (p / 'tools/utils/wav_to_wem.py').is_file()), None)
    if root is None:
        parser.error('Run the script from its project skill location; project tools not found')
    say, ffmpeg = shutil.which('say'), shutil.which('ffmpeg')
    if not say or not ffmpeg:
        parser.error('Requires local macOS say and FFmpeg; use the nanoha-gunlance-mod conda environment')
    voices = subprocess.run([say, '-v', '?'], capture_output=True, text=True, check=True).stdout
    if not any(line.startswith(args.voice + ' ') and 'zh_CN' in line for line in voices.splitlines()):
        parser.error(f'Installed zh_CN voice unavailable: {args.voice}; choose one from say -v "?"')
    # Build off to the side. Neither conversion failures nor decoding failures publish partial output.
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.probe-markers-', dir=out.parent) as temp:
        stage = Path(temp) / 'markers'
        stage.mkdir()
        labels = [('load_check', '加载成功')]
        labels += [(f'trigger_{i}', f'触发{chinese_number(i)}') for i in range(1, args.count + 1)]
        manifest = {'voice': args.voice, 'rate': args.rate,
                    'speech_engine': say, 'ffmpeg': ffmpeg,
                    'count': args.count, 'in_game_tested': False, 'markers': []}
        for stem, text in labels:
            (stage / f'{stem}.txt').write_text(text + '\n', encoding='utf-8')
            source = stage / f'{stem}.aiff'
            wav = stage / f'{stem}.wav'
            wem = stage / f'{stem}.wem'
            decoded = stage / f'{stem}.decoded.wav'
            run([say, '-v', args.voice, '-r', str(args.rate), '-o', str(source), text])
            run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-i', str(source),
                 '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', str(wav)])
            pcm, info = read_pcm(wav)
            run([sys.executable, str(root / 'tools/utils/wav_to_wem.py'), str(wav), str(wem)])
            run([sys.executable, str(root / 'tools/utils/pyvgmstream.py'), 'decode', str(wem), str(decoded)])
            decoded_pcm, decoded_info = read_pcm(decoded)
            if pcm != decoded_pcm or info != decoded_info:
                raise RuntimeError(f'WEM decode does not match source PCM: {stem}')
            manifest['markers'].append({'name': stem, 'text': text, **info,
                                         'decode_pcm_exact': True})
        manifest['sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(stage.iterdir()) if p.is_file()}
        (stage / 'markers.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # mkdir is an exclusive reservation: a concurrent creator cannot be overwritten.
        out.mkdir()
        try:
            for source in stage.iterdir():
                shutil.copyfile(source, out / source.name)
        except BaseException:
            shutil.rmtree(out)
            raise
    print(f'Generated and decoded {len(labels)} markers: {out}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, subprocess.CalledProcessError, wave.Error) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
