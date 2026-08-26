from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest
import wave

from builders.voice_standard import (
    STANDARD_ACTOR_BANK_PATH,
    STANDARD_ACTOR_BANK_SHA256,
    STANDARD_DONOR_BANK_PATH,
    STANDARD_DONOR_BANK_SHA256,
    STANDARD_SOUND_BODY_LENGTH,
    STANDARD_SOUND_PARENT_OFFSET,
    STANDARD_SOUND_POSITIONING_VECTOR,
    STANDARD_SOUND_POSITIONING_VECTOR_OFFSET,
    STANDARD_VOICE_PARENT_ID,
    standard_voice_sound_body,
    validate_standard_reference_binaries,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class StandardVoiceSoundTests(unittest.TestCase):
    def test_reference_files_and_semantic_guards_are_exact(self) -> None:
        donor = PROJECT_ROOT / STANDARD_DONOR_BANK_PATH
        actor = PROJECT_ROOT / STANDARD_ACTOR_BANK_PATH
        self.assertEqual(hashlib.sha256(donor.read_bytes()).hexdigest(), STANDARD_DONOR_BANK_SHA256)
        self.assertEqual(hashlib.sha256(actor.read_bytes()).hexdigest(), STANDARD_ACTOR_BANK_SHA256)
        validate_standard_reference_binaries(donor, actor)

    def test_standard_body_is_46_bytes_with_direct_209_and_c1(self) -> None:
        sound_id = 4_000_000_001
        media_id = 4_000_000_002
        body = standard_voice_sound_body(sound_id, media_id)
        self.assertEqual(len(body), STANDARD_SOUND_BODY_LENGTH)
        self.assertEqual(struct.unpack_from("<I", body, 0)[0], sound_id)
        self.assertEqual(struct.unpack_from("<I", body, 9)[0], media_id)
        self.assertEqual(
            struct.unpack_from("<I", body, STANDARD_SOUND_PARENT_OFFSET)[0],
            STANDARD_VOICE_PARENT_ID,
        )
        self.assertEqual(
            body[STANDARD_SOUND_POSITIONING_VECTOR_OFFSET],
            STANDARD_SOUND_POSITIONING_VECTOR,
        )

    def test_all_project_audio_is_48khz_stereo_pcm_16_or_24_bit(self) -> None:
        paths = sorted((PROJECT_ROOT / "audio").rglob("*.wav"))
        self.assertEqual(len(paths), 12)
        for path in paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                with wave.open(str(path), "rb") as wav:
                    self.assertEqual(wav.getframerate(), 48_000)
                    self.assertEqual(wav.getnchannels(), 2)
                    self.assertIn(wav.getsampwidth(), (2, 3))
                    self.assertEqual(wav.getcomptype(), "NONE")

    def test_guard_silent_fallback_is_exactly_ten_ms_of_zeroes(self) -> None:
        path = PROJECT_ROOT / "audio/hm_cm00_epvsp/silence_10ms.wav"
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "94988ef93524fb8b65c1884f413729ae71b526e694d63aca79adf27e27b02222",
        )
        with wave.open(str(path), "rb") as wav:
            self.assertEqual(
                (
                    wav.getframerate(),
                    wav.getnchannels(),
                    wav.getsampwidth(),
                    wav.getnframes(),
                    wav.getcomptype(),
                ),
                (48_000, 2, 2, 480, "NONE"),
            )
            self.assertEqual(wav.readframes(480), bytes(1_920))


if __name__ == "__main__":
    unittest.main()
