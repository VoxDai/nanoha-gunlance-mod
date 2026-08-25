"""Build stationary-draw, overhead-smash, and reload voice routes."""

from __future__ import annotations

import struct

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli


VOICE_MEDIA_ID = 863_865_614
VOICE_SOUND_ID = 700_212_875
ORIGINAL_ROUTE_ACTION_ID = 267_255_962
VOICE_ACTION_ID = 708_529_406
VOICE_EVENT_ID = 3_176_129_810

ORIGINAL_EVENT_ID = 3_567_942_167
ORIGINAL_EVENT_ACTION_ID = 1_061_269_777
DONOR_SOUND_ID = 233_981_936
DONOR_MEDIA_ID = 867_938_822
POSITIONING_VECTOR_OFFSET = 0x2A

OVERHEAD_VOICE_MEDIA_ID = 1_280_643_898
OVERHEAD_VOICE_SOUND_ID = 1_643_477_631
OVERHEAD_ORIGINAL_ROUTE_ACTION_ID = 2_557_911_997
OVERHEAD_VOICE_ACTION_ID = 3_750_542_142
OVERHEAD_VOICE_EVENT_ID = 2_866_569_635

OVERHEAD_ORIGINAL_EVENT_ID = 1_129_041_389
OVERHEAD_ORIGINAL_EVENT_ACTION_ID = 948_030_399
OVERHEAD_ORIGINAL_CONTAINER_ID = 968_655_714
OVERHEAD_DONOR_SOUND_ID = 959_908_164
OVERHEAD_DONOR_MEDIA_ID = 554_875_117
OVERHEAD_DONOR_MEDIA_INDEX = 13
OVERHEAD_SOUND_PARENT_OFFSET = 0x19
OVERHEAD_SOUND_OVERRIDE_BUS_OFFSET = 0x15
OVERHEAD_SOUND_AUX_OFFSET = 0x2C
OVERHEAD_SOUND_AUX_IDS = (3_015_692_424, 0, 0, 0)

RELOAD_VOICE_MEDIA_ID = 1_284_288_484
RELOAD_VOICE_SOUND_ID = 1_474_128_429
RELOAD_VOICE_ACTION_ID = 3_418_611_510

