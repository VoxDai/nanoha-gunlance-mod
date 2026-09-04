"""Build the sharpening-complete voice overlay SoundBank."""

from __future__ import annotations

import hashlib

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli
from .voice_standard import (
    STANDARD_DONOR_SOUND_BODY,
    STANDARD_VOICE_PARENT_ID,
    STANDARD_VOICE_REFERENCE_INPUTS,
    insert_standard_voice_sound,
    standard_voice_sound_body,
)


EVENT_ID = 166_276_485
ORIGINAL_ACTION_ID = 579_012_432
DONOR_SOUND_ID = 890_667_980
DONOR_MEDIA_ID = 838_569_492
DONOR_MEDIA_INDEX = 52
DONOR_RANDOM_ID = 306_760_817
DONOR_RANDOM_PARENT_ID = 914_939_451
DONOR_RANDOM_SHA256 = (
    "5f4b68b79ee8809c2c1f6bc8ed3dfde2e247e7c42a25e2b97b31cd58feb7fca0"
)

VOICE_MEDIA_ID = 2_791_080_207
CONDITION_GREEN_MEDIA_ID = 2_163_208_725
VOICE_MEDIA_IDS = (VOICE_MEDIA_ID, CONDITION_GREEN_MEDIA_ID)
VOICE_MEDIA_INDICES = (72, 73)

VOICE_ACTION_ID = 487_645_987
VOICE_SOUND_ID = 84_645_870
CONDITION_GREEN_SOUND_ID = 2_168_824_776
VOICE_SOUND_IDS = (VOICE_SOUND_ID, CONDITION_GREEN_SOUND_ID)
VOICE_RANDOM_ID = 3_800_640_078
VOICE_PLAYLIST = tuple((sound_id, 50_000) for sound_id in VOICE_SOUND_IDS)

VOICE_RANDOM_SHA256 = (
    "30dac3ea0e65598e2b1aa56e6cdca67ad72a016908dfdec627a8f744851fcec9"
)
VOICE_SOUND_SHA256S = (
    "5052b089e940f8b99e5b4f8091ebfa54f5e6de51fa09e4a1854a8c2f1598518e",
    "25b4895802884802a7955c98a9357d8b9de7e29d196c40f2da2753b38fca268d",
)
VOICE_ACTION_SHA256 = (
    "21ca6e777442d1b1f1f0e0a57ae207aaa599e428113b4dcb50fbe45b02228f5d"
)
FINAL_EVENT_SHA256 = (
    "46edd54989cd71ac293633f9c954950476e8f2e33c01e3359fcaab913fa4ae95"
)


def _guard_original_route(
        bank: soundbank_editor.SoundBankEditor,
        expected_event_actions: tuple[int, ...],
) -> None:
    editor = bank.hirc
    donor_random = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, DONOR_RANDOM_ID
    )
    if (
            bank.media_entry(index=DONOR_MEDIA_INDEX).media_id != DONOR_MEDIA_ID
            or editor.event_actions(EVENT_ID) != expected_event_actions
            or editor.object_body(soundbank_editor.HIRC_ACTION, ORIGINAL_ACTION_ID)
            != editor.create_play_action(
        ORIGINAL_ACTION_ID, DONOR_RANDOM_ID, bank.bank_id
    )
            or editor.object_body(soundbank_editor.HIRC_SOUND, DONOR_SOUND_ID)
            != STANDARD_DONOR_SOUND_BODY
            or hashlib.sha256(donor_random).hexdigest() != DONOR_RANDOM_SHA256
            or editor.pitch_settings(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, DONOR_RANDOM_ID
    )
            != soundbank_editor.HircPitchSettings(None, (-25.0, 25.0))
    ):
        raise soundbank_editor.SoundBankError(
            "sharpening-complete original route or Random donor changed"
        )


