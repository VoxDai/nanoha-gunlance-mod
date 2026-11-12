"""Guarded shared Accelerator route for the three mounted finishers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import struct

from tools import soundbank_editor as se

from .base import BuildError, BundleValidator, HircBank, MediaAddition
from .voice_standard import insert_standard_voice_sound

DESIGN_ID = "wp_gun_cmn.mounted_finisher"
REQUEST = 6615
DONOR_REQUEST = 6550
LMT_EDITS = tuple(
    se.LmtRequestEdit(motion, "EventGroup06", "E", 0.0, (82.0,), offset, DONOR_REQUEST, REQUEST, 1)
    for motion, offset in ((170, 1792672), (171, 1867552), (172, 1941728))
)
WWEV_EDITS = (
    se.WwevRecordEdit(33, DONOR_REQUEST, 2925880017, 51, REQUEST, 496401681, 129),
    se.WwevRecordEdit(34, DONOR_REQUEST, 1080565533, 52, REQUEST, 3994593461, 129),
)
DONOR_RECORD_HASHES = (
    "b501ecd9ebb0baaf4ae7432ef8c25e161f372c7b298791664ad4567c1851736e",
    "0ce801814a4ba5382e311df66e9611d56c9972dad36aab2690ceb5a7ad1944fb",
)
NATIVE_ROUTES = (
    (2925880017, 1012787452,
     "c9adec59ce59bd1cf3c407f2d8efa9afa051668b423459b852ffe730cface5ca",
     "273437fb964544b5333f281a91f87099fdb7e6e0671e5ad786ca3c17f2a5b0b2"),
    (1080565533, 29680933,
     "27390d1f2a5a2a3356cd5eee0cdbafe1d9fa9f4d734a6f8fba0f469e5a8f193b",
     "b156ed03e9878e9474778f313489e1f7c9d3ac905ba4cd8d30655e94ee780ebb"),
)

VOICE_EVENT = 4197115840
VOICE_ACTION = 831225203
VOICE_SOUND = 2739514054
VOICE_SOUND_HASH = "5533fb6a951b52f8d554559b62ba2b564d0d9c3ba290362be40d407c591ecb91"
PITCH = se.HircPitchSettings(None, (-50.0, 50.0))
MEDIA = MediaAddition(
    50, 3650218823,
    "audio/wp_gun_cmn/mounted_finisher/"
    "nanoha_accelerator_01(source_audio.movie_detonation.nanoha.accelerator.1).wav",
    wem_channels=1,
)
WRAPPERS = (
    (496401681, ((2248472451, 2925880017), (2095821896, VOICE_EVENT))),
    (3994593461, ((2208167511, 1080565533),)),
)
WRAPPER_OBJECTS = tuple(
    obj for event, calls in WRAPPERS
    for obj in (*((se.HIRC_ACTION, action) for action, _ in calls), (se.HIRC_EVENT, event))
)
VOICE_OBJECTS = (
    (se.HIRC_SOUND, VOICE_SOUND),
    (se.HIRC_ACTION, VOICE_ACTION),
    (se.HIRC_EVENT, VOICE_EVENT),
)


def _guard_native(hirc: se.HircEditor) -> None:
    for event, action, event_hash, action_hash in NATIVE_ROUTES:
        if (
            hirc.event_actions(event) != (action,)
            or sha256(hirc.object_body(se.HIRC_EVENT, event)).hexdigest() != event_hash
            or sha256(hirc.object_body(se.HIRC_ACTION, action)).hexdigest() != action_hash
        ):
            raise se.SoundBankError(f"Mounted finisher native Event {event} differs")


def apply_wrappers(hirc: se.HircEditor) -> None:
    _guard_native(hirc)
    for event, calls in WRAPPERS:
        for action, target in calls:
            body = hirc.create_play_event_action(action, target)
            hirc.insert_object(se.HIRC_ACTION, action, body[4:])
        actions = tuple(action for action, _ in calls)
        hirc.insert_object(
            se.HIRC_EVENT, event, struct.pack(f"<{len(actions) + 1}I", len(actions), *actions),
        )


def apply_voice(bank: se.SoundBankEditor) -> None:
    hirc = bank.hirc
    if bank.media_entry(index=MEDIA.expected_index).media_id != MEDIA.media_id:
        raise se.SoundBankError("Mounted finisher DIDX identity differs")
    insert_standard_voice_sound(hirc, VOICE_SOUND, MEDIA.media_id)
    hirc.set_pitch(
        se.HIRC_SOUND, VOICE_SOUND, expected=se.HircPitchSettings(None, None),
        random_range_cents=PITCH.random_range_cents,
    )
    if sha256(hirc.object_body(se.HIRC_SOUND, VOICE_SOUND)).hexdigest() != VOICE_SOUND_HASH:
        raise se.SoundBankError("Mounted finisher Sound body differs")
    play = hirc.create_play_action(VOICE_ACTION, VOICE_SOUND, bank.bank_id)
    hirc.insert_object(se.HIRC_ACTION, VOICE_ACTION, play[4:])
    hirc.insert_object(se.HIRC_EVENT, VOICE_EVENT, struct.pack("<II", 1, VOICE_ACTION))


def _validate_event(hirc: se.HircEditor, event: int, actions: tuple[tuple[int, bytes], ...]) -> None:
    if hirc.event_actions(event) != tuple(action for action, _ in actions):
        raise BuildError(f"Mounted finisher Event {event} Action list differs")
    objects = hirc.objects()
    positions = {obj.object_id: obj.index for obj in objects}
    for action, body in actions:
        owners = tuple(
            obj.object_id for obj in objects
            if obj.object_type == se.HIRC_EVENT and action in hirc.event_actions(obj.object_id)
        )
        if (
            hirc.object_body(se.HIRC_ACTION, action) != body
            or owners != (event,)
            or positions[action] >= positions[event]
        ):
            raise BuildError(f"Mounted finisher Action {action} differs")


def validate_bundle(staged: Mapping[Path, Path]) -> None:
    from .hm_wp07_snd_ev import PLAN as wwev_plan
    from .pl_wp_par_op_event_structure import PLAN as structure_plan
    from .w07_00 import PLAN as lmt_plan
    from .wp_gun_cmn import PLAN as common_plan

    root = Path(__file__).resolve().parents[1]
    original_wwev = se.WwevFile.from_file(root / wwev_plan.source)
    wwev = se.WwevFile.from_file(staged[wwev_plan.target])
    if (
        wwev.records[:len(original_wwev.records)] != original_wwev.records
        or wwev.dependencies != original_wwev.dependencies
    ):
        raise BuildError("Mounted finisher original weapon WWEV records or dependencies differ")

    records = wwev.records_for_request(REQUEST)
    if len(records) != len(WWEV_EDITS):
        raise BuildError("Mounted finisher WWEV branch count differs")
    for record, edit, digest in zip(records, WWEV_EDITS, DONOR_RECORD_HASHES, strict=True):
        donor = original_wwev.records[edit.donor_record_index - 1]
        if (
            donor.sha256 != digest
            or (record.index, record.event_id, record.mode) != (edit.added_record_index, edit.new_event_id, 2)
            or record.raw[2:4] != donor.raw[2:4]
            or record.raw[8:] != donor.raw[8:]
        ):
            raise BuildError(f"Mounted finisher WWEV clone #{record.index} differs")

    original_lmt = se.LmtFile.from_file(root / lmt_plan.source)
    lmt = se.LmtFile.from_file(staged[lmt_plan.target])
    motions = {edit.motion_id for edit in LMT_EDITS}
    wrappers = {edit.new_event_id for edit in WWEV_EDITS}
    by_donor_index = {edit.donor_record_index: edit for edit in WWEV_EDITS}
    expected_routes = []
    for route in original_lmt.triggered_requests(original_wwev):
        if route.motion_id not in motions:
            continue
        if (route.event_group, route.slot, route.trigger_frame, route.request_no) == (
            "EventGroup06", "E", 82.0, DONOR_REQUEST,
        ):
            edit = by_donor_index[route.wwev_record]
            route = replace(
                route, request_no=REQUEST, wwev_record=edit.added_record_index, event_id=edit.new_event_id,
            )
        expected_routes.append(route)
    actual_routes = tuple(
        route for route in lmt.triggered_requests(wwev)
        if route.motion_id in motions or route.request_no == REQUEST or route.event_id in wrappers | {VOICE_EVENT}
    )
    if actual_routes != tuple(expected_routes) or sum(
        route.request_no == REQUEST for route in actual_routes
    ) != len(LMT_EDITS) * len(WWEV_EDITS):
        raise BuildError("Mounted finisher LMT triggers or WWEV branch order differ")

    structure = HircBank.from_bytes(staged[structure_plan.target].read_bytes())
    hirc = se.HircEditor(structure.hirc_payload, version=structure.version)
    _guard_native(hirc)
    for event, calls in WRAPPERS:
        _validate_event(hirc, event, tuple(
            (action, hirc.create_play_event_action(action, target)) for action, target in calls
        ))

    common = se.SoundBankEditor.from_file(
        staged[common_plan.target], external_stop_references=common_plan.external_stop_references,
    )
    hirc = common.hirc
    _validate_event(hirc, VOICE_EVENT, (
        (VOICE_ACTION, hirc.create_play_action(VOICE_ACTION, VOICE_SOUND, common.bank_id)),
    ))
    positions = {obj.object_id: obj.index for obj in hirc.objects()}
    if (
        common.media_entry(index=MEDIA.expected_index).media_id != MEDIA.media_id
        or hirc.pitch_settings(se.HIRC_SOUND, VOICE_SOUND) != PITCH
        or sha256(hirc.object_body(se.HIRC_SOUND, VOICE_SOUND)).hexdigest() != VOICE_SOUND_HASH
        or positions[VOICE_SOUND] >= positions[VOICE_ACTION]
    ):
        raise BuildError("Mounted finisher shared Sound, Pitch or media differs")


VALIDATOR = BundleValidator(
    name="mounted_finisher_routes", design_id=DESIGN_ID, validate=validate_bundle,
)
