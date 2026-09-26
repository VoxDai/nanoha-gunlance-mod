"""Build reviewed gunlance Motion request replacements."""

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

OVERHEAD_EVENT_GROUP = "EventGroup02"
OVERHEAD_REQUEST_KEYFRAME = 0.0
OVERHEAD_OLD_REQUEST = 1409
OVERHEAD_NEW_REQUEST = 6595

QUICK_RELOAD_MOTION_ID = 128
QUICK_RELOAD_SLOT = "B"
QUICK_RELOAD_TRIGGER_FRAMES = (18.0,)
QUICK_RELOAD_REQUEST_OFFSET = 0xF03C0

LINK_MOTION_ID = 131
LINK_SLOT = "A"
LINK_TRIGGER_FRAMES = (14.0,)
LINK_REQUEST_OFFSET = 0xFC5A0

ORIGINAL_MECHANICAL_EVENT_GROUP = EVENT_GROUP
ORIGINAL_MECHANICAL_SLOT = "F"
ORIGINAL_MECHANICAL_REQUEST = 6505
ORIGINAL_MECHANICAL_TRIGGER_FRAMES = (32.0,)

WIDE_SWEEP_MOTION_ID = 143
WIDE_SWEEP_EVENT_GROUP = "EventGroup06"
WIDE_SWEEP_SLOT = "A"
WIDE_SWEEP_REQUEST_KEYFRAME = 0.0
WIDE_SWEEP_TRIGGER_FRAMES = (11.0,)
WIDE_SWEEP_OLD_REQUEST = 6486
WIDE_SWEEP_NEW_REQUEST = 6596
WIDE_SWEEP_REQUEST_OFFSET = 1_202_416

CHARGED_SHELLING_MOTION_IDS = (132, 133, 134)
CHARGED_SHELLING_EVENT_GROUP = "EventGroup06"
CHARGED_SHELLING_SLOT = "B"
CHARGED_SHELLING_REQUEST_KEYFRAME = 0.0
CHARGED_SHELLING_TRIGGER_FRAMES = (1.0,)
CHARGED_SHELLING_OLD_REQUEST = 6470
CHARGED_SHELLING_NEW_REQUEST = 6599
CHARGED_SHELLING_REQUEST_OFFSETS = (0xFEDF0, 0x101850, 0x104C70)
FIRING_VOICE_MOTIONS = (101, 102, 103)
FIRING_VOICE_REQUEST = 6608
FIRING_VOICE_OFFSETS = (606048, 627200, 648272)

WYR_STAKE_VOICE_MUTE_REQUEST = 6750
WYR_STAKE_VOICE_MUTE_EDITS = (
    (144, "A", 1129, 27.0, 1_222_880),
    (145, "B", 1105, 80.0, 1_261_120),
    (145, "C", 1019, 183.0, 1_261_152),
    (178, "A", 1309, 19.0, 2_055_696),
    (179, "B", 1119, 2.0, 2_093_728),
    (179, "A", 1109, 68.0, 2_093_696),
    (179, "C", 1009, 176.0, 2_093_760),
    (181, "A", 1309, 34.0, 2_135_488),
    (182, "B", 1119, 4.0, 2_174_160),
    (182, "A", 1109, 65.0, 2_174_128),
    (182, "C", 1009, 184.0, 2_174_192),
    (310, "A", 1309, 53.0, 2_691_040),
)


WYR_STAKE_EDITS = (
    (144, "EventGroup06", "G", 6456, 6610, (2.0,), 1_223_392),
    (178, "EventGroup07", "A", 6570, 6611, (1.0,), 2_056_144),
    (181, "EventGroup07", "A", 6570, 6611, (1.0,), 2_135_936),
    (310, "EventGroup07", "A", 6570, 6611, (3.0,), 2_691_488),
    (145, "EventGroup06", "H", 6525, 6612, (1.0,), 1_261_552),
    (179, "EventGroup06", "G", 6525, 6612, (1.0,), 2_094_144),
    (182, "EventGroup06", "G", 6525, 6612, (1.0,), 2_174_576),
)


