"""Guarded routes for the Motion 335 draw voice overlay and grunt mute."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
import struct

from tools import soundbank_editor as se

from .base import BuildError, BundleValidator, HircBank, MediaAddition
from .pl_voice import (
    WYR_STAKE_MUTE_EVENT_ID,
    WYR_STAKE_MUTE_RECORD_SHA256,
    WYR_STAKE_MUTE_REQUEST,
)
from .voice_standard import insert_standard_voice_sound

DESIGN_ID = "wp_gun_cmn.clutch_weapon_attack"
MOTION = 335
GROUP = "EventGroup06"
ASSIGNMENT_FRAME = 0.0
PITCH = se.HircPitchSettings(None, (-50.0, 50.0))

MUTE_EDITS = (
    se.LmtRequestEdit(MOTION, "EventGroup02", "B", ASSIGNMENT_FRAME, (16.0,), 2915504,
                      1409, WYR_STAKE_MUTE_REQUEST, 2),
    se.LmtRequestEdit(MOTION, "EventGroup02", "A", ASSIGNMENT_FRAME, (107.0,), 2915472,
                      1309, WYR_STAKE_MUTE_REQUEST, 2),
)
LMT_EDITS = (
    se.LmtRequestEdit(MOTION, GROUP, "F", ASSIGNMENT_FRAME, (5.0,), 2915840, 6470, 6613, 1),
) + MUTE_EDITS


@dataclass(frozen=True)
class Wrapper:
    edit: se.WwevRecordEdit
    donor_sha256: str
    native_action: int
    native_event_sha256: str
    native_action_sha256: str
    calls: tuple[tuple[int, int], ...]


WRAPPERS = (
    Wrapper(
        se.WwevRecordEdit(17, 6470, 3567942167, 50, 6613, 146964709, 129),
        "1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f",
        1061269777,
        "cdf654b3ef9e93d51971da97cc9479fcfd85ad8baaa6923f1a94bb6784844f15",
        "6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a",
        ((1984195518, 3567942167), (1423603563, 2405966492)),
    ),
)


@dataclass(frozen=True)
class Voice:
    media: MediaAddition
    sound: int
    action: int
    event: int
    sound_sha256: str


VOICES = (
    Voice(
        MediaAddition(
            49, 3631037616,
            "audio/wp_gun_cmn/clutch_weapon_attack/"
            "nanoha_excellion_01(movie_reflection.nanoha.excellion_buster.1).wav",
            wem_channels=1,
        ),
        507956785, 1277608954, 2405966492,
        "0b8d9f6f3c01e0f9f91234fc65954a1ec1db9f4f0c502577bd5f97dc28dfef8c",
    ),
)

WRAPPER_OBJECTS = tuple(
    obj for wrapper in WRAPPERS
    for obj in (
        *((se.HIRC_ACTION, action) for action, _ in wrapper.calls),
        (se.HIRC_EVENT, wrapper.edit.new_event_id),
    )
)
VOICE_OBJECTS = tuple(
    obj for voice in VOICES
    for obj in (
        (se.HIRC_SOUND, voice.sound),
        (se.HIRC_ACTION, voice.action),
        (se.HIRC_EVENT, voice.event),
    )
)


def _guard_native(hirc: se.HircEditor, wrapper: Wrapper) -> None:
    event = wrapper.edit.donor_event_id
    if (
        hirc.event_actions(event) != (wrapper.native_action,)
        or sha256(hirc.object_body(se.HIRC_EVENT, event)).hexdigest() != wrapper.native_event_sha256
        or sha256(hirc.object_body(se.HIRC_ACTION, wrapper.native_action)).hexdigest()
        != wrapper.native_action_sha256
    ):
        raise se.SoundBankError(f"Clutch native Event {event} or Action differs")


def apply_wrappers(hirc: se.HircEditor) -> None:
    for wrapper in WRAPPERS:
        for action, target in wrapper.calls:
            hirc.insert_object(se.HIRC_ACTION, action, hirc.create_play_event_action(action, target)[4:])
        actions = tuple(action for action, _ in wrapper.calls)
        hirc.insert_object(
            se.HIRC_EVENT, wrapper.edit.new_event_id,
            struct.pack(f"<{len(actions) + 1}I", len(actions), *actions),
        )
    _validate_wrappers(hirc)


def apply_voices(bank: se.SoundBankEditor) -> None:
    hirc = bank.hirc
    _guard_native(hirc, WRAPPERS[0])
    for voice in VOICES:
        if bank.media_entry(index=voice.media.expected_index).media_id != voice.media.media_id:
            raise se.SoundBankError("Clutch DIDX identity differs")
        insert_standard_voice_sound(hirc, voice.sound, voice.media.media_id)
        hirc.set_pitch(
            se.HIRC_SOUND, voice.sound, expected=se.HircPitchSettings(None, None),
            random_range_cents=PITCH.random_range_cents,
        )
        hirc.insert_object(
            se.HIRC_ACTION, voice.action,
            hirc.create_play_action(voice.action, voice.sound, bank.bank_id)[4:],
        )
        hirc.insert_object(se.HIRC_EVENT, voice.event, struct.pack("<II", 1, voice.action))
    _validate_voices(bank)


def _validate_wrappers(hirc: se.HircEditor) -> None:
    positions = {obj.object_id: obj.index for obj in hirc.objects()}
    owners = {
        action: [] for wrapper in WRAPPERS for action, _ in wrapper.calls
    }
    for obj in hirc.objects():
        if obj.object_type == se.HIRC_EVENT:
            for action in hirc.event_actions(obj.object_id):
                if action in owners:
                    owners[action].append(obj.object_id)
    for wrapper in WRAPPERS:
        event = wrapper.edit.new_event_id
        if hirc.event_actions(event) != tuple(action for action, _ in wrapper.calls):
            raise BuildError(f"Clutch wrapper {event} Action list differs")
        for action, target in wrapper.calls:
            if (
                hirc.object_body(se.HIRC_ACTION, action) != hirc.create_play_event_action(action, target)
                or owners[action] != [event]
                or positions[action] >= positions[event]
            ):
                raise BuildError(f"Clutch wrapper Action {action} differs")


def _validate_voices(bank: se.SoundBankEditor) -> None:
    hirc = bank.hirc
    positions = {obj.object_id: obj.index for obj in hirc.objects()}
    for voice in VOICES:
        if (
            bank.media_entry(index=voice.media.expected_index).media_id != voice.media.media_id
            or sha256(hirc.object_body(se.HIRC_SOUND, voice.sound)).hexdigest() != voice.sound_sha256
            or hirc.pitch_settings(se.HIRC_SOUND, voice.sound) != PITCH
            or hirc.event_actions(voice.event) != (voice.action,)
            or hirc.object_body(se.HIRC_ACTION, voice.action)
            != hirc.create_play_action(voice.action, voice.sound, bank.bank_id)
            or not positions[voice.sound] < positions[voice.action] < positions[voice.event]
        ):
            raise BuildError(f"Clutch voice route {voice.event} differs")


def _validate_mute_routes(original_lmt, lmt, original_voice, voice) -> None:
    mute_records = voice.records_for_request(WYR_STAKE_MUTE_REQUEST)
    if tuple((r.index, r.mode, r.event_id, r.sha256) for r in mute_records) != (
        (103, 4, WYR_STAKE_MUTE_EVENT_ID, WYR_STAKE_MUTE_RECORD_SHA256),
    ):
        raise BuildError("Clutch shared mute WWEV record differs")

    expected = []
    for edit, (index, event, digest) in zip(MUTE_EDITS, (
        (20, 967571325, "73c0de66cceb0d4c467d1652296537e0a63b53490620542d1b9174df7a3da507"),
        (18, 3262711103, "505d806915b6b08b37add31895e56e4e45faf84cc0e85883a4414873927390f9"),
    ), strict=True):
        original_records = original_voice.records_for_request(edit.old_request)
        if (
            tuple((r.index, r.mode, r.event_id, r.sha256) for r in original_records)
            != ((index, 4, event, digest),)
            or voice.records_for_request(edit.old_request) != original_records
        ):
            raise BuildError(f"Clutch original voice request {edit.old_request} differs")
        expected.append(se.TriggeredRequest(
            motion_id=MOTION, frame_count=359, timl_offset=2913472,
            shared_timl_motions=(MOTION,), event_group=edit.event_group,
            trigger_frame=edit.trigger_frames[0], trigger_mask=1 << (ord(edit.slot) - ord("A")),
            slot=edit.slot, request_no=edit.old_request, wwev_record=index,
            wwev_mode=4, event_id=event,
        ))

    def motion_voice_routes(timeline, table):
        return tuple(
            row for row in timeline.triggered_requests(table)
            if row.motion_id == MOTION and row.event_group == "EventGroup02"
        )

    muted = tuple(
        replace(row, request_no=WYR_STAKE_MUTE_REQUEST, wwev_record=103,
                event_id=WYR_STAKE_MUTE_EVENT_ID)
        for row in expected
    )
    if (
        motion_voice_routes(original_lmt, original_voice) != tuple(expected)
        or motion_voice_routes(lmt, voice) != muted
    ):
        raise BuildError("Clutch Motion 335 voice triggers differ")


def validate_bundle(staged: Mapping[Path, Path]) -> None:
    from .hm_wp07_snd_ev import PLAN as wwev_plan
    from .pl_voice import PLAN as voice_plan
    from .pl_wp_par_op_event_structure import PLAN as structure_plan
    from .w07_00 import PLAN as lmt_plan
    from .wp_gun_cmn import PLAN as common_plan, validate_wyrmstake_original_voice_mute_hirc

    root = Path(__file__).resolve().parents[1]
    original_wwev = se.WwevFile.from_file(root / wwev_plan.source)
    wwev = se.WwevFile.from_file(staged[wwev_plan.target])
    if (
        wwev.records[:len(original_wwev.records)] != original_wwev.records
        or wwev.dependencies != original_wwev.dependencies
    ):
        raise BuildError("Clutch original weapon WWEV records or dependencies changed")
    retired_events = {1767044258, 3205911733, 3228545391}
    if any(record.request_no == 6614 or record.event_id in retired_events for record in wwev.records):
        raise BuildError("Retired clutch insert WWEV route remains")
    original_lmt = se.LmtFile.from_file(root / lmt_plan.source)
    lmt = se.LmtFile.from_file(staged[lmt_plan.target])
    original_voice = se.WwevFile.from_file(root / voice_plan.source)
    voice = se.WwevFile.from_file(staged[voice_plan.target])
    _validate_mute_routes(original_lmt, lmt, original_voice, voice)
    original_routes = original_lmt.triggered_requests(original_wwev)
    native_routes = {
        (route.slot, route.wwev_record): route
        for route in original_routes
        if route.motion_id == MOTION and route.event_group == GROUP and route.slot == "F"
    }
    mute_slots = {(edit.event_group, edit.slot): edit.new_request for edit in MUTE_EDITS}
    replacements = {
        route: replace(route, request_no=mute_slots[route.event_group, route.slot])
        for route in original_routes
        if route.motion_id == MOTION and (route.event_group, route.slot) in mute_slots
    }
    for wrapper, slot in zip(WRAPPERS, ("F",), strict=True):
        edit = wrapper.edit
        donor = original_wwev.records[edit.donor_record_index - 1]
        record = wwev.records[edit.added_record_index - 1]
        if (
            donor.sha256 != wrapper.donor_sha256
            or (record.request_no, record.event_id, record.mode) != (edit.new_request, edit.new_event_id, 2)
            or record.raw[2:4] != donor.raw[2:4]
            or record.raw[8:] != donor.raw[8:]
        ):
            raise BuildError(f"Clutch WWEV clone #{edit.added_record_index} differs")
        native_route = native_routes[slot, edit.donor_record_index]
        replacements[native_route] = replace(
            native_route,
            request_no=edit.new_request, wwev_record=record.index, event_id=record.event_id,
        )
    requests = {wrapper.edit.new_request for wrapper in WRAPPERS}
    events = {wrapper.edit.new_event_id for wrapper in WRAPPERS} | {voice.event for voice in VOICES}
    actual_routes = tuple(
        route for route in lmt.triggered_requests(wwev)
        if route.motion_id == MOTION or route.request_no in requests or route.event_id in events
    )
    expected_routes = tuple(
        replacements.get(route, route) for route in original_routes if route.motion_id == MOTION
    )
    if actual_routes != expected_routes:
        raise BuildError("Clutch triggers or WWEV branch order differ")

    structure = HircBank.from_bytes(staged[structure_plan.target].read_bytes())
    wrappers = se.HircEditor(structure.hirc_payload, version=structure.version)
    common = se.SoundBankEditor.from_file(
        staged[common_plan.target], external_stop_references=common_plan.external_stop_references,
    )
    if (
        wrappers.object_ids & {1767044258, 3205911733, 2910429509, 2515977290, 2396863630}
        or common.hirc.object_ids & {3228545391, 1585582823, 690215586}
        or any(entry.media_id == 2785082779 for entry in common.original.entries)
    ):
        raise BuildError("Retired clutch insert HIRC or media remains")
    _guard_native(common.hirc, WRAPPERS[0])
    _validate_wrappers(wrappers)
    _validate_voices(common)
    validate_wyrmstake_original_voice_mute_hirc(common)


VALIDATOR = BundleValidator(
    name="clutch_weapon_attack_routes", design_id=DESIGN_ID, validate=validate_bundle,
)
