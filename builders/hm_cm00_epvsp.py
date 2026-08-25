"""Build the gunlance-guard Protection overlay SoundBank."""

from __future__ import annotations

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli

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

SOUND_PARENT_OFFSET = 0x19
RANDOM_PARENT_OFFSET = 0x0B
RANDOM_OVER_LIMIT_BEHAVIOR_OFFSET = 0x19
RANDOM_MAX_INSTANCES_OFFSET = 0x1B

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

VOICE_SWITCH_IDS = (
    3_396_333_570,
    1_382_012_724,
    345_916_037,
    1_839_555_973,
    3_165_334_324,
    3_529_994_682,
    3_846_765_152,
    1_876_434_011,
    835_669_289,
    3_295_588_651,
    208_142_906,
)
EXCLUDED_SWITCH_IDS = (
    3_893_559_432,
    3_366_211_890,
    3_818_705_907,
    1_341_411_413,
)
VOICE_SWITCH_TOPOLOGY = soundbank_editor.SwitchContainerTopology(
    group_type=DONOR_SWITCH_TOPOLOGY.group_type,
    group_id=DONOR_SWITCH_TOPOLOGY.group_id,
    default_switch=DONOR_SWITCH_TOPOLOGY.default_switch,
    continuous_validation=DONOR_SWITCH_TOPOLOGY.continuous_validation,
    children=(VOICE_RANDOM_ID,),
    switch_packages=tuple(
        (switch_id, (VOICE_RANDOM_ID,)) for switch_id in VOICE_SWITCH_IDS
    ),
    node_params=(soundbank_editor.SwitchNodeParams(VOICE_RANDOM_ID, 0, 1, 0, 0),),
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


def _guard_voice_route_serialization(
    editor: soundbank_editor.HircEditor,
) -> None:
    positions = {item.object_id: item.index for item in editor.objects()}
    if not (
        max(positions[sound_id] for sound_id in VOICE_SOUND_IDS)
        < positions[VOICE_RANDOM_ID]
        < positions[VOICE_SWITCH_ID]
        < positions[VOICE_ACTION_ID]
        < positions[EVENT_ID]
    ):
        raise soundbank_editor.SoundBankError(
            "gunlance guard HIRC route is not serialized child-before-parent"
        )


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Add one guarded Switch-to-Random Protection overlay route."""

    _guard_original_route(bank)
    for media_id in VOICE_MEDIA_IDS:
        bank.media_entry(media_id=media_id)

    editor = bank.hirc
    for sound_id, media_id in zip(VOICE_SOUND_IDS, VOICE_MEDIA_IDS, strict=True):
        editor.clone_sound(
            DONOR_SOUND_ID,
            sound_id,
            media_id,
            expected_source_id=DONOR_MEDIA_ID,
            label=f"clone gunlance guard donor Sound as {sound_id}",
        )
        editor.patch_u32(
            soundbank_editor.HIRC_SOUND,
            sound_id,
            SOUND_PARENT_OFFSET,
            DONOR_RANDOM_ID,
            VOICE_RANDOM_ID,
            label=f"route Protection Sound {sound_id} to the voice Random",
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
    editor.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        VOICE_RANDOM_ID,
        RANDOM_PARENT_OFFSET,
        DONOR_SWITCH_ID,
        VOICE_SWITCH_ID,
        label="route Protection Random to the voice Switch",
    )
    editor.patch_u8(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        VOICE_RANDOM_ID,
        RANDOM_OVER_LIMIT_BEHAVIOR_OFFSET,
        0,
        1,
        label="set Protection Random over-limit behavior to Kill Newest",
    )
    editor.patch_u16(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        VOICE_RANDOM_ID,
        RANDOM_MAX_INSTANCES_OFFSET,
        0,
        1,
        label="limit Protection Random to one audio instance",
    )

    editor.clone_switch_container(
        DONOR_SWITCH_ID,
        VOICE_SWITCH_ID,
        {
            101_900_622: None,
            125_400_496: None,
            DONOR_RANDOM_ID: VOICE_RANDOM_ID,
            133_098_601: None,
            438_972_177: None,
        },
        expected_topology=DONOR_SWITCH_TOPOLOGY,
        expected_body_sha256=DONOR_SWITCH_BODY_SHA256,
        label="clone and isolate the gunlance guard Switch Container",
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
    added_media=((141, VOICE_MEDIA_IDS[0]), (142, VOICE_MEDIA_IDS[1])),
    hirc_changed_bytes=15,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_IDS[0]),
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_IDS[1]),
        (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, VOICE_RANDOM_ID),
        (soundbank_editor.HIRC_SWITCH_CONTAINER, VOICE_SWITCH_ID),
        (soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID),
    ),
    resized_hirc_objects=((soundbank_editor.HIRC_EVENT, EVENT_ID, 12, 16),),
    hirc_size_delta=512,
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
            "audio/hm_cm00_epvsp/"
            "raising_heart_protection_01(movie_1st.raising_heart.protection_01.1).wav",
        ),
        MediaAddition(
            142,
            VOICE_MEDIA_IDS[1],
            "audio/hm_cm00_epvsp/"
            "raising_heart_protection_02(movie_1st.raising_heart.protection_02.1).wav",
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)

if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