def apply_edits(editor: soundbank_editor.LmtEditor) -> None:
    """Guard and replace the reviewed animation and voice request assignments."""

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
        motion_id=QUICK_RELOAD_MOTION_ID,
        event_group=OVERHEAD_EVENT_GROUP,
        slot=QUICK_RELOAD_SLOT,
        request_keyframe_frame=OVERHEAD_REQUEST_KEYFRAME,
        expected_request=OVERHEAD_OLD_REQUEST,
        replacement_request=OVERHEAD_NEW_REQUEST,
        expected_trigger_frames=QUICK_RELOAD_TRIGGER_FRAMES,
    )
    editor.replace_request(
        motion_id=LINK_MOTION_ID,
        event_group=OVERHEAD_EVENT_GROUP,
        slot=LINK_SLOT,
        request_keyframe_frame=OVERHEAD_REQUEST_KEYFRAME,
        expected_request=OVERHEAD_OLD_REQUEST,
        replacement_request=OVERHEAD_NEW_REQUEST,
        expected_trigger_frames=LINK_TRIGGER_FRAMES,
    )
    editor.replace_request(
        motion_id=WIDE_SWEEP_MOTION_ID,
        event_group=WIDE_SWEEP_EVENT_GROUP,
        slot=WIDE_SWEEP_SLOT,
        request_keyframe_frame=WIDE_SWEEP_REQUEST_KEYFRAME,
        expected_request=WIDE_SWEEP_OLD_REQUEST,
        replacement_request=WIDE_SWEEP_NEW_REQUEST,
        expected_trigger_frames=WIDE_SWEEP_TRIGGER_FRAMES,
    )
    for motion_id in CHARGED_SHELLING_MOTION_IDS:
        editor.replace_request(
            motion_id=motion_id,
            event_group=CHARGED_SHELLING_EVENT_GROUP,
            slot=CHARGED_SHELLING_SLOT,
            request_keyframe_frame=CHARGED_SHELLING_REQUEST_KEYFRAME,
            expected_request=CHARGED_SHELLING_OLD_REQUEST,
            replacement_request=CHARGED_SHELLING_NEW_REQUEST,
            expected_trigger_frames=CHARGED_SHELLING_TRIGGER_FRAMES,
        )
    for motion_id in FIRING_VOICE_MOTIONS:
        editor.replace_request(
            motion_id=motion_id, event_group="EventGroup02", slot="A",
            request_keyframe_frame=0.0, expected_request=1305,
            replacement_request=FIRING_VOICE_REQUEST, expected_trigger_frames=(5.0,),
        )
    for motion, group, slot, old_request, new_request, frames, _ in WYR_STAKE_EDITS:
        editor.replace_request(
            motion_id=motion, event_group=group, slot=slot,
            request_keyframe_frame=0.0, expected_request=old_request,
            replacement_request=new_request, expected_trigger_frames=frames,
        )
    for motion, slot, old_request, frame, _ in WYR_STAKE_VOICE_MUTE_EDITS:
        editor.replace_request(
            motion_id=motion, event_group="EventGroup02", slot=slot,
            request_keyframe_frame=0.0, expected_request=old_request,
            replacement_request=WYR_STAKE_VOICE_MUTE_REQUEST,
            expected_trigger_frames=(frame,),
        )


