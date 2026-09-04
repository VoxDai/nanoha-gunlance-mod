"""Build the gunlance-guard Protection overlay SoundBank."""

from __future__ import annotations

import hashlib

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli
from .voice_standard import (
    STANDARD_VOICE_PARENT_ID,
    STANDARD_VOICE_REFERENCE_INPUTS,
    insert_standard_voice_sound,
)

EVENT_ID = 4_072_881_687
ORIGINAL_ACTION_ID = 601_196_071
DONOR_SWITCH_ID = 368_774_789
DONOR_RANDOM_ID = 127_521_149
DONOR_SOUND_ID = 925_721_864
DONOR_MEDIA_ID = 676_385_730

VOICE_ACTION_ID = 4_197_300_369
VOICE_SWITCH_ID = 4_010_844_647
VOICE_RANDOM_ID = 3_163_089_818
VOICE_SOUND_IDS = (2_154_199_438, 640_829_561)
VOICE_MEDIA_IDS = (141_209_263, 440_767_416)
SILENCE_SOUND_ID = 3_060_148_569
SILENCE_MEDIA_ID = 2_901_559_960
GUNLANCE_SWITCH_ID = 3_529_994_682

RANDOM_PARENT_OFFSET = 0x0B
RANDOM_OVER_LIMIT_BEHAVIOR_OFFSET = 0x19
RANDOM_MAX_INSTANCES_OFFSET = 0x1B
SWITCH_PARENT_OFFSET = 0x0B
ORIGINAL_SWITCH_PARENT_ID = 422_956_649

DONOR_RANDOM_BODY_SHA256 = (
    "dd0dfececc9d361c76f00553fe4179e4558f9adf909199c64c0fd28e9997237f"
)
VOICE_RANDOM_BODY_SHA256 = (
    "396592e4835d0108b6049e3f40c2d1e6fb66c628c52fb59da3506f49c0c4756f"
)
VOICE_RANDOM_PITCH = soundbank_editor.HircPitchSettings(None, (-50, 50))

