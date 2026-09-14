"""Build overhead-smash replacement and ordinary/charged firing silence."""

from __future__ import annotations

from tools import soundbank_editor

from .base import WwevBuildPlan, run_single_cli


DONOR_REQUEST = 1409
DONOR_EVENT_ID = 967_571_325
DONOR_MODE = 4
DONOR_RECORD_SHA256 = (
    "73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507"
)
NEW_REQUEST = 6595
NEW_EVENT_ID = 2_866_569_635
NEW_RECORD_SHA256 = (
    "c430e117fad198b99f94187fc7ff7c3ca1140c1ae618ad306037c16d9f4a7ed6"
)
FIRING_VOICE_REQUEST = 6608
FIRING_VOICE_EVENT_ID = 2_825_008_231
FIRING_VOICE_RECORD_SHA256 = (
    "2b21f2a836c096e164751adfcad860aa8f919fea0a857f11fa64ac4de40798c4"
)


def apply_edits(editor: soundbank_editor.WwevEditor) -> None:
    """Clone the original grunt request for Accel and isolated firing silence."""

    editor.append_cloned_record(
        donor_request=DONOR_REQUEST,
        expected_donor_event_id=DONOR_EVENT_ID,
        expected_donor_mode=DONOR_MODE,
        expected_donor_sha256=DONOR_RECORD_SHA256,
        new_request=NEW_REQUEST,
        new_event_id=NEW_EVENT_ID,
    )
    record = editor.append_cloned_record(
        donor_request=DONOR_REQUEST, expected_donor_event_id=DONOR_EVENT_ID,
        expected_donor_mode=DONOR_MODE, expected_donor_sha256=DONOR_RECORD_SHA256,
        new_request=FIRING_VOICE_REQUEST, new_event_id=FIRING_VOICE_EVENT_ID,
    )
    if record.sha256 != FIRING_VOICE_RECORD_SHA256:
        raise soundbank_editor.WwevError("firing silence record body differs")


EXPECTED_SUMMARY = soundbank_editor.WwevEditSummary(
    record_count_before=100,
    record_count_after=102,
    appended_size=258,
    edits=(
        soundbank_editor.WwevRecordEdit(
            donor_record_index=20,
            donor_request=DONOR_REQUEST,
            donor_event_id=DONOR_EVENT_ID,
            added_record_index=101,
            new_request=NEW_REQUEST,
            new_event_id=NEW_EVENT_ID,
            appended_size=129,
        ),
        soundbank_editor.WwevRecordEdit(
            donor_record_index=20, donor_request=DONOR_REQUEST,
            donor_event_id=DONOR_EVENT_ID, added_record_index=102,
            new_request=FIRING_VOICE_REQUEST, new_event_id=FIRING_VOICE_EVENT_ID,
            appended_size=129,
        ),
    ),
)


PLAN = WwevBuildPlan(
    name="pl_voice",
    design_ids=("wp_gun_cmn.overhead_smash", "wp07_gun_epvsp_shell.charged_shelling"),
    source="original/wwev/pl_voice.wwev",
    target="sound/pl/pl_voice.wwev",
    expected_source_sha256=(
        "7667e0caca4bb7d4d2c3dda62085db3a9a8b68992b9f7a089aaed9dc84afa696"
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