RELOAD_EVENT_ID = 3_476_627_122
RELOAD_ORIGINAL_ACTION_ID = 126_049_847
RELOAD_CONTAINER_ID = 411_055_943
RELOAD_DONOR_SOUND_ID = 176_748_589
RELOAD_DONOR_MEDIA_ID = 86_782_159
RELOAD_DONOR_MEDIA_INDEX = 1
RELOAD_SOUND_PARENT_OFFSET = 0x19
RELOAD_SOUND_OVERRIDE_BUS_OFFSET = 0x15
RELOAD_SOUND_AUX_OFFSET = 0x2C
RELOAD_SOUND_AUX_IDS = (3_015_692_424, 0, 0, 0)
RELOAD_CONTAINER_AVOID_REPEAT_OFFSET = 0x40
RELOAD_CONTAINER_MODE_OFFSET = 0x44
RELOAD_CONTAINER_PLAYLIST_OFFSET = 0x46
RELOAD_CONTAINER_PLAYLIST = struct.pack(
    "<IIHII",
    1,
    RELOAD_DONOR_SOUND_ID,
    1,
    RELOAD_DONOR_SOUND_ID,
    50_000,
)


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Create isolated action routes and append the shared reload Event Action."""

    bank.media_entry(media_id=VOICE_MEDIA_ID)
    editor = bank.hirc
    if editor.event_actions(ORIGINAL_EVENT_ID) != (ORIGINAL_EVENT_ACTION_ID,):
        raise soundbank_editor.SoundBankError(
            "original stationary-draw Event route differs from its design guard"
        )

    editor.clone_sound(
        DONOR_SOUND_ID,
        VOICE_SOUND_ID,
        VOICE_MEDIA_ID,
        expected_source_id=DONOR_MEDIA_ID,
        label="clone frame-9 draw Sound topology for stationary-draw voice",
    )
    editor.patch_u8(
        soundbank_editor.HIRC_SOUND,
        VOICE_SOUND_ID,
        POSITIONING_VECTOR_OFFSET,
        0xC0,
        0xC1,
        label="enable local 2D positioning for stationary-draw voice",
    )

    original_route = editor.create_play_event_action(
        ORIGINAL_ROUTE_ACTION_ID, ORIGINAL_EVENT_ID
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        ORIGINAL_ROUTE_ACTION_ID,
        original_route[4:],
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add stationary-draw PlayEvent Action for the original route",
    )
    voice = editor.create_play_action(VOICE_ACTION_ID, VOICE_SOUND_ID, bank.bank_id)
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        VOICE_ACTION_ID,
        voice[4:],
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add stationary-draw voice Play Action",
    )
    editor.insert_object(
        soundbank_editor.HIRC_EVENT,
        VOICE_EVENT_ID,
        struct.pack("<III", 2, ORIGINAL_ROUTE_ACTION_ID, VOICE_ACTION_ID),
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add isolated stationary-draw Event",
    )

    bank.media_entry(media_id=OVERHEAD_VOICE_MEDIA_ID)
    if bank.media_entry(index=OVERHEAD_DONOR_MEDIA_INDEX).media_id != OVERHEAD_DONOR_MEDIA_ID:
        raise soundbank_editor.SoundBankError(
            "overhead-smash donor DIDX identity differs from its design guard"
        )
    if editor.event_actions(OVERHEAD_ORIGINAL_EVENT_ID) != (
        OVERHEAD_ORIGINAL_EVENT_ACTION_ID,
    ):
        raise soundbank_editor.SoundBankError(
            "original overhead-smash Event route differs from its design guard"
        )
    original_action = editor.object_body(
        soundbank_editor.HIRC_ACTION, OVERHEAD_ORIGINAL_EVENT_ACTION_ID
    )
    if (
        struct.unpack_from("<H", original_action, 4)[0]
        != soundbank_editor.ACTION_PLAY
        or struct.unpack_from("<I", original_action, 6)[0]
        != OVERHEAD_ORIGINAL_CONTAINER_ID
    ):
        raise soundbank_editor.SoundBankError(
            "original overhead-smash Action no longer targets its Container"
        )
    donor_sound = editor.object_body(
        soundbank_editor.HIRC_SOUND, OVERHEAD_DONOR_SOUND_ID
    )
    if (
        len(donor_sound) != 72
        or struct.unpack_from("<I", donor_sound, 9)[0] != OVERHEAD_DONOR_MEDIA_ID
        or struct.unpack_from("<I", donor_sound, OVERHEAD_SOUND_OVERRIDE_BUS_OFFSET)[0]
        != 0
        or struct.unpack_from("<I", donor_sound, OVERHEAD_SOUND_PARENT_OFFSET)[0]
        != OVERHEAD_ORIGINAL_CONTAINER_ID
        or donor_sound[POSITIONING_VECTOR_OFFSET] != 0xC0
        or struct.unpack_from("<4I", donor_sound, OVERHEAD_SOUND_AUX_OFFSET)
        != OVERHEAD_SOUND_AUX_IDS
    ):
        raise soundbank_editor.SoundBankError(
            "overhead-smash donor Sound topology differs from its design guard"
        )

    editor.clone_sound(
        OVERHEAD_DONOR_SOUND_ID,
        OVERHEAD_VOICE_SOUND_ID,
        OVERHEAD_VOICE_MEDIA_ID,
        expected_source_id=OVERHEAD_DONOR_MEDIA_ID,
        label="clone overhead-smash donor Sound for Accel voice",
    )
    editor.patch_u8(
        soundbank_editor.HIRC_SOUND,
        OVERHEAD_VOICE_SOUND_ID,
        POSITIONING_VECTOR_OFFSET,
        0xC0,
        0xC1,
        label="enable local 2D positioning for overhead-smash Accel voice",
    )

    overhead_original_route = editor.create_play_event_action(
        OVERHEAD_ORIGINAL_ROUTE_ACTION_ID, OVERHEAD_ORIGINAL_EVENT_ID
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        OVERHEAD_ORIGINAL_ROUTE_ACTION_ID,
        overhead_original_route[4:],
        before=(soundbank_editor.HIRC_EVENT, OVERHEAD_ORIGINAL_EVENT_ID),
        label="add overhead-smash PlayEvent Action for the original route",
    )
    overhead_voice = editor.create_play_action(
        OVERHEAD_VOICE_ACTION_ID, OVERHEAD_VOICE_SOUND_ID, bank.bank_id
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        OVERHEAD_VOICE_ACTION_ID,
        overhead_voice[4:],
        before=(soundbank_editor.HIRC_EVENT, OVERHEAD_ORIGINAL_EVENT_ID),
        label="add overhead-smash Accel Play Action",
    )
    editor.insert_object(
        soundbank_editor.HIRC_EVENT,
        OVERHEAD_VOICE_EVENT_ID,
        struct.pack(
            "<III",
            2,
            OVERHEAD_ORIGINAL_ROUTE_ACTION_ID,
            OVERHEAD_VOICE_ACTION_ID,
        ),
        before=(soundbank_editor.HIRC_EVENT, OVERHEAD_ORIGINAL_EVENT_ID),
        label="add isolated overhead-smash Event",
    )

    bank.media_entry(media_id=RELOAD_VOICE_MEDIA_ID)
    if bank.media_entry(index=RELOAD_DONOR_MEDIA_INDEX).media_id != RELOAD_DONOR_MEDIA_ID:
        raise soundbank_editor.SoundBankError(
            "reload donor DIDX identity differs from its design guard"
        )
    if editor.event_actions(RELOAD_EVENT_ID) != (RELOAD_ORIGINAL_ACTION_ID,):
        raise soundbank_editor.SoundBankError(
            "original reload Event route differs from its design guard"
        )
    reload_action = editor.object_body(
        soundbank_editor.HIRC_ACTION, RELOAD_ORIGINAL_ACTION_ID
    )
    if (
        struct.unpack_from("<H", reload_action, 4)[0]
        != soundbank_editor.ACTION_PLAY
        or struct.unpack_from("<I", reload_action, 6)[0] != RELOAD_CONTAINER_ID
    ):
        raise soundbank_editor.SoundBankError(
            "original reload Action no longer targets its Container"
        )
    reload_donor = editor.object_body(
        soundbank_editor.HIRC_SOUND, RELOAD_DONOR_SOUND_ID
    )
    if (
        len(reload_donor) != 72
        or reload_donor[8] != 0
        or struct.unpack_from("<I", reload_donor, 9)[0] != RELOAD_DONOR_MEDIA_ID
        or struct.unpack_from(
            "<I", reload_donor, RELOAD_SOUND_OVERRIDE_BUS_OFFSET
        )[0]
        != 0
        or struct.unpack_from("<I", reload_donor, RELOAD_SOUND_PARENT_OFFSET)[0]
        != RELOAD_CONTAINER_ID
        or reload_donor[POSITIONING_VECTOR_OFFSET] != 0xC0
        or struct.unpack_from("<4I", reload_donor, RELOAD_SOUND_AUX_OFFSET)
        != RELOAD_SOUND_AUX_IDS
    ):
        raise soundbank_editor.SoundBankError(
            "reload donor Sound topology differs from its design guard"
        )
    reload_container = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, RELOAD_CONTAINER_ID
    )
    if (
        len(reload_container) != 88
        or struct.unpack_from(
            "<H", reload_container, RELOAD_CONTAINER_AVOID_REPEAT_OFFSET
        )[0]
        != 1
        or reload_container[RELOAD_CONTAINER_MODE_OFFSET] != 0
        or reload_container[RELOAD_CONTAINER_PLAYLIST_OFFSET:]
        != RELOAD_CONTAINER_PLAYLIST
    ):
        raise soundbank_editor.SoundBankError(
            "reload Container playlist differs from its design guard"
        )

    editor.clone_sound(
        RELOAD_DONOR_SOUND_ID,
        RELOAD_VOICE_SOUND_ID,
        RELOAD_VOICE_MEDIA_ID,
        expected_source_id=RELOAD_DONOR_MEDIA_ID,
        label="clone reload donor Sound for Raising Heart voice",
    )
    reload_voice = editor.create_play_action(
        RELOAD_VOICE_ACTION_ID,
        RELOAD_VOICE_SOUND_ID,
        bank.bank_id,
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        RELOAD_VOICE_ACTION_ID,
        reload_voice[4:],
        before=(soundbank_editor.HIRC_EVENT, RELOAD_EVENT_ID),
        label="add Raising Heart reload Play Action",
    )
    editor.append_event_action(
        RELOAD_EVENT_ID,
        RELOAD_VOICE_ACTION_ID,
        expected_actions=(RELOAD_ORIGINAL_ACTION_ID,),
        label="append Raising Heart voice to reload Event",
    )


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=(
        (34, VOICE_MEDIA_ID),
        (35, OVERHEAD_VOICE_MEDIA_ID),
        (36, RELOAD_VOICE_MEDIA_ID),
    ),
    hirc_changed_bytes=3,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_ID),
        (soundbank_editor.HIRC_ACTION, ORIGINAL_ROUTE_ACTION_ID),
        (soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, VOICE_EVENT_ID),
        (soundbank_editor.HIRC_SOUND, OVERHEAD_VOICE_SOUND_ID),
        (soundbank_editor.HIRC_ACTION, OVERHEAD_ORIGINAL_ROUTE_ACTION_ID),
        (soundbank_editor.HIRC_ACTION, OVERHEAD_VOICE_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, OVERHEAD_VOICE_EVENT_ID),
        (soundbank_editor.HIRC_SOUND, RELOAD_VOICE_SOUND_ID),
        (soundbank_editor.HIRC_ACTION, RELOAD_VOICE_ACTION_ID),
    ),
    resized_hirc_objects=(
        (soundbank_editor.HIRC_EVENT, RELOAD_EVENT_ID, 12, 16),
    ),
    hirc_size_delta=382,
)


PLAN = SoundBankBuildPlan(
    name="wp_gun_cmn",
    design_ids=(
        "wp_gun_cmn.stationary_draw",
        "wp_gun_cmn.overhead_smash",
        "wp_gun_cmn.reload",
    ),
    source="original/nbnk/wp_gun_cmn.nbnk",
    target="sound/wwise/Windows/wp_gun_cmn.nbnk",
    expected_source_sha256=(
        "bba3b716b0bbaf06dfe562adf9867c43dd78b29dd5132b150f1f08142b54cfa1"
    ),
    expected_bank_id=939_294_496,
    media_additions=(
        MediaAddition(
            34,
            VOICE_MEDIA_ID,
            "audio/wp_gun_cmn/stationary_draw/"
            "raising_heart_standby_ready_01(movie_1st.raising_heart."
            "standby_ready_set_up.1).wav",
        ),
        MediaAddition(
            35,
            OVERHEAD_VOICE_MEDIA_ID,
            "audio/wp_gun_cmn/overhead_smash/"
            "nanoha_accel_01(battle_of_aces.attack_voice.attack_03.2).wav",
        ),
        MediaAddition(
            36,
            RELOAD_VOICE_MEDIA_ID,
            "audio/wp_gun_cmn/reload/"
            "raising_heart_reload_01(movie_2nd_as.raising_heart.reload.1).wav",
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
