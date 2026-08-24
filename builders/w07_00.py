"""Build the stationary-draw request substitution in w07_00.lmt."""

from __future__ import annotations

from tools import soundbank_editor

from .base import LmtBuildPlan, run_single_cli


MOTION_ID = 2
EVENT_GROUP = "EventGroup06"
SLOT = "B"
REQUEST_KEYFRAME = 0.0
TRIGGER_FRAMES = (9.0,)
OLD_REQUEST = 6470
NEW_REQUEST = 6592
REQUEST_OFFSET = 0xCC50


def apply_edits(editor: soundbank_editor.LmtEditor) -> None:
    """Guard and replace the one TIML slot-B request assignment."""

    editor.replace_request(
        motion_id=MOTION_ID,
        event_group=EVENT_GROUP,
        slot=SLOT,
        request_keyframe_frame=REQUEST_KEYFRAME,
        expected_request=OLD_REQUEST,
        replacement_request=NEW_REQUEST,
        expected_trigger_frames=TRIGGER_FRAMES,
    )


EXPECTED_SUMMARY = soundbank_editor.LmtEditSummary(
    changed_byte_count=1,
    edits=(
        soundbank_editor.LmtRequestEdit(
            motion_id=MOTION_ID,
            event_group=EVENT_GROUP,
            slot=SLOT,
            request_keyframe_frame=REQUEST_KEYFRAME,
            trigger_frames=TRIGGER_FRAMES,
            offset=REQUEST_OFFSET,
            old_request=OLD_REQUEST,
            new_request=NEW_REQUEST,
            changed_byte_count=1,
        ),
    ),
)


PLAN = LmtBuildPlan(
    name="w07_00",
    design_ids=("wp_gun_cmn.stationary_draw",),
    source="original/lmt/w07_00.lmt",
    target="hm/wp/wp07/mot/w07_00/w07_00.lmt",
    expected_source_sha256=(
        "7897e766963b177b2dc157f65204e8a4ef9a35aba4b294c8d0f0635209800b94"
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
    expected_output_sha256=(
        "4c516b832d2b735ded1179b4de1462841e6eb79261d8328da9e25d3b77d80b16"
    ),
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
