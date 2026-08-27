from __future__ import annotations

from pathlib import Path
import struct
import tempfile
import unittest
import wave

from tools.utils.wav_to_wem import (
    ConversionError,
    WWISE_CHANNEL_EXTRAS,
    build_wem,
    convert_to_raw,
)

def fmt_fields(wem: bytes) -> tuple[int, int, int, int, int, int, bytes]:
    offset = wem.index(b"fmt ") + 8
    tag, channels, rate, byte_rate, align, bits, extra_size = struct.unpack_from(
        "<HHIIHHH", wem, offset
    )
    extra = wem[offset + 18 : offset + 18 + extra_size]
    return tag, channels, rate, byte_rate, align, bits, extra


class WavToWemTests(unittest.TestCase):
    def test_mono_and_stereo_headers_use_reviewed_wwise_channel_config(self) -> None:
        for channels in (1, 2):
            with self.subTest(channels=channels):
                pcm = b"\0" * (channels * 2 * 4)
                self.assertEqual(
                    fmt_fields(build_wem(pcm, channels)),
                    (
                        0xFFFE,
                        channels,
                        48_000,
                        48_000 * channels * 2,
                        channels * 2,
                        16,
                        WWISE_CHANNEL_EXTRAS[channels],
                    ),
                )

    def test_build_wem_rejects_invalid_channel_or_frame_size(self) -> None:
        with self.assertRaisesRegex(ConversionError, "channels"):
            build_wem(b"\0\0", 3)
        with self.assertRaisesRegex(ConversionError, "whole number"):
            build_wem(b"\0", 1)

    def test_dual_mono_downmix_preserves_sample_level_without_gain(self) -> None:
        samples = (0, 1000, -1000, 12_345, -12_345, 32_000, -32_000)
        stereo_pcm = b"".join(struct.pack("<hh", sample, sample) for sample in samples)
        with tempfile.TemporaryDirectory(prefix="wav-to-wem-test.") as directory:
            root = Path(directory)
            source = root / "dual-mono.wav"
            with wave.open(str(source), "wb") as wav:
                wav.setnchannels(2)
                wav.setsampwidth(2)
                wav.setframerate(48_000)
                wav.writeframes(stereo_pcm)
            stereo = convert_to_raw(source, root / "stereo.pcm", 2)
            mono = convert_to_raw(source, root / "mono.pcm", 1)
        self.assertEqual(stereo, stereo_pcm)
        self.assertEqual(struct.unpack(f"<{len(samples)}h", mono), samples)

if __name__ == "__main__":
    unittest.main()
