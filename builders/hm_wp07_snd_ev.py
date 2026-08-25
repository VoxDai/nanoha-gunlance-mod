"""Build stationary-draw and overhead-smash request-to-Event records."""

from __future__ import annotations

from tools import soundbank_editor

from .base import WwevBuildPlan, run_single_cli


DONOR_REQUEST = 6470
DONOR_EVENT_ID = 3_567_942_167
DONOR_MODE = 2
DONOR_RECORD_SHA256 = (
    "1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f"
)
NEW_REQUEST = 6592
NEW_EVENT_ID = 3_176_129_810

OVERHEAD_DONOR_REQUEST = 6505
OVERHEAD_DONOR_EVENT_ID = 1_129_041_389
OVERHEAD_DONOR_MODE = 100
OVERHEAD_DONOR_RECORD_SHA256 = (
    "716e10c4bb841822f8d5b178580980d654f4367e5753403474bc8b50cfb7f2c8"
)
OVERHEAD_NEW_REQUEST = 6593
OVERHEAD_NEW_EVENT_ID = 2_866_569_635


def apply_edits(editor: soundbank_editor.WwevEditor) -> None:
    """Clone both complete donors and change only ReqNo and Event ID."""

    editor.append_cloned_record(
        donor_request=DONOR_REQUEST,
        expected_donor_event_id=DONOR_EVENT_ID,
        expected_donor_mode=DONOR_MODE,
        expected_donor_sha256=DONOR_RECORD_SHA256,
        new_request=NEW_REQUEST,
        new_event_id=NEW_EVENT_ID,
    )
    editor.append_cloned_record(
        donor_request=OVERHEAD_DONOR_REQUEST,
        expected_donor_event_id=OVERHEAD_DONOR_EVENT_ID,
        expected_donor_mode=OVERHEAD_DONOR_MODE,
        expected_donor_sha256=OVERHEAD_DONOR_RECORD_SHA256,
        new_request=OVERHEAD_NEW_REQUEST,
        new_event_id=OVERHEAD_NEW_EVENT_ID,
    )


EXPECTED_SUMMARY = soundbank_editor.WwevEditSummary(
    record_count_before=43,
    record_count_after=45,
    appended_size=258,
    edits=(
        soundbank_editor.WwevRecordEdit(
            donor_record_index=17,
            donor_request=DONOR_REQUEST,
            donor_event_id=DONOR_EVENT_ID,
            added_record_index=44,
            new_request=NEW_REQUEST,
            new_event_id=NEW_EVENT_ID,
            appended_size=129,
        ),
        soundbank_editor.WwevRecordEdit(
            donor_record_index=28,
            donor_request=OVERHEAD_DONOR_REQUEST,
            donor_event_id=OVERHEAD_DONOR_EVENT_ID,
            added_record_index=45,
            new_request=OVERHEAD_NEW_REQUEST,
            new_event_id=OVERHEAD_NEW_EVENT_ID,
            appended_size=129,
        ),
    ),
)


PLAN = WwevBuildPlan(
    name="hm_wp07_snd_ev",
    design_ids=(
        "wp_gun_cmn.stationary_draw",
        "wp_gun_cmn.overhead_smash",
    ),
    source="original/wwev/hm_wp07_snd_ev.wwev",
    target="sound/pl/hm_wp07_snd_ev.wwev",
    expected_source_sha256=(
        "82c7162f3cb502e3ce3e1e7c1e6ff4823d373a764148d6d761f675420bcd2a0f"
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
    expected_output_sha256=(
        "1818d0547237ef6bed7900ad3fa2bbecda2e040910b88760800c6fdc9b7a6222"
    ),
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
