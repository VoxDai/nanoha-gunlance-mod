"""Build the clutch-claw launch voice overlay SoundBank."""

from __future__ import annotations

import hashlib
import struct

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli
from .voice_standard import (
    STANDARD_VOICE_REFERENCE_INPUTS,
    insert_standard_voice_sound,
)

EVENT_ID = 1_419_271_252
ORIGINAL_ACTION_ID = 546_716_350
ORIGINAL_CONTAINER_ID = 334_024_264
ORIGINAL_SOUND_ID = 653_757_911
ORIGINAL_MEDIA_ID = 334_975_050
ORIGINAL_MEDIA_INDEX = 79

ORIGINAL_SOUND_SHA256 = (
    "a82d8dc855b6b2051ff301e163a5f8a9d740012b49192f8d512432a3d650a06d"
)
ORIGINAL_CONTAINER_SHA256 = (
    "7cc917007a8d22b7aa678acebf3c3f08d3dc224cc5201024555ce56485a39b4c"
)
ORIGINAL_ACTION_SHA256 = (
    "015cffb4b6d6b5f2841719a2a2a2be8b1060bba94775c3bb52622f945498a6f7"
)
ORIGINAL_EVENT_SHA256 = (
    "8179cc400c084912d8bbf4ae9feb09cfdd4068e37da1f7fcfd80ffc54da02b61"
)
ORIGINAL_PARENT_CHAIN = frozenset((334_024_264, 917_544_551, 694_534_885))

VOICE_MEDIA_ID = 259_390_702
VOICE_MEDIA_INDEX = 242
VOICE_SOUND_ID = 137_314_667
VOICE_ACTION_ID = 1_404_747_944
VOICE_PITCH = soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))

VOICE_SOUND_SHA256 = (
    "9d675712ffb82adbf9da68bc14d64c09bc3bec7b2115f73d2f53598b5c1fa409"
)
VOICE_ACTION_SHA256 = (
    "069217cd5ae92ad8de3fb1197943cc225635593e338597115f8f113b0f8db071"
)
FINAL_EVENT_SHA256 = (
    "e782c444805654508990b381a6a5d5b37d020f3a1e573762b4cc3472ba06cae3"
)


def _event_owned_stop_targets(
        editor: soundbank_editor.HircEditor,
) -> frozenset[int]:
    targets: set[int] = set()
    for item in editor.objects():
        if item.object_type != soundbank_editor.HIRC_EVENT:
            continue
        for action_id in editor.event_actions(item.object_id):
            action = editor.object_body(soundbank_editor.HIRC_ACTION, action_id)
            if (
                    len(action) >= 10
                    and struct.unpack_from("<H", action, 4)[0]
                    == soundbank_editor.ACTION_STOP
            ):
                targets.add(struct.unpack_from("<I", action, 6)[0])
    return frozenset(targets)


def _guard_original_route(
        bank: soundbank_editor.SoundBankEditor,
        expected_event_actions: tuple[int, ...],
) -> None:
    editor = bank.hirc
    original_sound = editor.object_body(
        soundbank_editor.HIRC_SOUND, ORIGINAL_SOUND_ID
    )
    original_container = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, ORIGINAL_CONTAINER_ID
    )
    original_action = editor.object_body(
        soundbank_editor.HIRC_ACTION, ORIGINAL_ACTION_ID
    )
    original_event = editor.object_body(soundbank_editor.HIRC_EVENT, EVENT_ID)
    if (
            bank.media_entry(index=ORIGINAL_MEDIA_INDEX).media_id != ORIGINAL_MEDIA_ID
            or editor.event_actions(EVENT_ID) != expected_event_actions
            or original_action
            != editor.create_play_action(
        ORIGINAL_ACTION_ID, ORIGINAL_CONTAINER_ID, bank.bank_id
    )
            or hashlib.sha256(original_sound).hexdigest() != ORIGINAL_SOUND_SHA256
            or struct.unpack_from("<I", original_sound, 9)[0] != ORIGINAL_MEDIA_ID
            or struct.unpack_from("<I", original_sound, 25)[0]
            != ORIGINAL_CONTAINER_ID
            or hashlib.sha256(original_container).hexdigest()
            != ORIGINAL_CONTAINER_SHA256
            or hashlib.sha256(original_action).hexdigest() != ORIGINAL_ACTION_SHA256
            or (
            expected_event_actions == (ORIGINAL_ACTION_ID,)
            and hashlib.sha256(original_event).hexdigest() != ORIGINAL_EVENT_SHA256
    )
            or _event_owned_stop_targets(editor) & ORIGINAL_PARENT_CHAIN
    ):
        raise soundbank_editor.SoundBankError(
            "clutch-claw launch original route, donor, or Stop audit changed"
        )


