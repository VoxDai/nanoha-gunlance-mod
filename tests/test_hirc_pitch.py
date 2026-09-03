from __future__ import annotations

from dataclasses import FrozenInstanceError
import struct
import unittest

from tools import soundbank_editor as se
from tools.soundbank_editor import editor as compatibility_editor

from ._soundbank_fixtures import SOUNDBANK_ROOT, make_hirc

NODE_TYPES = (
    se.HIRC_SOUND,
    se.HIRC_RANDOM_SEQUENCE_CONTAINER,
    se.HIRC_SWITCH_CONTAINER,
    se.HIRC_ACTOR_MIXER,
)
ABSENT = se.HircPitchSettings(None, None)


def f32(value: float) -> bytes:
    return struct.pack("<f", value)


def bundle(*items: tuple[int, bytes]) -> bytes:
    return bytes([len(items), *(key for key, _ in items)]) + b"".join(
        value for _, value in items
    )


def node_prefix(
        kind: int,
        *,
        fx_count: int = 0,
        plugin_id: int = 0x00040001,
        plugin_parameters: bytes = b"",
) -> bytes:
    """An explicit v120 prefix, including object ID but not property tables."""
    body = struct.pack("<I", 10)
    if kind == se.HIRC_SOUND:
        body += struct.pack("<IBIIB", plugin_id, 0, 987654321, 128, 0)
        if plugin_id & 0x0F in (2, 5):
            body += struct.pack("<I", len(plugin_parameters)) + plugin_parameters
    body += bytes([1, fx_count])
    if fx_count:
        body += b"\x01"
        body += b"".join(
            struct.pack("<BIBB", index, 700 + index, 1, 0)
            for index in range(fx_count)
        )
    body += struct.pack("<BIIB", 1, 200, 300, 5)
    return body


def make_editor(kind: int, body: bytes, version: int = 120) -> se.HircEditor:
    return se.HircEditor(make_hirc((kind, 10, body[4:])), version=version)


def snapshot(editor: se.HircEditor) -> tuple:
    return (
        editor.build(),
        editor.changed_byte_count,
        editor.patched_objects,
        editor.rebuilt_objects,
        editor.resized_objects,
        editor.added_objects,
    )