EXPECTED_SUMMARY = soundbank_editor.LmtEditSummary(
    changed_byte_count=46,
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
            motion_id=QUICK_RELOAD_MOTION_ID,
            event_group=OVERHEAD_EVENT_GROUP,
            slot=QUICK_RELOAD_SLOT,
            request_keyframe_frame=OVERHEAD_REQUEST_KEYFRAME,
            trigger_frames=QUICK_RELOAD_TRIGGER_FRAMES,
            offset=QUICK_RELOAD_REQUEST_OFFSET,
            old_request=OVERHEAD_OLD_REQUEST,
            new_request=OVERHEAD_NEW_REQUEST,
            changed_byte_count=2,
        ),
        soundbank_editor.LmtRequestEdit(
            motion_id=LINK_MOTION_ID,
            event_group=OVERHEAD_EVENT_GROUP,
            slot=LINK_SLOT,
            request_keyframe_frame=OVERHEAD_REQUEST_KEYFRAME,
            trigger_frames=LINK_TRIGGER_FRAMES,
            offset=LINK_REQUEST_OFFSET,
            old_request=OVERHEAD_OLD_REQUEST,
            new_request=OVERHEAD_NEW_REQUEST,
            changed_byte_count=2,
        ),
        soundbank_editor.LmtRequestEdit(
            motion_id=WIDE_SWEEP_MOTION_ID,
            event_group=WIDE_SWEEP_EVENT_GROUP,
            slot=WIDE_SWEEP_SLOT,
            request_keyframe_frame=WIDE_SWEEP_REQUEST_KEYFRAME,
            trigger_frames=WIDE_SWEEP_TRIGGER_FRAMES,
            offset=WIDE_SWEEP_REQUEST_OFFSET,
            old_request=WIDE_SWEEP_OLD_REQUEST,
            new_request=WIDE_SWEEP_NEW_REQUEST,
            changed_byte_count=1,
        ),
        soundbank_editor.LmtRequestEdit(
            motion_id=CHARGED_SHELLING_MOTION_IDS[0],
            event_group=CHARGED_SHELLING_EVENT_GROUP,
            slot=CHARGED_SHELLING_SLOT,
            request_keyframe_frame=CHARGED_SHELLING_REQUEST_KEYFRAME,
            trigger_frames=CHARGED_SHELLING_TRIGGER_FRAMES,
            offset=CHARGED_SHELLING_REQUEST_OFFSETS[0],
            old_request=CHARGED_SHELLING_OLD_REQUEST,
            new_request=CHARGED_SHELLING_NEW_REQUEST,
            changed_byte_count=1,
        ),
        soundbank_editor.LmtRequestEdit(
            motion_id=CHARGED_SHELLING_MOTION_IDS[1],
            event_group=CHARGED_SHELLING_EVENT_GROUP,
            slot=CHARGED_SHELLING_SLOT,
            request_keyframe_frame=CHARGED_SHELLING_REQUEST_KEYFRAME,
            trigger_frames=CHARGED_SHELLING_TRIGGER_FRAMES,
            offset=CHARGED_SHELLING_REQUEST_OFFSETS[1],
            old_request=CHARGED_SHELLING_OLD_REQUEST,
            new_request=CHARGED_SHELLING_NEW_REQUEST,
            changed_byte_count=1,
        ),
        soundbank_editor.LmtRequestEdit(
            motion_id=CHARGED_SHELLING_MOTION_IDS[2],
            event_group=CHARGED_SHELLING_EVENT_GROUP,
            slot=CHARGED_SHELLING_SLOT,
            request_keyframe_frame=CHARGED_SHELLING_REQUEST_KEYFRAME,
            trigger_frames=CHARGED_SHELLING_TRIGGER_FRAMES,
            offset=CHARGED_SHELLING_REQUEST_OFFSETS[2],
            old_request=CHARGED_SHELLING_OLD_REQUEST,
            new_request=CHARGED_SHELLING_NEW_REQUEST,
            changed_byte_count=1,
        ),
    ) + tuple(
        soundbank_editor.LmtRequestEdit(
            motion_id=motion, event_group="EventGroup02", slot="A",
            request_keyframe_frame=0.0, trigger_frames=(5.0,), offset=offset,
            old_request=1305, new_request=FIRING_VOICE_REQUEST, changed_byte_count=2,
        )
        for motion, offset in zip(FIRING_VOICE_MOTIONS, FIRING_VOICE_OFFSETS, strict=True)
    ) + tuple(
        soundbank_editor.LmtRequestEdit(
            motion_id=motion, event_group=group, slot=slot,
            request_keyframe_frame=0.0, trigger_frames=frames,
            offset=offset, old_request=old_request, new_request=new_request,
            changed_byte_count=1,
        )
        for motion, group, slot, old_request, new_request, frames, offset in WYR_STAKE_EDITS
    ) + tuple(
        soundbank_editor.LmtRequestEdit(
            motion_id=motion, event_group="EventGroup02", slot=slot,
            request_keyframe_frame=0.0, trigger_frames=(frame,),
            offset=offset, old_request=old_request,
            new_request=WYR_STAKE_VOICE_MUTE_REQUEST, changed_byte_count=2,
        )
        for motion, slot, old_request, frame, offset in WYR_STAKE_VOICE_MUTE_EDITS
    ),
)


PLAN = LmtBuildPlan(
    name="w07_00",
    design_ids=(
        "wp_gun_cmn.stationary_draw",
        "wp_gun_cmn.overhead_smash",
        "wp_gun_cmn.wide_sweep",
        "wp07_gun_epvsp_shell.charged_shelling",
        "wp07_gun_epvsp_shell.wyrmstake_cannon",
    ),
    source="original/lmt/w07_00.lmt",
    target="hm/wp/wp07/mot/w07_00/w07_00.lmt",
    expected_source_sha256=(
        "7897e766963b177b2dc157f65204e8a4ef9a35aba4b294c8d0f0635209800b94"
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
