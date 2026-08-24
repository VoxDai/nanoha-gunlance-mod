"""Build the stationary-draw request-to-Event WWEV record."""

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


def apply_edits(editor: soundbank_editor.WwevEditor) -> None:
    """Clone the complete guarded donor and change only ReqNo and Event ID."""

    editor.append_cloned_record(
        donor_request=DONOR_REQUEST,
        expected_donor_event_id=DONOR_EVENT_ID,
        expected_donor_mode=DONOR_MODE,
        expected_donor_sha256=DONOR_RECORD_SHA256,
        new_request=NEW_REQUEST,
        new_event_id=NEW_EVENT_ID,
    )


EXPECTED_SUMMARY = soundbank_editor.WwevEditSummary(
    record_count_before=43,
    record_count_after=44,
    appended_size=129,
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
    ),
)


PLAN = WwevBuildPlan(
    name="hm_wp07_snd_ev",
    design_ids=("wp_gun_cmn.stationary_draw",),
    source="original/wwev/hm_wp07_snd_ev.wwev",
    target="sound/pl/hm_wp07_snd_ev.wwev",
    expected_source_sha256=(
        "82c7162f3cb502e3ce3e1e7c1e6ff4823d373a764148d6d761f675420bcd2a0f"
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
    expected_output_sha256=(
        "8fb3c6134a50ac094540a8134ccb92948cc676dff87ef94afecc87f80194dd04"
    ),
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