def validate_clutch_claw_launch_hirc(
        bank: soundbank_editor.SoundBankEditor,
) -> None:
    """Verify the complete clutch-claw launch voice overlay."""

    _guard_original_route(bank, (ORIGINAL_ACTION_ID, VOICE_ACTION_ID))
    editor = bank.hirc
    if len(editor.objects()) != 744 or len(editor.build()) != 40_629:
        raise soundbank_editor.SoundBankError(
            "clutch-claw launch HIRC count or payload size differs"
        )
    if bank.media_entry(index=VOICE_MEDIA_INDEX).media_id != VOICE_MEDIA_ID:
        raise soundbank_editor.SoundBankError(
            "clutch-claw launch voice DIDX identity differs"
        )

    sound = editor.object_body(soundbank_editor.HIRC_SOUND, VOICE_SOUND_ID)
    action = editor.object_body(soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID)
    event = editor.object_body(soundbank_editor.HIRC_EVENT, EVENT_ID)
    if (
            len(sound) != 55
            or hashlib.sha256(sound).hexdigest() != VOICE_SOUND_SHA256
            or editor.pitch_settings(soundbank_editor.HIRC_SOUND, VOICE_SOUND_ID)
            != VOICE_PITCH
            or action
            != editor.create_play_action(VOICE_ACTION_ID, VOICE_SOUND_ID, bank.bank_id)
            or hashlib.sha256(action).hexdigest() != VOICE_ACTION_SHA256
            or hashlib.sha256(event).hexdigest() != FINAL_EVENT_SHA256
    ):
        raise soundbank_editor.SoundBankError(
            "clutch-claw launch voice Sound, Action, or Event differs"
        )

    positions = {item.object_id: item.index for item in editor.objects()}
    ordered = (VOICE_SOUND_ID, VOICE_ACTION_ID, EVENT_ID)
    if any(
            positions[left] >= positions[right]
            for left, right in zip(ordered, ordered[1:])
    ):
        raise soundbank_editor.SoundBankError(
            "clutch-claw launch HIRC objects violate Wwise v120 load order"
        )


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Append the guarded Raising Heart voice route."""

    _guard_original_route(bank, (ORIGINAL_ACTION_ID,))
    if bank.media_entry(index=VOICE_MEDIA_INDEX).media_id != VOICE_MEDIA_ID:
        raise soundbank_editor.SoundBankError(
            "clutch-claw launch voice DIDX identity differs"
        )

    editor = bank.hirc
    insert_standard_voice_sound(
        editor,
        VOICE_SOUND_ID,
        VOICE_MEDIA_ID,
        label="insert standard clutch-claw launch custom-voice Sound",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_SOUND,
        VOICE_SOUND_ID,
        expected=soundbank_editor.HircPitchSettings(None, None),
        random_range_cents=VOICE_PITCH.random_range_cents,
        label="set clutch-claw launch voice Pitch to plus/minus 50 cents",
    )
    action = editor.create_play_action(
        VOICE_ACTION_ID, VOICE_SOUND_ID, bank.bank_id
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        VOICE_ACTION_ID,
        action[4:],
        before=(soundbank_editor.HIRC_EVENT, EVENT_ID),
        label="add clutch-claw launch voice Play Action",
    )
    editor.append_event_action(
        EVENT_ID,
        VOICE_ACTION_ID,
        expected_actions=(ORIGINAL_ACTION_ID,),
        label="append Raising Heart voice to clutch-claw launch Event",
    )
    validate_clutch_claw_launch_hirc(bank)


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=((VOICE_MEDIA_INDEX, VOICE_MEDIA_ID),),
    hirc_changed_bytes=9,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_ID),
        (soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID),
    ),
    resized_hirc_objects=(
        (soundbank_editor.HIRC_EVENT, EVENT_ID, 12, 16),
    ),
    hirc_size_delta=87,
)

PLAN = SoundBankBuildPlan(
    name="pl_prop_cmn",
    design_ids=("pl_prop_cmn.clutch_claw_launch",),
    source="original/nbnk/pl_prop_cmn.nbnk",
    target="sound/wwise/Windows/pl_prop_cmn.nbnk",
    expected_source_sha256=(
        "47e15d2a786b3ca04c368faeeeb7c32062f6ddcc9e38aaa508942c9b4dc5697c"
    ),
    expected_bank_id=4_182_706_408,
    reference_inputs=STANDARD_VOICE_REFERENCE_INPUTS,
    media_additions=(
        MediaAddition(
            VOICE_MEDIA_INDEX,
            VOICE_MEDIA_ID,
            "audio/pl_prop_cmn/clutch_claw_launch/"
            "raising_heart_flier_fin_01(movie_1st.raising_heart.flier_fin.1).wav",
            wem_channels=1,
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)

if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
