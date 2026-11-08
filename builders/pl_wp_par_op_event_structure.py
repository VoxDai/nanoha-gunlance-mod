"""Build the media-less event wrappers for Wyrmstake and clutch attacks."""

from __future__ import annotations

import hashlib
import struct

from tools import soundbank_editor

from . import clutch_weapon_attack_routes as clutch
from .base import HircBankBuildPlan, HircBankEditSummary, run_single_cli

DESIGN_ID = "wp07_gun_epvsp_shell.wyrmstake_cannon"
BANK_ID = 2_944_223_826

ORIGINAL_START_144_EVENT_ID = 2_798_914_977
ORIGINAL_START_VERTICAL_EVENT_ID = 1_517_840_452
ORIGINAL_START_VERTICAL_ACTION_ID = 446_594_426
ORIGINAL_START_VERTICAL_TARGET_ID = 381_232_159
ORIGINAL_START_VERTICAL_EVENT_SHA256 = "16fa0d520fed4ceb2268c3c208bcfd0fc7fefad2d271215c69a324ac6935fdfa"
ORIGINAL_START_VERTICAL_ACTION_SHA256 = "47c43eb3751fc1b5a0e984d2f2c0eee3bbb1ff65f82761db044581aa78579301"
ORIGINAL_RELEASE_EVENT_ID = 2_279_772_715

ACS_VOICE_EVENT_ID = 1_289_400_830
DRIVE_VOICE_EVENT_ID = 1_358_515_313

WRAPPERS = (
    (2_456_922_025, 1_727_625_947, 1_013_300_236,
     ORIGINAL_START_144_EVENT_ID, ACS_VOICE_EVENT_ID),
    (4_272_667_772, 1_192_238_746, 318_061_507,
     ORIGINAL_START_VERTICAL_EVENT_ID, ACS_VOICE_EVENT_ID),
    (3_413_751_962, 2_725_269_056, 3_159_197_441,
     ORIGINAL_RELEASE_EVENT_ID, DRIVE_VOICE_EVENT_ID),
)


def validate_wyrmstake_wrappers(hirc: soundbank_editor.HircEditor) -> None:
    """Verify ownership, Action bodies, ordering, and the original local route."""

    if (
            hirc.event_actions(ORIGINAL_START_VERTICAL_EVENT_ID)
            != (ORIGINAL_START_VERTICAL_ACTION_ID,)
            or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_EVENT,
                                               ORIGINAL_START_VERTICAL_EVENT_ID)).hexdigest()
            != ORIGINAL_START_VERTICAL_EVENT_SHA256
            or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_ACTION,
                                               ORIGINAL_START_VERTICAL_ACTION_ID)).hexdigest()
            != ORIGINAL_START_VERTICAL_ACTION_SHA256
            or struct.unpack_from("<I", hirc.object_body(soundbank_editor.HIRC_ACTION,
                                                         ORIGINAL_START_VERTICAL_ACTION_ID), 6)[0]
            != ORIGINAL_START_VERTICAL_TARGET_ID
    ):
        raise soundbank_editor.SoundBankError("original vertical Wyrmstake Event changed")
    positions = {item.object_id: item.index for item in hirc.objects()}
    owners: dict[int, int] = {}
    for item in hirc.objects():
        if item.object_type == soundbank_editor.HIRC_EVENT:
            for aid in hirc.event_actions(item.object_id):
                if aid in owners:
                    raise soundbank_editor.SoundBankError(f"Action {aid} has multiple owners")
                owners[aid] = item.object_id
    for event, original_action, voice_action, original_event, voice_event in WRAPPERS:
        if hirc.event_actions(event) != (original_action, voice_action):
            raise soundbank_editor.SoundBankError(f"Wyrmstake wrapper {event} Action list differs")
        for aid, target in ((original_action, original_event), (voice_action, voice_event)):
            if (
                    hirc.object_body(soundbank_editor.HIRC_ACTION, aid)
                    != hirc.create_play_event_action(aid, target)
                    or owners[aid] != event
                    or positions[aid] >= positions[event]
            ):
                raise soundbank_editor.SoundBankError(f"Wyrmstake wrapper Action {aid} differs")


def apply_edits(hirc: soundbank_editor.HircEditor) -> None:
    validate_original = (
            hirc.event_actions(ORIGINAL_START_VERTICAL_EVENT_ID)
            == (ORIGINAL_START_VERTICAL_ACTION_ID,)
            and hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_EVENT,
                                                ORIGINAL_START_VERTICAL_EVENT_ID)).hexdigest()
            == ORIGINAL_START_VERTICAL_EVENT_SHA256
    )
    if not validate_original:
        raise soundbank_editor.SoundBankError("original vertical Wyrmstake donor differs")
    for event, original_action, voice_action, original_event, voice_event in WRAPPERS:
        for aid, target in ((original_action, original_event), (voice_action, voice_event)):
            hirc.insert_object(soundbank_editor.HIRC_ACTION, aid,
                               hirc.create_play_event_action(aid, target)[4:],
                               label="insert Wyrmstake PlayEvent Action")
        hirc.insert_object(soundbank_editor.HIRC_EVENT, event,
                           struct.pack("<III", 2, original_action, voice_action),
                           label="insert Wyrmstake wrapper Event")
    validate_wyrmstake_wrappers(hirc)
    clutch.apply_wrappers(hirc)


EXPECTED_SUMMARY = HircBankEditSummary(
    added_hirc_objects=tuple(
        item for event, original_action, voice_action, _, _ in WRAPPERS
        for item in ((soundbank_editor.HIRC_ACTION, original_action),
                     (soundbank_editor.HIRC_ACTION, voice_action),
                     (soundbank_editor.HIRC_EVENT, event))
    ) + clutch.WRAPPER_OBJECTS,
    changed_byte_count=0,
    resized_hirc_objects=(),
    hirc_size_delta=320,
)

PLAN = HircBankBuildPlan(
    name="pl_wp_par_op_event_structure",
    design_ids=(DESIGN_ID, clutch.DESIGN_ID),
    source="original/nbnk/pl_wp_par_op_event_structure.nbnk",
    target="sound/wwise/Windows/pl_wp_par_op_event_structure.nbnk",
    expected_source_sha256="4765ba898f64dc57fca55e6015925aff49f4b9111908866b083c89a2edc63484",
    expected_bank_id=BANK_ID,
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)

if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
