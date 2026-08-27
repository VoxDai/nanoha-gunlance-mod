from __future__ import annotations

import struct
import unittest

from builders.voice_standard import (
    STANDARD_SOUND_BODY,
    STANDARD_SOUND_BODY_LENGTH,
    STANDARD_SOUND_MEDIA_OFFSET,
    STANDARD_SOUND_PARENT_OFFSET,
    STANDARD_SOUND_POSITIONING_VECTOR,
    STANDARD_SOUND_POSITIONING_VECTOR_OFFSET,
    insert_standard_voice_sound,
    standard_voice_sound_body,
)
from tools import soundbank_editor

from ._soundbank_fixtures import make_hirc


class StandardVoiceSoundTests(unittest.TestCase):
    def test_standard_body_changes_only_requested_ids(self) -> None:
        sound_id = 4_000_000_001
        media_id = 4_000_000_002
        parent_id = 4_000_000_003
        body = standard_voice_sound_body(
            sound_id,
            media_id,
            direct_parent_id=parent_id,
        )
        expected = bytearray(STANDARD_SOUND_BODY)
        struct.pack_into("<I", expected, 0, sound_id)
        struct.pack_into("<I", expected, STANDARD_SOUND_MEDIA_OFFSET, media_id)
        struct.pack_into("<I", expected, STANDARD_SOUND_PARENT_OFFSET, parent_id)
        self.assertEqual(body, bytes(expected))
        self.assertEqual(len(body), STANDARD_SOUND_BODY_LENGTH)
        self.assertEqual(
            body[STANDARD_SOUND_POSITIONING_VECTOR_OFFSET],
            STANDARD_SOUND_POSITIONING_VECTOR,
        )

    def test_standard_body_rejects_invalid_unsigned_ids(self) -> None:
        cases = (
            (-1, 1, 1),
            (1, 0x1_0000_0000, 1),
            (1, 1, True),
        )
        for sound_id, media_id, parent_id in cases:
            with self.subTest(
                sound_id=sound_id,
                media_id=media_id,
                parent_id=parent_id,
            ):
                with self.assertRaisesRegex(
                    soundbank_editor.SoundBankError,
                    "unsigned 32-bit",
                ):
                    standard_voice_sound_body(
                        sound_id,
                        media_id,
                        direct_parent_id=parent_id,
                    )

    def test_insert_standard_sound_uses_the_synthetic_body(self) -> None:
        sound_id = 4_000_000_001
        media_id = 4_000_000_002
        parent_id = 4_000_000_003
        editor = soundbank_editor.HircEditor(make_hirc(), version=120)
        insert_standard_voice_sound(
            editor,
            sound_id,
            media_id,
            direct_parent_id=parent_id,
        )
        self.assertEqual(
            editor.object_body(soundbank_editor.HIRC_SOUND, sound_id),
            standard_voice_sound_body(
                sound_id,
                media_id,
                direct_parent_id=parent_id,
            ),
        )


if __name__ == "__main__":
    unittest.main()
