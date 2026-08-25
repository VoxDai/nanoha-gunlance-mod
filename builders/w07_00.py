"""Build isolated stationary-draw and overhead-smash LMT requests."""

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

OVERHEAD_MOTION_ID = 138
OVERHEAD_REQUEST_KEYFRAME = 0.0
OVERHEAD_TRIGGER_FRAMES = (1.0,)
OVERHEAD_OLD_REQUEST = 6505
OVERHEAD_NEW_REQUEST = 6593
OVERHEAD_REQUEST_OFFSET = 0x113570


def apply_edits(editor: soundbank_editor.LmtEditor) -> None:
    """Guard and replace both isolated TIML slot-B request assignments."""

    editor.replace_request(
        motion_id=MOTION_ID,
        event_group=EVENT_GROUP,
        slot=SLOT,
        request_keyframe_frame=REQUEST_KEYFRAME,
        expected_request=OLD_REQUEST,
        replacement_request=NEW_REQUEST,
        expected_trigger_frames=TRIGGER_FRAMES,
    )
    editor.replace_request(
        motion_id=OVERHEAD_MOTION_ID,
        event_group=EVENT_GROUP,
        slot=SLOT,
        request_keyframe_frame=OVERHEAD_REQUEST_KEYFRAME,
        expected_request=OVERHEAD_OLD_REQUEST,
        replacement_request=OVERHEAD_NEW_REQUEST,
        expected_trigger_frames=OVERHEAD_TRIGGER_FRAMES,
    )


EXPECTED_SUMMARY = soundbank_editor.LmtEditSummary(
    changed_byte_count=2,
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
        soundbank_editor.LmtRequestEdit(
            motion_id=OVERHEAD_MOTION_ID,
            event_group=EVENT_GROUP,
            slot=SLOT,
            request_keyframe_frame=OVERHEAD_REQUEST_KEYFRAME,
            trigger_frames=OVERHEAD_TRIGGER_FRAMES,
            offset=OVERHEAD_REQUEST_OFFSET,
            old_request=OVERHEAD_OLD_REQUEST,
            new_request=OVERHEAD_NEW_REQUEST,
            changed_byte_count=1,
        ),
    ),
)


PLAN = LmtBuildPlan(
    name="w07_00",
    design_ids=(
        "wp_gun_cmn.stationary_draw",
        "wp_gun_cmn.overhead_smash",
    ),
    source="original/lmt/w07_00.lmt",
    target="hm/wp/wp07/mot/w07_00/w07_00.lmt",
    expected_source_sha256=(
        "7897e766963b177b2dc157f65204e8a4ef9a35aba4b294c8d0f0635209800b94"
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
    expected_output_sha256=(
        "e75b48eb9bb61e2595311b6a026d195f2178bc61729968bd2da3078fbce957d1"
    ),
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
