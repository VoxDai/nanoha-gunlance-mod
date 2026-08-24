"""Build the isolated stationary-draw Event and voice route SoundBank."""

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


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Create a new Event that delegates to the original route and adds voice."""

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


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=((34, VOICE_MEDIA_ID),),
    hirc_changed_bytes=1,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_ID),
        (soundbank_editor.HIRC_ACTION, ORIGINAL_ROUTE_ACTION_ID),
        (soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, VOICE_EVENT_ID),
    ),
    resized_hirc_objects=(),
    hirc_size_delta=139,
)


PLAN = SoundBankBuildPlan(
    name="wp_gun_cmn",
    design_ids=("wp_gun_cmn.stationary_draw",),
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
            "raising_heart_standby_ready(movie_1st.raising_heart."
            "standby_ready_set_up.1).wav",
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