DONOR_SWITCH_BODY_SHA256 = (
    "a6df54f2d29b79482420ff8a17420b0952cbb64589e03dde1358c02ab99043bb"
)
DONOR_SWITCH_TOPOLOGY = soundbank_editor.SwitchContainerTopology(
    group_type=0,
    group_id=3_251_135_135,
    default_switch=3_396_333_570,
    continuous_validation=0,
    children=(
        101_900_622,
        125_400_496,
        DONOR_RANDOM_ID,
        133_098_601,
        438_972_177,
    ),
    switch_packages=(
        (3_396_333_570, (DONOR_RANDOM_ID,)),
        (1_341_411_413, (438_972_177,)),
        (3_366_211_890, (125_400_496,)),
        (1_382_012_724, (DONOR_RANDOM_ID,)),
        (345_916_037, (DONOR_RANDOM_ID,)),
        (1_839_555_973, (DONOR_RANDOM_ID,)),
        (3_165_334_324, (DONOR_RANDOM_ID,)),
        (3_893_559_432, (133_098_601,)),
        (3_529_994_682, (DONOR_RANDOM_ID,)),
        (3_846_765_152, (DONOR_RANDOM_ID,)),
        (3_818_705_907, (101_900_622,)),
        (1_876_434_011, (DONOR_RANDOM_ID,)),
        (835_669_289, (DONOR_RANDOM_ID,)),
        (3_295_588_651, (DONOR_RANDOM_ID,)),
        (208_142_906, (DONOR_RANDOM_ID,)),
    ),
    node_params=(
        soundbank_editor.SwitchNodeParams(125_400_496, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(438_972_177, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(133_098_601, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(101_900_622, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(DONOR_RANDOM_ID, 0, 1, 0, 0),
    ),
)

VOICE_SWITCH_TOPOLOGY = soundbank_editor.SwitchContainerTopology(
    group_type=DONOR_SWITCH_TOPOLOGY.group_type,
    group_id=DONOR_SWITCH_TOPOLOGY.group_id,
    default_switch=DONOR_SWITCH_TOPOLOGY.default_switch,
    continuous_validation=DONOR_SWITCH_TOPOLOGY.continuous_validation,
    children=(SILENCE_SOUND_ID, VOICE_RANDOM_ID),
    switch_packages=(
        (DONOR_SWITCH_TOPOLOGY.default_switch, (SILENCE_SOUND_ID,)),
        (GUNLANCE_SWITCH_ID, (VOICE_RANDOM_ID,)),
    ),
    node_params=(
        soundbank_editor.SwitchNodeParams(SILENCE_SOUND_ID, 0, 1, 0, 0),
        soundbank_editor.SwitchNodeParams(VOICE_RANDOM_ID, 0, 1, 0, 0),
    ),
)


def _guard_original_route(
        bank: soundbank_editor.SoundBankEditor,
) -> None:
    editor = bank.hirc
    if bank.media_entry(index=88).media_id != DONOR_MEDIA_ID:
        raise soundbank_editor.SoundBankError(
            "gunlance guard DIDX #88 no longer has the designed Media ID"
        )
    expected_action = editor.create_play_action(
        ORIGINAL_ACTION_ID,
        DONOR_SWITCH_ID,
        bank.bank_id,
        delay_ms=30,
    )
    if (
            editor.object_body(soundbank_editor.HIRC_ACTION, ORIGINAL_ACTION_ID)
            != expected_action
    ):
        raise soundbank_editor.SoundBankError(
            "original gunlance guard Action differs from its design guard"
        )
    if editor.event_actions(EVENT_ID) != (ORIGINAL_ACTION_ID,):
        raise soundbank_editor.SoundBankError(
            "original gunlance guard Event route differs from its design guard"
        )
    donor_random = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, DONOR_RANDOM_ID
    )
    if hashlib.sha256(donor_random).hexdigest() != DONOR_RANDOM_BODY_SHA256:
        raise soundbank_editor.SoundBankError(
            "original gunlance guard Random body differs from its design guard"
        )


def _configure_voice_random(editor: soundbank_editor.HircEditor) -> None:
    """Compose the instance limit and random Pitch as one guarded replacement."""

    kind = soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER
    cloned_body = editor.object_body(kind, VOICE_RANDOM_ID)
    if len(cloned_body) != 91:
        raise soundbank_editor.SoundBankError(
            "Protection Random clone must have a 91-byte body before Pitch insertion"
        )
    staged = soundbank_editor.HircEditor(editor.build(), version=editor.version)
    staged.patch_u32(
        kind,
        VOICE_RANDOM_ID,
        RANDOM_PARENT_OFFSET,
        DONOR_SWITCH_ID,
        VOICE_SWITCH_ID,
        label="route Protection Random to the voice Switch",
    )
    staged.patch_u8(
        kind,
        VOICE_RANDOM_ID,
        RANDOM_OVER_LIMIT_BEHAVIOR_OFFSET,
        0,
        1,
        label="set Protection Random over-limit behavior to Kill Newest",
    )
    staged.patch_u16(
        kind,
        VOICE_RANDOM_ID,
        RANDOM_MAX_INSTANCES_OFFSET,
        0,
        1,
        label="limit Protection Random to one audio instance",
    )

    # Pitch insertion resizes the body, so reparse after the guarded field patches.
    staged = soundbank_editor.HircEditor(staged.build(), version=editor.version)
    staged.set_pitch(
        kind,
        VOICE_RANDOM_ID,
        expected=soundbank_editor.HircPitchSettings(None, None),
        random_range_cents=VOICE_RANDOM_PITCH.random_range_cents,
        label="set Protection Random Pitch to plus/minus 50 cents",
    )
    final_body = staged.object_body(kind, VOICE_RANDOM_ID)
    if (
        len(final_body) != 100
        or hashlib.sha256(final_body).hexdigest() != VOICE_RANDOM_BODY_SHA256
    ):
        raise soundbank_editor.SoundBankError(
            "Protection Random final body differs from its design guard"
        )
    editor.replace_object_body(
        kind,
        VOICE_RANDOM_ID,
        cloned_body,
        final_body,
        label="apply composed Protection Random body",
    )
    if editor.pitch_settings(kind, VOICE_RANDOM_ID) != VOICE_RANDOM_PITCH:
        raise soundbank_editor.SoundBankError(
            "Protection Random Pitch read-back differs from its design guard"
        )


def _guard_voice_route_serialization(
    editor: soundbank_editor.HircEditor,
) -> None:
    positions = {item.object_id: item.index for item in editor.objects()}
    if not (
        max(positions[sound_id] for sound_id in VOICE_SOUND_IDS)
        < positions[VOICE_RANDOM_ID]
        and positions[SILENCE_SOUND_ID] < positions[VOICE_SWITCH_ID]
        and positions[VOICE_RANDOM_ID]
        < positions[VOICE_SWITCH_ID]
        < positions[VOICE_ACTION_ID]
        < positions[EVENT_ID]
    ):
        raise soundbank_editor.SoundBankError(
            "gunlance guard HIRC route is not serialized child-before-parent"
        )


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Add the accepted gunlance-only Protection overlay route."""

    _guard_original_route(bank)
    for media_id in (*VOICE_MEDIA_IDS, SILENCE_MEDIA_ID):
        bank.media_entry(media_id=media_id)

    editor = bank.hirc
    for sound_id, media_id in zip(VOICE_SOUND_IDS, VOICE_MEDIA_IDS, strict=True):
        insert_standard_voice_sound(
            editor,
            sound_id,
            media_id,
            direct_parent_id=VOICE_RANDOM_ID,
            label=f"insert Protection standard Sound {sound_id}",
        )
    insert_standard_voice_sound(
        editor,
        SILENCE_SOUND_ID,
        SILENCE_MEDIA_ID,
        direct_parent_id=VOICE_SWITCH_ID,
        label="insert Protection silent default Sound",
    )

    editor.clone_random_sequence_container(
        DONOR_RANDOM_ID,
        VOICE_RANDOM_ID,
        tuple((sound_id, 50_000) for sound_id in VOICE_SOUND_IDS),
        expected_playlist=((DONOR_SOUND_ID, 50_000),),
        expected_avoid_repeat_count=1,
        avoid_repeat_count=0,
        label="clone gunlance guard Random Container",
    )
    _configure_voice_random(editor)

    editor.clone_switch_container_with_topology(
        DONOR_SWITCH_ID,
        VOICE_SWITCH_ID,
        VOICE_SWITCH_TOPOLOGY,
        expected_topology=DONOR_SWITCH_TOPOLOGY,
        expected_body_sha256=DONOR_SWITCH_BODY_SHA256,
        label="clone gunlance-only Protection Switch",
    )
    editor.patch_u32(
        soundbank_editor.HIRC_SWITCH_CONTAINER,
        VOICE_SWITCH_ID,
        SWITCH_PARENT_OFFSET,
        ORIGINAL_SWITCH_PARENT_ID,
        STANDARD_VOICE_PARENT_ID,
        label="route Protection Switch to Actor-Mixer 209038110",
    )

    action = editor.create_play_action(
        VOICE_ACTION_ID,
        VOICE_SWITCH_ID,
        bank.bank_id,
        delay_ms=30,
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        VOICE_ACTION_ID,
        action[4:],
        before=(soundbank_editor.HIRC_EVENT, EVENT_ID),
        label="add gunlance guard Protection Play Action",
    )
    editor.append_event_action(
        EVENT_ID,
        VOICE_ACTION_ID,
        expected_actions=(ORIGINAL_ACTION_ID,),
        label="append Protection overlay to the gunlance guard Event",
    )
    _guard_voice_route_serialization(editor)


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=(
        (141, VOICE_MEDIA_IDS[0]),
        (142, VOICE_MEDIA_IDS[1]),
        (143, SILENCE_MEDIA_ID),
    ),
    hirc_changed_bytes=51,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_IDS[0]),
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_IDS[1]),
        (soundbank_editor.HIRC_SOUND, SILENCE_SOUND_ID),
        (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, VOICE_RANDOM_ID),
        (soundbank_editor.HIRC_SWITCH_CONTAINER, VOICE_SWITCH_ID),
        (soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID),
    ),
    resized_hirc_objects=((soundbank_editor.HIRC_EVENT, EVENT_ID, 12, 16),),
    hirc_size_delta=430,
)

PLAN = SoundBankBuildPlan(
    name="hm_cm00_epvsp",
    design_ids=("hm_cm00_epvsp.gunlance_guard",),
    source="original/nbnk/hm_cm00_epvsp.nbnk",
    target="sound/wwise/Windows/hm_cm00_epvsp.nbnk",
    expected_source_sha256=(
        "73b52c1a69532f0a84ab6dfa2e95bd804bf8affc5af77450786d700c177a9977"
    ),
    expected_bank_id=707_566_772,
    media_additions=(
        MediaAddition(
            141,
            VOICE_MEDIA_IDS[0],
            "audio/hm_cm00_epvsp/gunlance_guard/"
            "raising_heart_protection_01(movie_1st.raising_heart.protection_01.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            142,
            VOICE_MEDIA_IDS[1],
            "audio/hm_cm00_epvsp/gunlance_guard/"
            "raising_heart_protection_02(movie_1st.raising_heart.protection_02.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            143,
            SILENCE_MEDIA_ID,
            "audio/silence_10ms.wav",
            wem_channels=1,
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
    reference_inputs=STANDARD_VOICE_REFERENCE_INPUTS,
)

if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
