"""Synthetic project inputs and plans for generic builder tests."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import wave

from builders.base import (
    LmtBuildPlan,
    MediaAddition,
    ReferenceInput,
    SoundBankBuildPlan,
    WwevBuildPlan,
)
from tools import soundbank_editor

from ._event_format_fixtures import make_test_lmt, make_test_wwev
from ._soundbank_fixtures import make_test_soundbank


TEST_BANK_ID = 123_456_789
TEST_MEDIA_ID = 987_654_321
ADDED_MEDIA_ID = 987_654_322
TEST_DESIGN_ID = "test.synthetic"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def apply_test_lmt(editor: soundbank_editor.LmtEditor) -> None:
    editor.replace_request(
        motion_id=0,
        event_group="EventGroup06",
        slot="A",
        request_keyframe_frame=0.0,
        expected_request=6485,
        replacement_request=6500,
        expected_trigger_frames=(12.0,),
    )


def apply_test_wwev(editor: soundbank_editor.WwevEditor) -> None:
    donor = editor.records_for_request(6485)[0]
    editor.append_cloned_record(
        donor_request=6485,
        expected_donor_event_id=donor.event_id,
        expected_donor_mode=donor.mode,
        expected_donor_sha256=donor.sha256,
        new_request=6500,
        new_event_id=3_000_000_001,
    )


def _lmt_summary() -> soundbank_editor.LmtEditSummary:
    editor = soundbank_editor.LmtEditor.from_bytes(make_test_lmt())
    apply_test_lmt(editor)
    return editor.summary


def _wwev_summary() -> soundbank_editor.WwevEditSummary:
    editor = soundbank_editor.WwevEditor.from_bytes(make_test_wwev())
    apply_test_wwev(editor)
    return editor.summary


TEST_LMT_SUMMARY = _lmt_summary()
TEST_WWEV_SUMMARY = _wwev_summary()
TEST_BANK_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=((2, ADDED_MEDIA_ID),),
    hirc_changed_bytes=0,
    added_hirc_objects=(),
    resized_hirc_objects=(),
    hirc_size_delta=0,
)


@dataclass(frozen=True)
class SyntheticBuilderProject:
    root: Path
    bank_bytes: bytes
    lmt_bytes: bytes
    wwev_bytes: bytes
    reference_bytes: bytes

    @classmethod
    def create(cls, root: Path) -> SyntheticBuilderProject:
        root = root.resolve()
        bank_bytes = make_test_soundbank(
            bank_id=TEST_BANK_ID,
            media_id=TEST_MEDIA_ID,
        )
        lmt_bytes = make_test_lmt()
        wwev_bytes = make_test_wwev()
        reference_bytes = b"synthetic immutable reference\n"
        paths = {
            "original/nbnk/test.nbnk": bank_bytes,
            "original/reference.bin": reference_bytes,
            "original/lmt/test.lmt": lmt_bytes,
            "original/wwev/test.wwev": wwev_bytes,
        }
        for relative, payload in paths.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        audio = root / "audio/test.wav"
        audio.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(audio), "wb") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(48_000)
            wav.writeframes(bytes(16))
        return cls(root, bank_bytes, lmt_bytes, wwev_bytes, reference_bytes)

    def soundbank_plan(self) -> SoundBankBuildPlan:
        return SoundBankBuildPlan(
            name="test_bank",
            design_ids=(TEST_DESIGN_ID,),
            source="original/nbnk/test.nbnk",
            target="sound/wwise/Windows/test.nbnk",
            expected_source_sha256=_sha256(self.bank_bytes),
            expected_bank_id=TEST_BANK_ID,
            media_additions=(
                MediaAddition(2, ADDED_MEDIA_ID, "audio/test.wav", wem_channels=1),
            ),
            reference_inputs=(
                ReferenceInput(
                    "original/reference.bin",
                    _sha256(self.reference_bytes),
                ),
            ),
            apply_edits=lambda _editor: None,
            expected_summary=TEST_BANK_SUMMARY,
        )

    def lmt_plan(self) -> LmtBuildPlan:
        return LmtBuildPlan(
            name="test_lmt",
            design_ids=(TEST_DESIGN_ID,),
            source="original/lmt/test.lmt",
            target="motion/test.lmt",
            expected_source_sha256=_sha256(self.lmt_bytes),
            apply_edits=apply_test_lmt,
            expected_summary=TEST_LMT_SUMMARY,
        )

    def wwev_plan(self) -> WwevBuildPlan:
        return WwevBuildPlan(
            name="test_wwev",
            design_ids=(TEST_DESIGN_ID,),
            source="original/wwev/test.wwev",
            target="sound/test.wwev",
            expected_source_sha256=_sha256(self.wwev_bytes),
            apply_edits=apply_test_wwev,
            expected_summary=TEST_WWEV_SUMMARY,
        )