class HircPitchTests(unittest.TestCase):
    def assert_rejected_unchanged(self, editor, call, pattern):
        before = snapshot(editor)
        with self.assertRaisesRegex(se.SoundBankError, pattern):
            call()
        self.assertEqual(snapshot(editor), before)

    def assert_pitch_rejected(self, editor, kind, pattern, *, expected=ABSENT, **args):
        self.assert_rejected_unchanged(
            editor,
            lambda: editor.set_pitch(kind, 10, expected=expected, **args),
            pattern,
        )

    def test_public_exports_and_immutable_settings(self):
        self.assertEqual(se.HIRC_ACTOR_MIXER, 0x07)
        self.assertIs(compatibility_editor.HircPitchSettings, se.HircPitchSettings)
        self.assertEqual(compatibility_editor.HIRC_ACTOR_MIXER, 0x07)
        for module in (se, compatibility_editor):
            self.assertIn("HircPitchSettings", module.__all__)
            self.assertIn("HIRC_ACTOR_MIXER", module.__all__)
        with self.assertRaises(FrozenInstanceError):
            ABSENT.base_cents = 1

    def test_read_absence_explicit_zero_and_nonzero_for_all_node_types(self):
        for kind in NODE_TYPES:
            for base, random, expected in (
                    (bundle(), bundle(), ABSENT),
                    (bundle((2, f32(0))), bundle(), se.HircPitchSettings(0, None)),
                    (bundle(), bundle((2, f32(0) * 2)), se.HircPitchSettings(None, (0, 0))),
                    (
                            bundle((0, f32(-6)), (2, f32(-200)), (14, f32(100))),
                            bundle((0, f32(-2) + f32(1)), (2, f32(-50) + f32(25))),
                            se.HircPitchSettings(-200, (-50, 25)),
                    ),
            ):
                with self.subTest(kind=kind, expected=expected):
                    editor = make_editor(kind, node_prefix(kind) + base + random + b"tail")
                    before = snapshot(editor)
                    self.assertEqual(editor.pitch_settings(kind, 10), expected)
                    self.assertEqual(snapshot(editor), before)

    def test_insert_either_or_both_properties_in_all_node_types(self):
        # NaN/ID-like bit patterns in OTHER properties must remain opaque.
        other_base = ((0, f32(-6)), (14, bytes.fromhex("efbeadde")), (240, b"\xff" * 4))
        other_random = ((0, f32(-2) + f32(1)), (240, b"\xff" * 8))
        suffix = b"\xd9\x03positioning-aux-rtpc-and-children\x00"
        for kind in NODE_TYPES:
            for args, result, growth in (
                    ({"base_cents": 0}, se.HircPitchSettings(0, None), 5),
                    ({"random_range_cents": (-75, 25)}, se.HircPitchSettings(None, (-75, 25)), 9),
                    (
                            {"base_cents": -200, "random_range_cents": (-50, 50)},
                            se.HircPitchSettings(-200, (-50, 50)),
                            14,
                    ),
            ):
                with self.subTest(kind=kind, args=args):
                    prefix = node_prefix(kind, fx_count=2)
                    body = prefix + bundle(*other_base) + bundle(*other_random) + suffix
                    editor = make_editor(kind, body)
                    self.assertEqual(editor.set_pitch(kind, 10, expected=ABSENT, **args), result)
                    base_items = list(other_base)
                    range_items = list(other_random)
                    if result.base_cents is not None:
                        base_items.insert(1, (2, f32(result.base_cents)))
                    if result.random_range_cents is not None:
                        low, high = result.random_range_cents
                        range_items.insert(1, (2, f32(low) + f32(high)))
                    expected_body = prefix + bundle(*base_items) + bundle(*range_items) + suffix
                    self.assertEqual(editor.object_body(kind, 10), expected_body)
                    self.assertEqual(editor.resized_objects, ((kind, 10, len(body), len(body) + growth),))
                    self.assertEqual(editor.rebuilt_objects, ((kind, 10),))
                    self.assertEqual(editor.patched_objects, ())
                    reread = se.HircEditor(editor.build())
                    self.assertEqual(reread.pitch_settings(kind, 10), result)
                    # Same-value requests are also no-ops after a structural edit.
                    before = snapshot(editor)
                    editor.set_pitch(kind, 10, expected=result, **args)
                    self.assertEqual(snapshot(editor), before)

    def test_insert_pitch_at_start_middle_and_end(self):
        for ids in ((), (0,), (0, 1, 14), (3, 14)):
            with self.subTest(ids=ids):
                base_items = [(key, bytes([key]) * 4) for key in ids]
                range_items = [(key, bytes([key]) * 8) for key in ids]
                prefix = node_prefix(se.HIRC_SOUND)
                body = prefix + bundle(*base_items) + bundle(*range_items) + b"tail"
                editor = make_editor(se.HIRC_SOUND, body)
                editor.set_pitch(
                    se.HIRC_SOUND, 10, expected=ABSENT,
                    base_cents=100, random_range_cents=(0, 0),
                )
                self.assertEqual(
                    editor.object_body(se.HIRC_SOUND, 10),
                    prefix
                    + bundle(*sorted(base_items + [(2, f32(100))]))
                    + bundle(*sorted(range_items + [(2, f32(0) * 2)]))
                    + b"tail",
                )

    def test_insert_one_property_while_editing_the_other(self):
        for kind in NODE_TYPES:
            for initial in (
                    se.HircPitchSettings(None, (-50, 50)),
                    se.HircPitchSettings(-200, None),
            ):
                with self.subTest(kind=kind, initial=initial):
                    prefix = node_prefix(kind)
                    base = bundle() if initial.base_cents is None else bundle((2, f32(-200)))
                    random = bundle() if initial.random_range_cents is None else bundle((2, f32(-50) + f32(50)))
                    editor = make_editor(kind, prefix + base + random + b"tail")
                    result = editor.set_pitch(
                        kind, 10, expected=initial,
                        base_cents=100, random_range_cents=(-25, 25),
                    )
                    self.assertEqual(result, se.HircPitchSettings(100, (-25, 25)))
                    self.assertEqual(
                        editor.object_body(kind, 10),
                        prefix + bundle((2, f32(100)))
                        + bundle((2, f32(-25) + f32(25))) + b"tail",
                    )

    def test_equal_length_edits_preserve_unspecified_settings_and_other_bytes(self):
        initial = se.HircPitchSettings(-200, (-50, 50))
        for kind in NODE_TYPES:
            for args, desired in (
                    ({"base_cents": 100}, se.HircPitchSettings(100, (-50, 50))),
                    ({"random_range_cents": (0, 0)}, se.HircPitchSettings(-200, (0, 0))),
                    ({"base_cents": 0, "random_range_cents": (-10, 30)}, se.HircPitchSettings(0, (-10, 30))),
            ):
                with self.subTest(kind=kind, args=args):
                    prefix = node_prefix(kind)
                    base = bundle((0, f32(-6)), (2, f32(-200)), (14, f32(100)))
                    ranges = bundle((2, f32(-50) + f32(50)))
                    body = prefix + base + ranges + b"opaque-tail"
                    editor = make_editor(kind, body)
                    result = editor.set_pitch(kind, 10, expected=initial, **args)
                    self.assertEqual(result, desired)
                    expected_body = (
                            prefix + bundle((0, f32(-6)), (2, f32(desired.base_cents)), (14, f32(100)))
                            + bundle((2, f32(desired.random_range_cents[0]) + f32(desired.random_range_cents[1])))
                            + b"opaque-tail"
                    )
                    self.assertEqual(editor.object_body(kind, 10), expected_body)
                    self.assertEqual(
                        editor.changed_byte_count,
                        sum(a != b for a, b in zip(body, expected_body)),
                    )
                    self.assertEqual(editor.resized_objects, ())
                    self.assertEqual(editor.rebuilt_objects, ())
                    self.assertEqual(editor.patched_objects, ((kind, 10),))
                    before = snapshot(editor)
                    editor.set_pitch(kind, 10, expected=result, **args)
                    self.assertEqual(snapshot(editor), before)

    def test_source_plugin_parameters_and_fx_are_preserved(self):
        for plugin_id in (0x00040001, 0x00650002, 0x01950005):
            for parameters in (b"", b"\x01\x02" + f32(777) * 3):
                with self.subTest(plugin_id=plugin_id, parameters=parameters):
                    prefix = node_prefix(
                        se.HIRC_SOUND, plugin_id=plugin_id,
                        plugin_parameters=parameters, fx_count=2,
                    )
                    body = prefix + b"\x00\x00" + b"opaque-tail"
                    editor = make_editor(se.HIRC_SOUND, body)
                    editor.set_pitch(se.HIRC_SOUND, 10, expected=ABSENT, base_cents=50)
                    self.assertEqual(
                        editor.object_body(se.HIRC_SOUND, 10),
                        prefix + bundle((2, f32(50))) + b"\x00opaque-tail",
                    )

    def test_float32_guards_rounding_signed_zero_and_noop(self):
        kind = se.HIRC_SOUND
        body = node_prefix(kind) + bundle((2, f32(0.1))) + bundle((2, f32(-0.2) + f32(0.3)))
        editor = make_editor(kind, body)
        before = snapshot(editor)
        result = editor.set_pitch(kind, 10, expected=se.HircPitchSettings(0.1, (-0.2, 0.3)), base_cents=0.1)
        self.assertEqual(result.base_cents, struct.unpack("<f", f32(0.1))[0])
        self.assertEqual(snapshot(editor), before)
        negative_zero = make_editor(kind, node_prefix(kind) + bundle((2, f32(-0.0))) + b"\x00")
        self.assert_rejected_unchanged(
            negative_zero,
            lambda: negative_zero.set_pitch(kind, 10, expected=se.HircPitchSettings(0.0, None), base_cents=1),
            "expected pitch",
        )
        negative_zero.set_pitch(kind, 10, expected=se.HircPitchSettings(-0.0, None), base_cents=0.0)
        self.assertEqual(f32(negative_zero.pitch_settings(kind, 10).base_cents), f32(0.0))

    def test_guards_cover_presence_and_both_fields(self):
        kind = se.HIRC_SOUND
        body = node_prefix(kind) + bundle() + bundle((2, f32(-50) + f32(50)))
        editor = make_editor(kind, body)
        for expected in (ABSENT, se.HircPitchSettings(0, (-50, 50)), se.HircPitchSettings(None, (-25, 25))):
            with self.subTest(expected=expected):
                self.assert_pitch_rejected(
                    editor, kind, "expected pitch", expected=expected, base_cents=100
                )
        self.assert_pitch_rejected(
            editor, kind, "HircPitchSettings", expected=None, base_cents=100
        )
        self.assert_pitch_rejected(
            editor, kind, "at least one", expected=se.HircPitchSettings(None, (-50, 50))
        )
        self.assert_rejected_unchanged(
            editor,
            lambda: editor.set_pitch(kind, 999, expected=ABSENT, base_cents=1),
            "object not found",
        )

    def test_invalid_numbers_and_ranges_are_atomic(self):
        kind = se.HIRC_SOUND
        editor = make_editor(kind, node_prefix(kind) + b"\x00\x00")
        for bad in (True, False, "50", float("nan"), float("inf"), -float("inf"), 1e40, 10 ** 400, object()):
            with self.subTest(bad=bad):
                for args in ({"base_cents": bad}, {"base_cents": 10, "random_range_cents": (0, bad)}):
                    self.assert_pitch_rejected(editor, kind, "float32", **args)
                self.assert_pitch_rejected(
                    editor, kind, "float32",
                    expected=se.HircPitchSettings(bad, None), base_cents=10,
                )
        for bad in ((50, -50), (1.00000001, 1.0), (0,), (0, 1, 2), [0, 1], "range"):
            with self.subTest(bad=bad):
                self.assert_pitch_rejected(
                    editor, kind, "random range", base_cents=10, random_range_cents=bad
                )

    def test_rejects_unsupported_versions_types_and_invalid_identifiers(self):
        for kind in NODE_TYPES:
            editor = make_editor(kind, node_prefix(kind) + b"\x00\x00", version=119)
            with self.assertRaisesRegex(se.SoundBankError, "v120"):
                editor.pitch_settings(kind, 10)
            self.assert_pitch_rejected(editor, kind, "v120", base_cents=0)
        for kind in (1, 3, 4, 8, 9, 10):
            editor = make_editor(kind, struct.pack("<I", 10) + bytes(30))
            with self.assertRaisesRegex(se.SoundBankError, "unsupported"):
                editor.pitch_settings(kind, 10)
            self.assert_pitch_rejected(editor, kind, "unsupported", base_cents=0)
        editor = make_editor(se.HIRC_SOUND, node_prefix(se.HIRC_SOUND) + b"\x00\x00")
        for kind, ident in ((True, 10), (2.0, 10), (2, True), (2, -1)):
            with self.subTest(kind=kind, ident=ident):
                self.assert_rejected_unchanged(
                    editor,
                    lambda: editor.set_pitch(kind, ident, expected=ABSENT, base_cents=0),
                    "must be",
                )

    def test_rejects_truncated_prefix_and_tables(self):
        for kind in NODE_TYPES:
            full = (
                    node_prefix(kind, fx_count=2, plugin_id=0x00650002, plugin_parameters=b"source")
                    + bundle((0, f32(-3)), (2, f32(100)))
                    + bundle((2, f32(-50) + f32(50)))
            )
            for cut in range(4, len(full)):
                with self.subTest(kind=kind, cut=cut):
                    editor = make_editor(kind, full[:cut])
                    with self.assertRaises(se.SoundBankError):
                        editor.pitch_settings(kind, 10)
                    self.assert_pitch_rejected(
                        editor, kind, "exceeds",
                        expected=se.HircPitchSettings(100, (-50, 50)), base_cents=0,
                    )

    def test_rejects_duplicate_unordered_and_nonfinite_pitch_properties(self):
        kind = se.HIRC_SOUND
        malformed = (
            (bundle((2, f32(1)), (2, f32(2))) + bundle(), "duplicate"),
            (bundle((14, f32(1)), (2, f32(2))) + bundle(), "unordered"),
            (bundle() + bundle((2, bytes(8)), (2, bytes(8))), "duplicate"),
            (bundle() + bundle((14, bytes(8)), (2, bytes(8))), "unordered"),
            (bundle((2, f32(float("nan")))) + bundle(), "finite"),
            (bundle() + bundle((2, f32(-1) + f32(float("inf")))), "finite"),
            (bundle() + bundle((2, f32(1) + f32(-1))), "min <= max"),
        )
        for tables, error in malformed:
            with self.subTest(error=error, tables=tables):
                editor = make_editor(kind, node_prefix(kind) + tables)
                with self.assertRaisesRegex(se.SoundBankError, error):
                    editor.pitch_settings(kind, 10)
                self.assert_pitch_rejected(editor, kind, error, base_cents=0)

    def test_property_count_overflow_is_atomic_even_when_other_table_can_grow(self):
        kind = se.HIRC_SOUND
        ids = [key for key in range(256) if key != 2]
        for base, random in (
                (bundle(*[(key, bytes(4)) for key in ids]), bundle()),
                (bundle(), bundle(*[(key, bytes(8)) for key in ids])),
        ):
            editor = make_editor(kind, node_prefix(kind) + base + random)
            self.assert_pitch_rejected(
                editor, kind, "exceed 255", base_cents=1, random_range_cents=(-1, 1)
            )

    def test_later_patch_conflict_does_not_apply_earlier_pitch_field(self):
        kind = se.HIRC_SOUND
        prefix = node_prefix(kind)
        base = bundle((2, f32(100)))
        body = prefix + base + bundle((2, f32(-50) + f32(50)))
        editor = make_editor(kind, body)
        high_offset = len(prefix) + len(base) + 2 + 4
        editor.patch_float(kind, 10, high_offset, 50, 25, label="prior range edit")
        self.assert_pitch_rejected(
            editor, kind, "overlaps",
            expected=se.HircPitchSettings(100, (-50, 25)),
            base_cents=0, random_range_cents=(0, 0),
        )

    def test_unrelated_patch_composition_and_rebuild_conflicts(self):
        kind = se.HIRC_SOUND
        prefix = node_prefix(kind)
        body = prefix + bundle((0, f32(-6)), (2, f32(100))) + bundle()
        editor = make_editor(kind, body)
        volume_offset = len(prefix) + 3
        editor.patch_float(kind, 10, volume_offset, -6, -3, label="volume")
        editor.set_pitch(kind, 10, expected=se.HircPitchSettings(100, None), base_cents=200)
        self.assertEqual(struct.unpack_from("<f", editor.object_body(kind, 10), volume_offset)[0], -3)
        self.assert_pitch_rejected(
            editor, kind, "already edited",
            expected=se.HircPitchSettings(200, None), random_range_cents=(-50, 50),
        )
        rebuilt = make_editor(kind, body)
        rebuilt.set_pitch(kind, 10, expected=se.HircPitchSettings(100, None), random_range_cents=(-50, 50))
        self.assert_pitch_rejected(
            rebuilt, kind, "already rebuilt",
            expected=se.HircPitchSettings(100, (-50, 50)), base_cents=200,
        )
        self.assert_rejected_unchanged(
            rebuilt,
            lambda: rebuilt.patch_float(kind, 10, volume_offset, -6, -3, label="volume"),
            "already rebuilt",
        )


