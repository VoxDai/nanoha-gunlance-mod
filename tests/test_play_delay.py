"""Synthetic Wwise v120 Play Action delay layouts and validation."""

import struct
import unittest

from tools import soundbank_editor as se


class PlayDelayTests(unittest.TestCase):
    def setUp(self):
        self.editor = se.HircEditor(bytes(4))
        self.prefix = struct.pack("<IHI", 1, se.ACTION_PLAY, 2)
        self.suffix = struct.pack("<BI", 4, 3)

    def test_immediate_and_fixed_delay_legacy_encoding(self):
        self.assertEqual(self.editor.create_play_action(1, 2, 3),
                         self.prefix + bytes(3) + self.suffix)
        self.assertEqual(
            self.editor.create_play_action(1, 2, 3, delay_ms=7),
            self.prefix + struct.pack("<BBBI", 0, 1, 0x0F, 7) + bytes(1) + self.suffix,
        )

    def test_random_delay_writes_explicit_base_and_range(self):
        for base, lo, hi in ((0, 0, 50), (100, -100, 100)):
            with self.subTest(base=base, lo=lo, hi=hi):
                body = self.editor.create_play_action(
                    1, 2, 3, delay_ms=base, delay_random_range_ms=(lo, hi)
                )
                self.assertEqual(body, self.prefix + struct.pack(
                    "<BBBIBBii", 0, 1, 0x0F, base, 1, 0x0F, lo, hi
                ) + self.suffix)

    def test_rejects_invalid_random_delay(self):
        for bounds in ((-1, 50), (50, 0), (0, 0x80000000), (0, 1.5), (True, 50), (0,)):
            with self.subTest(bounds=bounds), self.assertRaises(se.SoundBankError):
                self.editor.create_play_action(1, 2, 3, delay_random_range_ms=bounds)
        with self.assertRaises(se.SoundBankError):
            self.editor.create_play_action(1, 2, 3, delay_ms=0x7FFFFFFF, delay_random_range_ms=(0, 1))