def validate_sharpen_hirc(bank: soundbank_editor.SoundBankEditor) -> None:
    """Verify the complete two-choice sharpening voice route."""

    _guard_original_route(bank, (ORIGINAL_ACTION_ID, VOICE_ACTION_ID))
    editor = bank.hirc
    if len(editor.objects()) != 303 or len(editor.build()) != 25_434:
        raise soundbank_editor.SoundBankError(
            "sharpening-complete HIRC count or payload size differs"
        )

    random_body = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, VOICE_RANDOM_ID
    )
    if (
            hashlib.sha256(random_body).hexdigest() != VOICE_RANDOM_SHA256
            or editor.pitch_settings(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, VOICE_RANDOM_ID
    )
            != soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
    ):
        raise soundbank_editor.SoundBankError(
            "sharpening-complete Random weights, repeat, parent, or Pitch differ"
        )

    for index, sound_id, media_id, expected_sha256 in zip(
            VOICE_MEDIA_INDICES,
            VOICE_SOUND_IDS,
            VOICE_MEDIA_IDS,
            VOICE_SOUND_SHA256S,
            strict=True,
    ):
        sound_body = editor.object_body(soundbank_editor.HIRC_SOUND, sound_id)
        if (
                bank.media_entry(index=index).media_id != media_id
                or sound_body
                != standard_voice_sound_body(
            sound_id, media_id, direct_parent_id=VOICE_RANDOM_ID
        )
                or hashlib.sha256(sound_body).hexdigest() != expected_sha256
                or editor.pitch_settings(soundbank_editor.HIRC_SOUND, sound_id)
                != soundbank_editor.HircPitchSettings(None, None)
        ):
            raise soundbank_editor.SoundBankError(
                "sharpening-complete voice Sound, media, parent, or Pitch differ"
            )

    action_body = editor.object_body(soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID)
    event_body = editor.object_body(soundbank_editor.HIRC_EVENT, EVENT_ID)
    if (
            action_body
            != editor.create_play_action(
        VOICE_ACTION_ID, VOICE_RANDOM_ID, bank.bank_id
    )
            or hashlib.sha256(action_body).hexdigest() != VOICE_ACTION_SHA256
            or hashlib.sha256(event_body).hexdigest() != FINAL_EVENT_SHA256
    ):
        raise soundbank_editor.SoundBankError(
            "sharpening-complete Action or Event body differs"
        )

    positions = {obj.object_id: obj.index for obj in editor.objects()}
    ordered = (*VOICE_SOUND_IDS, VOICE_RANDOM_ID, VOICE_ACTION_ID, EVENT_ID)
    if any(
            positions[left] >= positions[right]
            for left, right in zip(ordered, ordered[1:])
    ):
        raise soundbank_editor.SoundBankError(
            "sharpening-complete HIRC objects violate Wwise v120 load order"
        )


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Insert the guarded two-choice Random voice route."""

    _guard_original_route(bank, (ORIGINAL_ACTION_ID,))
    editor = bank.hirc
    for index, sound_id, media_id in zip(
            VOICE_MEDIA_INDICES, VOICE_SOUND_IDS, VOICE_MEDIA_IDS, strict=True
    ):
        if bank.media_entry(index=index).media_id != media_id:
            raise soundbank_editor.SoundBankError(
                f"sharpening-complete DIDX #{index} identity differs"
            )
        insert_standard_voice_sound(
            editor,
            sound_id,
            media_id,
            direct_parent_id=VOICE_RANDOM_ID,
            label="insert standard sharpening-complete custom-voice Sound",
        )

    editor.clone_random_sequence_container(
        DONOR_RANDOM_ID,
        VOICE_RANDOM_ID,
        VOICE_PLAYLIST,
        expected_playlist=((DONOR_SOUND_ID, 50_000),),
        expected_avoid_repeat_count=1,
        avoid_repeat_count=0,
        label="clone uniform sharpening-complete Random",
    )
    editor.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        VOICE_RANDOM_ID,
        0x0B,
        DONOR_RANDOM_PARENT_ID,
        STANDARD_VOICE_PARENT_ID,
        label="parent sharpening-complete Random to voice mixer",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        VOICE_RANDOM_ID,
        expected=soundbank_editor.HircPitchSettings(None, (-25.0, 25.0)),
        random_range_cents=(-50.0, 50.0),
        label="set sharpening-complete Random Pitch",
    )

    action = editor.create_play_action(
        VOICE_ACTION_ID, VOICE_RANDOM_ID, bank.bank_id
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        VOICE_ACTION_ID,
        action[4:],
        before=(soundbank_editor.HIRC_EVENT, EVENT_ID),
        label="add sharpening-complete Play Action",
    )
    editor.append_event_action(
        EVENT_ID,
        VOICE_ACTION_ID,
        expected_actions=(ORIGINAL_ACTION_ID,),
        label="append sharpening-complete voice to Event",
    )
    validate_sharpen_hirc(bank)


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=((72, VOICE_MEDIA_IDS[0]), (73, VOICE_MEDIA_IDS[1])),
    hirc_changed_bytes=9,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_IDS[0]),
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_IDS[1]),
        (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, VOICE_RANDOM_ID),
        (soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID),
    ),
    resized_hirc_objects=((soundbank_editor.HIRC_EVENT, EVENT_ID, 12, 16),),
    hirc_size_delta=255,
)


PLAN = SoundBankBuildPlan(
    name="wp_cmn_epvsp",
    design_ids=("wp_cmn_epvsp.sharpen",),
    source="original/nbnk/wp_cmn_epvsp.nbnk",
    target="sound/wwise/Windows/wp_cmn_epvsp.nbnk",
    expected_source_sha256=(
        "76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8"
    ),
    expected_bank_id=1_149_256_632,
    reference_inputs=STANDARD_VOICE_REFERENCE_INPUTS,
    media_additions=(
        MediaAddition(
            72,
            VOICE_MEDIA_IDS[0],
            "audio/wp_cmn_epvsp/sharpen/"
            "raising_heart_charging_completed_01(movie_1st.raising_heart."
            "charging_completed.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            73,
            VOICE_MEDIA_IDS[1],
            "audio/wp_cmn_epvsp/sharpen/"
            "raising_heart_condition_green_01(movie_1st.raising_heart."
            "condition_green.1).wav",
            wem_channels=1,
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