class OriginalBankPitchTests(unittest.TestCase):
    def test_read_original_settings_without_mutation(self):
        cases = (
            ("wp07_gun_epvsp_shell.nbnk", se.HIRC_RANDOM_SEQUENCE_CONTAINER, 145848034,
             se.HircPitchSettings(None, (-50, 50))),
            ("wp07_gun_epvsp_shell.nbnk", se.HIRC_SOUND, 535190438, ABSENT),
            ("pl_prop_cmn.nbnk", se.HIRC_ACTOR_MIXER, 272869939, se.HircPitchSettings(None, (-50, 50))),
            ("hm_cm00_epvsp.nbnk", se.HIRC_SWITCH_CONTAINER, 368774789, ABSENT),
        )
        for name, kind, ident, expected in cases:
            with self.subTest(bank=name, ident=ident):
                bank = se.SoundBank.from_file(SOUNDBANK_ROOT / name)
                editor = se.SoundBankEditor(bank)
                before = editor.summary
                self.assertEqual(editor.hirc.pitch_settings(kind, ident), expected)
                self.assertEqual(editor.build(), bank.to_bytes())
                self.assertEqual(editor.summary, before)

    def test_original_bank_edits_preserve_media_routes_and_order(self):
        cases = (
            (
                "wp07_gun_epvsp_shell.nbnk", se.HIRC_RANDOM_SEQUENCE_CONTAINER, 145848034,
                se.HircPitchSettings(None, (-50, 50)),
                {"random_range_cents": (0, 0)}, 0, 0x18,
            ),
            (
                "wp07_gun_epvsp_shell.nbnk", se.HIRC_SOUND, 535190438, ABSENT,
                {"base_cents": -100, "random_range_cents": (-10, 30)}, 14, None,
            ),
            (
                "pl_prop_cmn.nbnk", se.HIRC_ACTOR_MIXER, 272869939,
                se.HircPitchSettings(None, (-50, 50)),
                {"random_range_cents": (-25, 25)}, 0, 0x1D,
            ),
            (
                "hm_cm00_epvsp.nbnk", se.HIRC_SWITCH_CONTAINER, 368774789, ABSENT,
                {"base_cents": 50}, 5, None,
            ),
        )
        for name, kind, ident, expected, args, growth, offset in cases:
            with self.subTest(bank=name, ident=ident):
                bank = se.SoundBank.from_file(SOUNDBANK_ROOT / name)
                editor = se.SoundBankEditor(bank)
                original_objects = editor.hirc.objects()
                old = editor.hirc.object_body(kind, ident)
                result = editor.hirc.set_pitch(kind, ident, expected=expected, **args)
                new = editor.hirc.object_body(kind, ident)
                if offset is not None:
                    golden = bytearray(old)
                    struct.pack_into("<ff", golden, offset, *args["random_range_cents"])
                    self.assertEqual(new, bytes(golden))
                else:
                    # Determine the property block boundary from the original
                    # public inspection evidence, then check prefix and tail.
                    property_start = 0x1E if kind == se.HIRC_SOUND else 0x10
                    base_count = old[property_start]
                    random_start = property_start + 1 + 5 * base_count
                    end = random_start + 1 + 9 * old[random_start]
                    self.assertEqual(new[:property_start], old[:property_start])
                    self.assertEqual(new[end + growth:], old[end:])
                rebuilt = editor.validate()
                diff = bank.diff(rebuilt)
                self.assertEqual(diff.changed_chunks, (b"HIRC",))
                self.assertEqual(diff.changed_hirc_objects, ((kind, ident),))
                self.assertEqual(diff.added_hirc_objects, ())
                self.assertEqual(diff.removed_hirc_objects, ())
                for chunk in bank.chunks:
                    if chunk.tag != b"HIRC":
                        self.assertEqual(rebuilt.chunk(chunk.tag).raw, chunk.raw)
                hirc = se.HircEditor(rebuilt.hirc_payload)
                self.assertEqual(hirc.pitch_settings(kind, ident), result)
                self.assertEqual(
                    [(o.object_type, o.object_id) for o in hirc.objects()],
                    [(o.object_type, o.object_id) for o in original_objects],
                )
                self.assertEqual(editor.summary.hirc_size_delta, growth)
                self.assertEqual(editor.summary.hirc_changed_bytes, sum(a != b for a, b in zip(old, new)))
                self.assertEqual(
                    editor.summary.resized_hirc_objects,
                    ((kind, ident, len(old), len(new)),) if growth else (),
                )
                if kind == se.HIRC_SWITCH_CONTAINER:
                    before_topology = se.HircEditor(bank.hirc_payload).switch_container_topology(ident)
                    self.assertEqual(hirc.switch_container_topology(ident), before_topology)


if __name__ == "__main__":
    unittest.main()
