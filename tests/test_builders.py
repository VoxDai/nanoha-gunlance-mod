from __future__ import annotations

import struct
from pathlib import Path
import unittest

from builders.__main__ import PLANS
from builders.base import parse_mapping, validate_registry
from builders.wp07_gun_epvsp_shell import apply_edits as apply_wp07_edits
from tools import soundbank_editor


PROJECT_ROOT = Path(__file__).resolve().parents[1]

class MappingTests(unittest.TestCase):
    def test_registry_matches_every_mapping_and_soundbank(self) -> None:
        validate_registry(
            PLANS,
            PROJECT_ROOT / "mapping",
            PROJECT_ROOT / "original" / "soundbank",
        )
        self.assertEqual(
            {plan.name for plan in PLANS},
            {
                "cm_hitmark_epvsp",
                "hm_cm00_epvsp",
                "pl_prop_cmn",
                "wp07_gun_epvsp_shell",
                "wp_cmn_epvsp",
                "wp_gun_cmn",
            },
        )

    def test_current_mapping_replacements_and_unresolved_rows(self) -> None:
        parsed = {
            path.stem: parse_mapping(path, PROJECT_ROOT)
            for path in sorted((PROJECT_ROOT / "mapping").glob("*.md"))
        }
        self.assertEqual(
            [item.index for item in parsed["wp07_gun_epvsp_shell"].replacements],
            [2, 4, 9, 15, 19, 23, 27, 29, 30, 33, 34, 37],
        )
        self.assertEqual(
            [item.index for item in parsed["wp_cmn_epvsp"].replacements], [52]
        )
        for name in (
            "cm_hitmark_epvsp",
            "hm_cm00_epvsp",
            "pl_prop_cmn",
            "wp_gun_cmn",
        ):
            self.assertEqual(parsed[name].replacements, [])
        self.assertEqual(len(parsed["cm_hitmark_epvsp"].unresolved_rows), 1)
        self.assertEqual(len(parsed["wp_gun_cmn"].unresolved_rows), 1)


class Wp07SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = (
            PROJECT_ROOT
            / "original"
            / "soundbank"
            / "wp07_gun_epvsp_shell.nbnk"
        )
        bank = soundbank_editor.SoundBank.from_file(source)
        editor = soundbank_editor.SoundBankEditor(bank)
        cls.original_hirc = bank.hirc_payload
        apply_wp07_edits(editor)
        cls.changed_byte_count = editor.hirc.changed_byte_count
        cls.patched_hirc = editor.hirc.build()
        cls.patched = soundbank_editor.HircEditor(cls.patched_hirc)

    def test_exact_change_count_and_length(self) -> None:
        self.assertEqual(self.changed_byte_count, 54)
        self.assertEqual(len(self.patched_hirc), len(self.original_hirc))
        self.assertEqual(
            sum(a != b for a, b in zip(self.original_hirc, self.patched_hirc)), 54
        )

    def test_aux_overrides_and_bus_clear(self) -> None:
        for sound_id, flag_offset, bus_offset in (
            (46149961, 0x2B, 0x2C),
            (219848096, 0x2B, 0x2C),
            (641882349, 0x30, 0x31),
            (68448090, 0x30, 0x31),
            (196455745, 0x2B, 0x2C),
            (994484287, 0x2B, 0x2C),
        ):
            body = self.patched.object_body(0x02, sound_id)
            self.assertEqual(body[flag_offset], 0x0D)
            self.assertEqual(struct.unpack_from("<I", body, bus_offset)[0], 0)
        for sound_id in (862816411, 467996314):
            self.assertEqual(self.patched.object_body(0x02, sound_id)[0x26], 0x05)

    def test_paired_pitch_and_volume_values(self) -> None:
        for container_id, offset in (
            (246916390, 0x17),
            (505597934, 0x12),
            (885313651, 0x12),
        ):
            body = self.patched.object_body(0x05, container_id)
            self.assertEqual(struct.unpack_from("<f", body, offset)[0], 0.0)

        for sound_id, offset in (
            (641882349, 0x22),
            (467996314, 0x20),
            (68448090, 0x22),
            (862816411, 0x20),
        ):
            body = self.patched.object_body(0x02, sound_id)
            self.assertEqual(struct.unpack_from("<f", body, offset)[0], -6.5)

        for sound_id in (196455745, 994484287):
            body = self.patched.object_body(0x02, sound_id)
            self.assertEqual(body[0x1F:0x21], bytes((0x00, 0x0E)))
            self.assertEqual(struct.unpack_from("<f", body, 0x21)[0], -1.5)
            self.assertEqual(struct.unpack_from("<f", body, 0x25)[0], 100.0)

    def test_other_builders_are_hirc_noops(self) -> None:
        for plan in PLANS:
            if plan.name == "wp07_gun_epvsp_shell":
                continue
            bank = soundbank_editor.SoundBank.from_file(
                PROJECT_ROOT / "original" / "soundbank" / f"{plan.name}.nbnk"
            )
            editor = soundbank_editor.SoundBankEditor(bank)
            plan.apply_edits(editor)
            self.assertEqual(editor.build(), bank.to_bytes(), plan.name)
            self.assertEqual(editor.hirc.changed_byte_count, 0, plan.name)


if __name__ == "__main__":
    unittest.main()
