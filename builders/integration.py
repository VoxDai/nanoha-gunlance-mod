"""Cross-format validators for routes that span LMT, WWEV, and NBNK."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
import struct

from tools import soundbank_editor

from .base import BuildError, BundleValidator, HircBank
from .pl_wp_par_op_event_structure import (
    PLAN as WYR_STAKE_STRUCTURE_PLAN,
    WRAPPERS as WYR_STAKE_WRAPPERS,
    validate_wyrmstake_wrappers,
)
from .hm_wp07_snd_ev import WYR_STAKE_NEW_RECORD_SHA256S, WYR_STAKE_ROUTES
from .w07_00 import (
    WYR_STAKE_EDITS,
    WYR_STAKE_VOICE_MUTE_EDITS,
    WYR_STAKE_VOICE_MUTE_REQUEST,
)
from .wp_gun_cmn import (
    WYR_STAKE_EVENT_IDS,
    WYR_STAKE_MEDIA_IDS,
    WYR_STAKE_SOUND_IDS,
    validate_wyrmstake_voice_hirc,
    validate_wyrmstake_original_voice_mute_hirc,
    WYR_STAKE_MUTE_EMPTY_EVENT_ID,
    WYR_STAKE_MUTE_ROUTE_EVENT_ID,
)
from .hm_wp07_snd_ev import (
    CHARGED_SHELLING_DONOR_EVENT_ID,
    CHARGED_SHELLING_DONOR_MODE,
    CHARGED_SHELLING_DONOR_RECORD_SHA256,
    CHARGED_SHELLING_DONOR_REQUEST,
    CHARGED_SHELLING_NEW_EVENT_ID,
    CHARGED_SHELLING_NEW_RECORD_SHA256,
    CHARGED_SHELLING_NEW_REQUEST,
    NEW_EVENT_ID,
    NEW_REQUEST,
    OVERHEAD_ORIGINAL_MODE,
    OVERHEAD_ORIGINAL_RECORD_SHA256,
    OVERHEAD_ORIGINAL_REQUEST,
    WIDE_SWEEP_DONOR_EVENT_ID,
    WIDE_SWEEP_DONOR_MODE,
    WIDE_SWEEP_DONOR_RECORD_SHA256,
    WIDE_SWEEP_DONOR_REQUEST,
    WIDE_SWEEP_NEW_EVENT_ID,
    WIDE_SWEEP_NEW_RECORD_SHA256,
    WIDE_SWEEP_NEW_REQUEST,
)
from .pl_voice import (
    FIRING_VOICE_REQUEST,
    FIRING_VOICE_EVENT_ID,
    FIRING_VOICE_RECORD_SHA256,
    WYR_STAKE_MUTE_REQUEST,
    WYR_STAKE_MUTE_EVENT_ID,
    WYR_STAKE_MUTE_RECORD_SHA256,
    DONOR_RECORD_SHA256 as FIRING_DONOR_RECORD_SHA256,
    DONOR_EVENT_ID as ORIGINAL_GRUNT_EVENT_ID,
    DONOR_REQUEST as ORIGINAL_GRUNT_REQUEST,
    NEW_EVENT_ID as OVERHEAD_REPLACEMENT_EVENT_ID,
    NEW_RECORD_SHA256 as OVERHEAD_REPLACEMENT_RECORD_SHA256,
    NEW_REQUEST as OVERHEAD_REPLACEMENT_REQUEST,
)
from .w07_00 import (
    FIRING_VOICE_REQUEST as FIRING_LMT_REQUEST,
    FIRING_VOICE_MOTIONS,
    CHARGED_SHELLING_EVENT_GROUP,
    CHARGED_SHELLING_MOTION_IDS,
    CHARGED_SHELLING_NEW_REQUEST as CHARGED_SHELLING_LMT_REQUEST,
    CHARGED_SHELLING_SLOT,
    EVENT_GROUP,
    LINK_MOTION_ID,
    LINK_SLOT,
    MOTION_ID,
    ORIGINAL_MECHANICAL_EVENT_GROUP,
    ORIGINAL_MECHANICAL_SLOT,
    OVERHEAD_EVENT_GROUP,
    QUICK_RELOAD_MOTION_ID,
    QUICK_RELOAD_SLOT,
    SLOT,
    WIDE_SWEEP_EVENT_GROUP,
    WIDE_SWEEP_MOTION_ID,
    WIDE_SWEEP_NEW_REQUEST as WIDE_SWEEP_LMT_REQUEST,
    WIDE_SWEEP_SLOT,
)
from .wp_gun_cmn import (
    FIRING_VOICE_EVENT_ID as FIRING_BANK_EVENT_ID,
    FIRING_SILENT_BODY_GUARDS,
    CHARGED_SHELLING_EXTERNAL_STOPS as COMMON_EXTERNAL_STOPS,
    CHARGED_SHELLING_DIVINE_MEDIA_IDS,
    CHARGED_SHELLING_DIVINE_MEDIA_INDICES,
    CHARGED_SHELLING_EVENT_ID,
    OVERHEAD_DONOR_MEDIA_ID,
    OVERHEAD_DONOR_MEDIA_INDEX,
    OVERHEAD_DONOR_SOUND_ID,
    OVERHEAD_ORIGINAL_CONTAINER_ID,
    OVERHEAD_ORIGINAL_EVENT_ACTION_ID,
    OVERHEAD_ORIGINAL_EVENT_ID,
    OBSOLETE_OVERHEAD_ORIGINAL_ROUTE_ACTION_ID,
    OVERHEAD_SILENT_EVENT_ID,
    OVERHEAD_SILENT_PRIME_ACTION_ID,
    OVERHEAD_VOICE_ACTION_ID,
    OVERHEAD_VOICE_EVENT_ID,
    VOICE_EVENT_ID,
    WIDE_SWEEP_EVENT_ID,
    WIDE_SWEEP_UNUSED_EVENT_IDS,
    validate_overhead_smash_hirc,
    validate_charged_shelling_divine_hirc,
    validate_stationary_draw_hirc,
    validate_wide_sweep_hirc,
)
from .wp07_gun_epvsp_shell import (
    CHARGED_SHELLING_EXTERNAL_STOPS as SHELL_EXTERNAL_STOPS,
    CHARGED_SHELLING_MEDIA_IDS as CHARGED_SHELLING_BUSTER_MEDIA_IDS,
    CHARGED_SHELLING_MEDIA_INDICES as CHARGED_SHELLING_BUSTER_MEDIA_INDICES,
    validate_charged_shelling_hirc,
    WYR_STAKE_STRIKE_EVENT_ID,
    WYR_STAKE_STRIKE_MEDIA_ID,
    WYR_STAKE_ACS_STANDBY_MEDIA_ID,
    validate_wyrmstake_hit_release_hirc,
)


LMT_TARGET = Path("hm/wp/wp07/mot/w07_00/w07_00.lmt")
WWEV_TARGET = Path("sound/pl/hm_wp07_snd_ev.wwev")
PL_VOICE_WWEV_TARGET = Path("sound/pl/pl_voice.wwev")
BANK_TARGET = Path("sound/wwise/Windows/wp_gun_cmn.nbnk")
SHELL_BANK_TARGET = Path("sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk")
EVENT_STRUCTURE_TARGET = WYR_STAKE_STRUCTURE_PLAN.target
OBSOLETE_OVERHEAD_REQUEST = 6593
CONTROL_MOTION_ID = 151
WYR_STAKE_ORIGINAL_VOICE_EVENTS = {
    1129: 2_509_923_097,
    1105: 365_584_827,
    1019: 1_121_077_459,
    1309: 3_262_711_103,
    1119: 1_510_209_164,
    1109: 2_158_071_957,
    1009: 3_779_993_687,
}


def validate_wyrmstake_cannon(staged: Mapping[Path, Path]) -> None:
    """Resolve weapon overlays and all twelve original-voice mute routes."""

    lmt = soundbank_editor.LmtFile.from_file(_path(staged, LMT_TARGET, "Wyrmstake"))
    wwev = soundbank_editor.WwevFile.from_file(_path(staged, WWEV_TARGET, "Wyrmstake"))
    common = soundbank_editor.SoundBankEditor.from_file(_path(staged, BANK_TARGET, "Wyrmstake"))
    structure = HircBank.from_bytes(_path(staged, EVENT_STRUCTURE_TARGET, "Wyrmstake").read_bytes())
    shirc = soundbank_editor.HircEditor(structure.hirc_payload, version=structure.version)
    validate_wyrmstake_voice_hirc(common)
    validate_wyrmstake_original_voice_mute_hirc(common)
    validate_wyrmstake_wrappers(shirc)
    shell = soundbank_editor.SoundBankEditor.from_file(
        _path(staged, SHELL_BANK_TARGET, "Wyrmstake Strike Flame"),
        external_stop_references=SHELL_EXTERNAL_STOPS,
    )
    validate_wyrmstake_hit_release_hirc(shell)

    requests = {r[4]: (r[0], r[1], r[2], r[3]) for r in WYR_STAKE_ROUTES}
    for index, (donor_request, donor_event, mode, digest, request, expected_event) in enumerate(WYR_STAKE_ROUTES, 47):
        donor = wwev.record(donor_request)
        record = wwev.record(request)
        if (
                donor.event_id != donor_event or donor.mode != mode or donor.sha256 != digest
                or record.index != index or record.event_id != expected_event or record.mode != mode
                or record.sha256 != WYR_STAKE_NEW_RECORD_SHA256S[index - 47]
                or len([r for r in wwev.records if r.request_no == request]) != 1
        ):
            raise BuildError(f"Wyrmstake WWEV request {request} differs from its donor clone")

    actual = [r for r in lmt.triggered_requests(wwev) if r.request_no in requests]
    expected = {(motion, group, slot, frame, request, requests[request][2],
                 next(e for old, _, _, _, new, e in WYR_STAKE_ROUTES if new == request))
                for motion, group, slot, _, request, frames, _ in WYR_STAKE_EDITS
                for frame in frames}
    observed = {(r.motion_id, r.event_group, r.slot, r.trigger_frame,
                 r.request_no, r.wwev_mode, r.event_id) for r in actual}
    if observed != expected or len(actual) != len(expected):
        raise BuildError(f"Wyrmstake LMT/WWEV route differs: {actual!r}")
    motion310_acs = tuple(
        r for r in lmt.triggered_requests(wwev)
        if r.motion_id == 310 and r.event_group == "EventGroup07" and r.slot == "A"
    )
    expected_motion310_acs = soundbank_editor.TriggeredRequest(
        motion_id=310, frame_count=59, timl_offset=2_689_312,
        shared_timl_motions=(310,), event_group="EventGroup07",
        trigger_frame=3.0, trigger_mask=0x01, slot="A", request_no=6611,
        wwev_record=48, wwev_mode=100, event_id=4_272_667_772,
    )
    if motion310_acs != (expected_motion310_acs,):
        raise BuildError("Wyrmstake Motion 310 frame-3 ACS route differs")

    event_owners = {}
    for bank_name, hirc in (("common", common.hirc), ("structure", shirc),
                            ("shell", shell.hirc)):
        for item in hirc.objects():
            if item.object_type == soundbank_editor.HIRC_EVENT:
                event_owners.setdefault(item.object_id, []).append(bank_name)
    for wrapper_event, _, _, original_event, voice_event in WYR_STAKE_WRAPPERS:
        if (event_owners.get(wrapper_event) != ["structure"]
                or len(event_owners.get(original_event, ())) != 1
                or event_owners.get(voice_event) != ["common"]):
            raise BuildError(f"Wyrmstake wrapper {wrapper_event} has ambiguous cross-Bank targets")
    if any(common.media_entry(index=i).media_id != media
           for i, media in enumerate(WYR_STAKE_MEDIA_IDS, 47)):
        raise BuildError("Wyrmstake voice media order differs")
    if len(WYR_STAKE_SOUND_IDS) != len(WYR_STAKE_EVENT_IDS):
        raise BuildError("Wyrmstake voice Sound/Event counts differ")
    if event_owners.get(WYR_STAKE_STRIKE_EVENT_ID) != ["shell"]:
        raise BuildError("Wyrmstake hit-release Event has ambiguous ownership")
    _validate_mono_wwise_pcm(
        shell, index=52, media_id=WYR_STAKE_STRIKE_MEDIA_ID,
        sample_count=54_000, label="Wyrmstake Strike Flame DIDX #52",
    )
    _validate_mono_wwise_pcm(
        shell, index=53, media_id=WYR_STAKE_ACS_STANDBY_MEDIA_ID,
        sample_count=78_000, label="Wyrmstake ACS Standby DIDX #53",
    )

    voice = soundbank_editor.WwevFile.from_file(
        _path(staged, PL_VOICE_WWEV_TARGET, "Wyrmstake voice mute")
    )
    if (
            WYR_STAKE_VOICE_MUTE_REQUEST != WYR_STAKE_MUTE_REQUEST
            or WYR_STAKE_MUTE_EVENT_ID != WYR_STAKE_MUTE_ROUTE_EVENT_ID
    ):
        raise BuildError("Wyrmstake voice-mute request or Event IDs diverged")
    donor = voice.record(ORIGINAL_GRUNT_REQUEST)
    mute = voice.record(WYR_STAKE_MUTE_REQUEST)
    if (
            donor.event_id != ORIGINAL_GRUNT_EVENT_ID
            or donor.mode != 4
            or donor.sha256 != FIRING_DONOR_RECORD_SHA256
            or mute.index != 103
            or mute.event_id != WYR_STAKE_MUTE_EVENT_ID
            or mute.mode != 4
            or mute.sha256 != WYR_STAKE_MUTE_RECORD_SHA256
            or len(voice.records_for_request(WYR_STAKE_MUTE_REQUEST)) != 1
    ):
        raise BuildError("Wyrmstake voice-mute WWEV donor or clone differs")
    for request, original_event in WYR_STAKE_ORIGINAL_VOICE_EVENTS.items():
        records = voice.records_for_request(request)
        if len(records) != 1 or records[0].mode != 4 or records[0].event_id != original_event:
            raise BuildError(f"Wyrmstake original voice request {request} changed")

    voice_routes = lmt.triggered_requests(voice)
    selected_motions = {motion for motion, _, _, _, _ in WYR_STAKE_VOICE_MUTE_EDITS}
    selected = tuple(
        row for row in voice_routes
        if row.motion_id in selected_motions and row.event_group == "EventGroup02"
    )
    expected_voice = {
        (motion, "EventGroup02", slot, frame, WYR_STAKE_MUTE_REQUEST,
         103, 4, WYR_STAKE_MUTE_EVENT_ID)
        for motion, slot, _, frame, _ in WYR_STAKE_VOICE_MUTE_EDITS
    }
    actual_voice = {
        (row.motion_id, row.event_group, row.slot, row.trigger_frame,
         row.request_no, row.wwev_record, row.wwev_mode, row.event_id)
        for row in selected
    }
    if actual_voice != expected_voice or len(selected) != len(expected_voice):
        raise BuildError("Wyrmstake selected Motion voice routes differ")
    if tuple(row for row in voice_routes if row.request_no == WYR_STAKE_MUTE_REQUEST) != selected:
        raise BuildError("Wyrmstake mute request leaks into an unselected Motion")
    if (
            event_owners.get(WYR_STAKE_MUTE_ROUTE_EVENT_ID) != ["common"]
            or event_owners.get(WYR_STAKE_MUTE_EMPTY_EVENT_ID) != ["common"]
    ):
        raise BuildError("Wyrmstake mute Event has ambiguous cross-Bank ownership")


WYR_STAKE_VALIDATOR = BundleValidator(
    name="wyrmstake_cannon_route",
    design_id="wp07_gun_epvsp_shell.wyrmstake_cannon",
    validate=validate_wyrmstake_cannon,
)


def _path(staged: Mapping[Path, Path], target: Path, route: str) -> Path:
    try:
        return staged[target]
    except KeyError as error:
        raise BuildError(f"{route} bundle is missing nativePC/{target}") from error


def validate_stationary_draw(staged: Mapping[Path, Path]) -> None:
    """Require the one reviewed Motion→request→Event→audio route end to end."""

    lmt = soundbank_editor.LmtFile.from_file(
        _path(staged, LMT_TARGET, "stationary draw")
    )
    wwev = soundbank_editor.WwevFile.from_file(
        _path(staged, WWEV_TARGET, "stationary draw")
    )
    bank = soundbank_editor.SoundBank.from_file(
        _path(staged, BANK_TARGET, "stationary draw")
    )

    routes = tuple(
        route
        for route in lmt.triggered_requests(wwev)
        if route.request_no == NEW_REQUEST or route.event_id == NEW_EVENT_ID
    )
    expected_route = soundbank_editor.TriggeredRequest(
        motion_id=MOTION_ID,
        frame_count=91,
        timl_offset=0xC6E0,
        shared_timl_motions=(MOTION_ID,),
        event_group=EVENT_GROUP,
        trigger_frame=9.0,
        trigger_mask=0x02,
        slot=SLOT,
        request_no=NEW_REQUEST,
        wwev_record=44,
        wwev_mode=2,
        event_id=NEW_EVENT_ID,
    )
    if routes != (expected_route,):
        raise BuildError(
            "stationary draw bundle expected exactly one reviewed cross-format route; "
            f"found {routes!r}"
        )

    if VOICE_EVENT_ID != NEW_EVENT_ID:
        raise BuildError("stationary draw WWEV and Bank Event IDs diverged")
    validate_stationary_draw_hirc(soundbank_editor.SoundBankEditor(bank))


STATIONARY_DRAW_VALIDATOR = BundleValidator(
    name="stationary_draw_route",
    design_id="wp_gun_cmn.stationary_draw",
    validate=validate_stationary_draw,
)


def validate_overhead_smash(staged: Mapping[Path, Path]) -> None:
    """Require both grunt replacements and the restored original mechanical route."""

    validate_stationary_draw(staged)
    lmt = soundbank_editor.LmtFile.from_file(
        _path(staged, LMT_TARGET, "overhead smash")
    )
    mechanical_wwev = soundbank_editor.WwevFile.from_file(
        _path(staged, WWEV_TARGET, "overhead smash")
    )
    voice_wwev = soundbank_editor.WwevFile.from_file(
        _path(staged, PL_VOICE_WWEV_TARGET, "overhead smash")
    )
    bank = soundbank_editor.SoundBank.from_file(
        _path(staged, BANK_TARGET, "overhead smash")
    )

    replacement_routes = tuple(
        route
        for route in lmt.triggered_requests(voice_wwev)
        if route.request_no == OVERHEAD_REPLACEMENT_REQUEST
        or route.event_id == OVERHEAD_REPLACEMENT_EVENT_ID
    )
    expected_quick_reload = soundbank_editor.TriggeredRequest(
        motion_id=QUICK_RELOAD_MOTION_ID,
        frame_count=199,
        timl_offset=0xEF7C0,
        shared_timl_motions=(QUICK_RELOAD_MOTION_ID,),
        event_group=OVERHEAD_EVENT_GROUP,
        trigger_frame=18.0,
        trigger_mask=0x02,
        slot=QUICK_RELOAD_SLOT,
        request_no=OVERHEAD_REPLACEMENT_REQUEST,
        wwev_record=101,
        wwev_mode=4,
        event_id=OVERHEAD_REPLACEMENT_EVENT_ID,
    )
    expected_link = soundbank_editor.TriggeredRequest(
        motion_id=LINK_MOTION_ID,
        frame_count=23,
        timl_offset=0xFC040,
        shared_timl_motions=(LINK_MOTION_ID,),
        event_group=OVERHEAD_EVENT_GROUP,
        trigger_frame=14.0,
        trigger_mask=0x01,
        slot=LINK_SLOT,
        request_no=OVERHEAD_REPLACEMENT_REQUEST,
        wwev_record=101,
        wwev_mode=4,
        event_id=OVERHEAD_REPLACEMENT_EVENT_ID,
    )
    if replacement_routes != (expected_quick_reload, expected_link):
        raise BuildError(
            "overhead smash bundle expected exactly the Motion 128 and Motion 131 "
            f"character-voice replacement routes; found {replacement_routes!r}"
        )

    replacement_record = voice_wwev.record(OVERHEAD_REPLACEMENT_REQUEST)
    if (
        replacement_record.index != 101
        or replacement_record.mode != 4
        or replacement_record.event_id != OVERHEAD_REPLACEMENT_EVENT_ID
        or replacement_record.sha256 != OVERHEAD_REPLACEMENT_RECORD_SHA256
    ):
        raise BuildError("overhead smash replacement WWEV record differs from its guard")

    control_routes = tuple(
        route
        for route in lmt.triggered_requests(voice_wwev)
        if route.motion_id == CONTROL_MOTION_ID
        and route.request_no == ORIGINAL_GRUNT_REQUEST
    )
    expected_control = soundbank_editor.TriggeredRequest(
        motion_id=CONTROL_MOTION_ID,
        frame_count=199,
        timl_offset=0x14B7D0,
        shared_timl_motions=(CONTROL_MOTION_ID,),
        event_group=OVERHEAD_EVENT_GROUP,
        trigger_frame=18.0,
        trigger_mask=0x02,
        slot=QUICK_RELOAD_SLOT,
        request_no=ORIGINAL_GRUNT_REQUEST,
        wwev_record=20,
        wwev_mode=4,
        event_id=ORIGINAL_GRUNT_EVENT_ID,
    )
    if control_routes != (expected_control,):
        raise BuildError(
            "overhead smash Motion 151 original-character-voice control changed; "
            f"found {control_routes!r}"
        )

    mechanical_routes = tuple(
        route
        for route in lmt.triggered_requests(mechanical_wwev)
        if route.motion_id == QUICK_RELOAD_MOTION_ID
        and route.event_group == ORIGINAL_MECHANICAL_EVENT_GROUP
        and route.slot == ORIGINAL_MECHANICAL_SLOT
        and route.trigger_frame == 32.0
    )
    expected_mechanical = soundbank_editor.TriggeredRequest(
        motion_id=QUICK_RELOAD_MOTION_ID,
        frame_count=199,
        timl_offset=0xEF7C0,
        shared_timl_motions=(QUICK_RELOAD_MOTION_ID,),
        event_group=ORIGINAL_MECHANICAL_EVENT_GROUP,
        trigger_frame=32.0,
        trigger_mask=0x20,
        slot=ORIGINAL_MECHANICAL_SLOT,
        request_no=OVERHEAD_ORIGINAL_REQUEST,
        wwev_record=28,
        wwev_mode=OVERHEAD_ORIGINAL_MODE,
        event_id=OVERHEAD_ORIGINAL_EVENT_ID,
    )
    if mechanical_routes != (expected_mechanical,):
        raise BuildError(
            "overhead smash original frame-32 mechanical route changed; "
            f"found {mechanical_routes!r}"
        )
    mechanical_record = mechanical_wwev.record(OVERHEAD_ORIGINAL_REQUEST)
    if mechanical_record.sha256 != OVERHEAD_ORIGINAL_RECORD_SHA256:
        raise BuildError("overhead smash original mechanical WWEV record changed")
    if mechanical_wwev.records_for_request(OBSOLETE_OVERHEAD_REQUEST):
        raise BuildError("overhead smash obsolete ReqNo 6593 route is still present")

    hirc = soundbank_editor.HircEditor(bank.hirc_payload, version=bank.version)
    if OVERHEAD_VOICE_EVENT_ID != OVERHEAD_REPLACEMENT_EVENT_ID:
        raise BuildError("overhead smash WWEV and Bank Event IDs diverged")
    expected_actions = (
        OVERHEAD_SILENT_PRIME_ACTION_ID,
        OVERHEAD_VOICE_ACTION_ID,
    )
    if hirc.event_actions(OVERHEAD_VOICE_EVENT_ID) != expected_actions:
        raise BuildError(
            f"overhead smash Event {OVERHEAD_VOICE_EVENT_ID} does not contain "
            f"{expected_actions} in order"
        )
    silent_prime = hirc.object_body(
        soundbank_editor.HIRC_ACTION, OVERHEAD_SILENT_PRIME_ACTION_ID
    )
    expected_silent_prime = hirc.create_play_event_action(
        OVERHEAD_SILENT_PRIME_ACTION_ID, OVERHEAD_SILENT_EVENT_ID
    )
    if silent_prime != expected_silent_prime:
        raise BuildError(
            "overhead smash silent-prime Action does not target the zero-Action Event"
        )
    if hirc.event_actions(OVERHEAD_SILENT_EVENT_ID) != ():
        raise BuildError("overhead smash silent-prime target Event is not empty")
    if OBSOLETE_OVERHEAD_ORIGINAL_ROUTE_ACTION_ID in hirc.object_ids:
        raise BuildError("overhead smash obsolete mechanical PlayEvent Action still exists")
    if hirc.event_actions(OVERHEAD_ORIGINAL_EVENT_ID) != (
        OVERHEAD_ORIGINAL_EVENT_ACTION_ID,
    ):
        raise BuildError("overhead smash original Event route changed")

    original_action = hirc.object_body(
        soundbank_editor.HIRC_ACTION, OVERHEAD_ORIGINAL_EVENT_ACTION_ID
    )
    if (
        struct.unpack_from("<H", original_action, 4)[0]
        != soundbank_editor.ACTION_PLAY
        or struct.unpack_from("<I", original_action, 6)[0]
        != OVERHEAD_ORIGINAL_CONTAINER_ID
    ):
        raise BuildError("overhead smash original Event no longer targets its Container")
    container = hirc.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        OVERHEAD_ORIGINAL_CONTAINER_ID,
    )
    if struct.pack("<I", OVERHEAD_DONOR_SOUND_ID) not in container:
        raise BuildError("overhead smash original Container lost its donor Sound")
    donor_sound = hirc.object_body(
        soundbank_editor.HIRC_SOUND, OVERHEAD_DONOR_SOUND_ID
    )
    if struct.unpack_from("<I", donor_sound, 9)[0] != OVERHEAD_DONOR_MEDIA_ID:
        raise BuildError("overhead smash original Sound no longer references original media")
    if (
        bank.media_entry(index=OVERHEAD_DONOR_MEDIA_INDEX).media_id
        != OVERHEAD_DONOR_MEDIA_ID
    ):
        raise BuildError("overhead smash original DIDX #13 identity changed")

    validate_overhead_smash_hirc(soundbank_editor.SoundBankEditor(bank))


OVERHEAD_SMASH_VALIDATOR = BundleValidator(
    name="overhead_smash_route",
    design_id="wp_gun_cmn.overhead_smash",
    validate=validate_overhead_smash,
)


def validate_wide_sweep(staged: Mapping[Path, Path]) -> None:
    """Require one frame-11 voice and preserve later native sounds and grunts."""

    lmt = soundbank_editor.LmtFile.from_file(_path(staged, LMT_TARGET, "wide sweep"))
    wwev = soundbank_editor.WwevFile.from_file(_path(staged, WWEV_TARGET, "wide sweep"))
    bank = soundbank_editor.SoundBankEditor.from_file(_path(staged, BANK_TARGET, "wide sweep"))
    if WIDE_SWEEP_EVENT_ID != WIDE_SWEEP_NEW_EVENT_ID or WIDE_SWEEP_LMT_REQUEST != WIDE_SWEEP_NEW_REQUEST:
        raise BuildError("wide-sweep artifact request or Event IDs diverged")
    all_routes = lmt.triggered_requests(wwev)
    routes = tuple(
        row for row in all_routes
        if row.request_no == WIDE_SWEEP_NEW_REQUEST or row.event_id == WIDE_SWEEP_NEW_EVENT_ID
    )
    expected_route = soundbank_editor.TriggeredRequest(
        motion_id=WIDE_SWEEP_MOTION_ID,
        frame_count=187,
        timl_offset=0x124BE0,
        shared_timl_motions=(WIDE_SWEEP_MOTION_ID,),
        event_group=WIDE_SWEEP_EVENT_GROUP,
        trigger_frame=11.0,
        trigger_mask=0x01,
        slot=WIDE_SWEEP_SLOT,
        request_no=WIDE_SWEEP_NEW_REQUEST,
        wwev_record=45,
        wwev_mode=100,
        event_id=WIDE_SWEEP_NEW_EVENT_ID,
    )
    if routes != (expected_route,):
        raise BuildError(f"wide sweep expected exactly one frame-11 route; found {routes!r}")
    record = wwev.record(WIDE_SWEEP_NEW_REQUEST)
    if (record.index, record.mode, record.event_id, record.sha256) != (
        45, WIDE_SWEEP_DONOR_MODE, WIDE_SWEEP_NEW_EVENT_ID, WIDE_SWEEP_NEW_RECORD_SHA256
    ):
        raise BuildError("wide-sweep appended WWEV record differs from its complete guard")
    if len(wwev.records) != 49 or any(wwev.records_for_request(request) for request in (6597, 6598)):
        raise BuildError("wide-sweep WWEV contains unexpected timing candidates")
    if any(record.event_id in WIDE_SWEEP_UNUSED_EVENT_IDS for record in wwev.records):
        raise BuildError("wide-sweep WWEV still references an unused timing Event")

    native_records = (
        (WIDE_SWEEP_DONOR_REQUEST, ((22, WIDE_SWEEP_DONOR_MODE, WIDE_SWEEP_DONOR_EVENT_ID,
                                    WIDE_SWEEP_DONOR_RECORD_SHA256),)),
        (6488, ((24, 100, 2467230204,
                 "f1ad3a74af5e568cbf058b9fa10b4df01459042fd40e7b62989b51b0e3e957d9"),)),
        (6410, ((4, 200, 252365729,
                 "e7fd989c59feb3d3543d02dd77ac79113f435212f795ed371cafc59a042d218c"),
                (5, 200, 3350794741,
                 "9f39b9a7d1443461da8e5e75d6b9d7a62b54badd488494714312df74fd2553f2"))),
    )
    for request, expected_records in native_records:
        actual = tuple((r.index, r.mode, r.event_id, r.sha256) for r in wwev.records_for_request(request))
        if actual != expected_records:
            raise BuildError(f"wide-sweep original request {request} lost records, order, or conditions")
    later_routes = tuple(
        row for row in all_routes if row.motion_id == WIDE_SWEEP_MOTION_ID
        and row.event_group == WIDE_SWEEP_EVENT_GROUP and row.trigger_frame in (27.0, 49.0)
    )
    expected_later = tuple(
        replace(expected_route, trigger_frame=frame, trigger_mask=mask, slot=slot,
                request_no=request, wwev_record=index, wwev_mode=mode, event_id=event)
        for frame, mask, slot, request, index, mode, event in (
            (27.0, 0x20, "F", 6488, 24, 100, 2467230204),
            (49.0, 0x10, "E", 6410, 4, 200, 252365729),
            (49.0, 0x10, "E", 6410, 5, 200, 3350794741),
        )
    )
    if later_routes != expected_later:
        raise BuildError("wide-sweep later metal/air and paired native routes changed")

    voice_groups = [group for group in lmt.timl_for_motion(WIDE_SWEEP_MOTION_ID)
                    if soundbank_editor.EVENT_GROUP_HASHES.get(group.timeline_hash) == "EventGroup02"]
    if len(voice_groups) != 1:
        raise BuildError("wide-sweep native character-voice timeline is missing or duplicated")
    expected_keyframes = {
        soundbank_editor.REQUEST_SLOT_HASHES[0]: ((0.0, 1129),),
        soundbank_editor.REQUEST_SLOT_HASHES[1]: ((0.0, 1009),),
        soundbank_editor.TRIGGER_HASH: ((0.0, 0), (27.0, 0), (166.0, 2)),
    }
    actual_keyframes = {
        transform.datatype_hash: tuple((key.frame, key.value) for key in transform.keyframes)
        for transform in voice_groups[0].transforms
    }
    if len(voice_groups[0].transforms) != 3 or actual_keyframes != expected_keyframes:
        raise BuildError("wide-sweep disabled frame-27 or native frame-166 voice changed")
    validate_wide_sweep_hirc(bank)


WIDE_SWEEP_VALIDATOR = BundleValidator(
    name="wide_sweep_route",
    design_id="wp_gun_cmn.wide_sweep",
    validate=validate_wide_sweep,
)


def _validate_mono_wwise_pcm(
    bank: soundbank_editor.SoundBankEditor,
    *,
    index: int,
    media_id: int,
    sample_count: int,
    label: str,
) -> None:
    if bank.media_entry(index=index).media_id != media_id:
        raise BuildError(f"{label} DIDX #{index} Media ID differs")
    payload = soundbank_editor.validate_wem(bank.extract_media(index=index))
    if len(payload) < 12 or payload[:4] != b"RIFF" or payload[8:12] != b"WAVE":
        raise BuildError(f"{label} is not a RIFF/WAVE WEM")

    chunks: dict[bytes, bytes] = {}
    position = 12
    while position + 8 <= len(payload):
        tag = payload[position : position + 4]
        size = struct.unpack_from("<I", payload, position + 4)[0]
        start = position + 8
        end = start + size
        if end > len(payload):
            raise BuildError(f"{label} contains an out-of-bounds RIFF chunk")
        chunks.setdefault(tag, payload[start:end])
        position = end + (size & 1)

    expected_fmt = bytes.fromhex(
        "feff010080bb000000770100020010000600000001410000"
    )
    if chunks.get(b"fmt ") != expected_fmt:
        raise BuildError(
            f"{label} must be 48 kHz, 16-bit mono Wwise PCM with channel config "
            "000001410000"
        )
    data = chunks.get(b"data")
    if data is None or len(data) != sample_count * 2:
        actual = None if data is None else len(data) // 2
        raise BuildError(
            f"{label} expected {sample_count} mono PCM samples but found {actual}"
        )


def validate_charged_shelling(staged: Mapping[Path, Path]) -> None:
    """Require charge-start overlays and exactly three firing-silence routes."""

    lmt = soundbank_editor.LmtFile.from_file(
        _path(staged, LMT_TARGET, "charged shelling")
    )
    wwev = soundbank_editor.WwevFile.from_file(
        _path(staged, WWEV_TARGET, "charged shelling")
    )
    common_bank = soundbank_editor.SoundBankEditor.from_file(
        _path(staged, BANK_TARGET, "charged shelling"),
        external_stop_references=COMMON_EXTERNAL_STOPS,
    )
    shell_bank = soundbank_editor.SoundBankEditor.from_file(
        _path(staged, SHELL_BANK_TARGET, "charged shelling"),
        external_stop_references=SHELL_EXTERNAL_STOPS,
    )
    voice = soundbank_editor.WwevFile.from_file(
        _path(staged, PL_VOICE_WWEV_TARGET, "charged shelling")
    )
    if (FIRING_LMT_REQUEST != FIRING_VOICE_REQUEST
            or FIRING_BANK_EVENT_ID != FIRING_VOICE_EVENT_ID):
        raise BuildError("firing silence LMT/WWEV/Bank IDs diverged")
    record = voice.record(FIRING_VOICE_REQUEST)
    donor = voice.record(1409)
    original_grunt = voice.record(1305)
    if (len(voice.records) != 103
            or (record.index, record.mode, record.event_id, record.sha256)
            != (102, 4, FIRING_VOICE_EVENT_ID, FIRING_VOICE_RECORD_SHA256)
            or (donor.index, donor.mode, donor.event_id, donor.sha256)
            != (20, 4, 967571325, FIRING_DONOR_RECORD_SHA256)
            or (original_grunt.index, original_grunt.mode, original_grunt.event_id)
            != (17, 4, 281150953)):
        raise BuildError("firing silence WWEV donor, original or appended record differs")
    voice_routes = lmt.triggered_requests(voice)
    firing = tuple(r for r in voice_routes
                   if r.request_no == FIRING_VOICE_REQUEST or r.event_id == FIRING_VOICE_EVENT_ID)
    expected_firing = tuple(
        soundbank_editor.TriggeredRequest(
            motion_id=motion, frame_count=frames, timl_offset=timl,
            shared_timl_motions=(motion,), event_group="EventGroup02",
            trigger_frame=5.0, trigger_mask=1, slot="A", request_no=6608,
            wwev_record=102, wwev_mode=4, event_id=2825008231,
        ) for motion, frames, timl in ((101, 85, 603840), (102, 89, 624896), (103, 95, 645968))
    )
    selected = tuple(r for r in voice_routes if r.motion_id in FIRING_VOICE_MOTIONS
                     and r.event_group == "EventGroup02")
    if FIRING_VOICE_MOTIONS != (101, 102, 103) or firing != expected_firing or selected != expected_firing:
        raise BuildError("expected exactly Motion 101–103 frame-5 firing silence")
    weapon_routes = tuple((r.motion_id, r.slot, r.trigger_frame, r.trigger_mask, r.request_no)
                          for r in lmt.triggered_requests()
                          if r.motion_id in FIRING_VOICE_MOTIONS and r.event_group == "EventGroup06")
    expected_weapon_routes = tuple(
        (motion, slot, frame, mask, request)
        for motion in FIRING_VOICE_MOTIONS
        for slot, frame, mask, request in (("D", 8.0, 8, 6460), ("A", 43.0, 1, 6456), ("C", 58.0, 4, 6400))
    )
    if weapon_routes != expected_weapon_routes:
        raise BuildError("firing silence changed native weapon requests")
    for event, action in ((2629885944, 667354318), (1888950507, 680466555), (192028055, 511124205)):
        if shell_bank.hirc.event_actions(event) != (action,):
            raise BuildError("normal shelling must not receive a voice restoration Action")
    # All new silent objects must be owned by Common, never duplicated in another Bank.
    silent_ids = {ident for _, ident, _ in FIRING_SILENT_BODY_GUARDS}
    for target, path in staged.items():
        if target.suffix == ".nbnk" and target != BANK_TARGET:
            if target == EVENT_STRUCTURE_TARGET:
                payload = HircBank.from_bytes(path.read_bytes()).hirc_payload
            else:
                payload = soundbank_editor.SoundBank.from_file(path).hirc_payload
            if silent_ids & soundbank_editor.HircEditor(payload).object_ids:
                raise BuildError("firing silence HIRC ownership is not unique")

    if (
        CHARGED_SHELLING_LMT_REQUEST != CHARGED_SHELLING_NEW_REQUEST
        or CHARGED_SHELLING_EVENT_ID != CHARGED_SHELLING_NEW_EVENT_ID
    ):
        raise BuildError("charged-shelling LMT, WWEV, and Bank IDs diverged")

    donor = wwev.record(CHARGED_SHELLING_DONOR_REQUEST)
    if (
        donor.index,
        donor.mode,
        donor.event_id,
        donor.sha256,
    ) != (
        17,
        CHARGED_SHELLING_DONOR_MODE,
        CHARGED_SHELLING_DONOR_EVENT_ID,
        CHARGED_SHELLING_DONOR_RECORD_SHA256,
    ):
        raise BuildError("charged-shelling original WWEV donor record changed")
    record = wwev.record(CHARGED_SHELLING_NEW_REQUEST)
    if (
        record.index,
        record.mode,
        record.event_id,
        record.sha256,
    ) != (
        46,
        CHARGED_SHELLING_DONOR_MODE,
        CHARGED_SHELLING_NEW_EVENT_ID,
        CHARGED_SHELLING_NEW_RECORD_SHA256,
    ) or len(wwev.records) != 49:
        raise BuildError("charged-shelling appended WWEV record differs from its guard")

    all_routes = lmt.triggered_requests(wwev)
    routes = tuple(
        route
        for route in all_routes
        if route.request_no == CHARGED_SHELLING_NEW_REQUEST
        or route.event_id == CHARGED_SHELLING_NEW_EVENT_ID
    )
    expected_routes = tuple(
        soundbank_editor.TriggeredRequest(
            motion_id=motion_id,
            frame_count=frame_count,
            timl_offset=timl_offset,
            shared_timl_motions=(motion_id,),
            event_group=CHARGED_SHELLING_EVENT_GROUP,
            trigger_frame=1.0,
            trigger_mask=0x02,
            slot=CHARGED_SHELLING_SLOT,
            request_no=CHARGED_SHELLING_NEW_REQUEST,
            wwev_record=46,
            wwev_mode=CHARGED_SHELLING_DONOR_MODE,
            event_id=CHARGED_SHELLING_NEW_EVENT_ID,
        )
        for motion_id, frame_count, timl_offset in (
            (132, 79, 0xFE820),
            (133, 65, 0x101280),
            (134, 79, 0x1046A0),
        )
    )
    if CHARGED_SHELLING_MOTION_IDS != (132, 133, 134) or routes != expected_routes:
        raise BuildError(
            "charged shelling expected exactly the Motion 132–134 frame-1 Divine "
            f"routes; found {routes!r}"
        )

    adjustment_routes = tuple(
        route
        for route in all_routes
        if route.motion_id in (139, 140, 141, 142)
        and route.event_group == CHARGED_SHELLING_EVENT_GROUP
        and route.trigger_frame == 1.0
        and route.slot == CHARGED_SHELLING_SLOT
    )
    expected_adjustments = tuple(
        soundbank_editor.TriggeredRequest(
            motion_id=motion_id,
            frame_count=21,
            timl_offset=timl_offset,
            shared_timl_motions=(motion_id,),
            event_group=CHARGED_SHELLING_EVENT_GROUP,
            trigger_frame=1.0,
            trigger_mask=0x02,
            slot=CHARGED_SHELLING_SLOT,
            request_no=CHARGED_SHELLING_DONOR_REQUEST,
            wwev_record=17,
            wwev_mode=CHARGED_SHELLING_DONOR_MODE,
            event_id=CHARGED_SHELLING_DONOR_EVENT_ID,
        )
        for motion_id, timl_offset in (
            (139, 0x1155B0),
            (140, 0x1176D0),
            (141, 0x1199E0),
            (142, 0x11BB50),
        )
    )
    if adjustment_routes != expected_adjustments:
        raise BuildError(
            "charged-shelling Motion 139–142 posture adjustments no longer preserve "
            f"the original route; found {adjustment_routes!r}"
        )

    validate_charged_shelling_divine_hirc(common_bank)
    validate_charged_shelling_hirc(shell_bank)
    soundbank_editor.validate_external_stop_references(
        (common_bank.validate(), shell_bank.validate()),
        {
            common_bank.bank_id: COMMON_EXTERNAL_STOPS,
            shell_bank.bank_id: SHELL_EXTERNAL_STOPS,
        },
    )
    for index, media_id, samples in zip(
            CHARGED_SHELLING_DIVINE_MEDIA_INDICES,
            CHARGED_SHELLING_DIVINE_MEDIA_IDS,
            (42_000, 48_000),
            strict=True,
    ):
        _validate_mono_wwise_pcm(
            common_bank, index=index, media_id=media_id, sample_count=samples,
            label=f"charged-shelling Divine DIDX #{index}",
        )
    for index, media_id in zip(
            CHARGED_SHELLING_BUSTER_MEDIA_INDICES,
            CHARGED_SHELLING_BUSTER_MEDIA_IDS,
            strict=True,
    ):
        _validate_mono_wwise_pcm(
            shell_bank, index=index, media_id=media_id, sample_count=60_000,
            label=f"charged-shelling Buster DIDX #{index}",
        )


CHARGED_SHELLING_VALIDATOR = BundleValidator(
    name="charged_shelling_route",
    design_id="wp07_gun_epvsp_shell.charged_shelling",
    validate=validate_charged_shelling,
)


def validate_wyverns_fire(staged: Mapping[Path, Path]) -> None:
    """Prove the staged EPVSP/WWEV/Bank route and preserve the native branch."""
    from .hm_wp07_epvsp import PLAN as esp_plan
    from .hm_wp07_epvsp_snd_ev import PLAN as wwev_plan
    from .wp07_gun_epvsp_shell import PLAN as shell_plan
    from . import wyverns_fire_routes as fire

    root = Path(__file__).resolve().parents[1]
    esp = soundbank_editor.EpvspFile.from_file(staged[esp_plan.target])
    original_esp = soundbank_editor.EpvspFile.from_file(root / esp_plan.source)
    if (
        original_esp.requests[0] != fire.EPVSP_OLD_ROW
        or esp.header != original_esp.header
        or esp.requests != (fire.EPVSP_NEW_ROW, *original_esp.requests[1:])
        or esp.requests.count(fire.EPVSP_CLUTCH_ROW) != 1
    ):
        raise BuildError("Wyvern EPVSP must change only the element-2000 start request")

    original_ww = soundbank_editor.WwevFile.from_file(root / wwev_plan.source)
    ww = soundbank_editor.WwevFile.from_file(staged[wwev_plan.target])
    record = ww.record(fire.NEW_REQUEST)
    donor = original_ww.record(26501)
    if (
        donor.sha256 != fire.DONOR_RECORD_SHA256
        or ww.records != (*original_ww.records, record)
        or ww.dependencies != original_ww.dependencies
        or record.event_id != fire.PRIVATE_EVENT
        or record.mode != -1
        or record.raw[2:4] != donor.raw[2:4]
        or record.raw[8:] != donor.raw[8:]
        or ww.record(26502).event_id != fire.STOP_EVENT
    ):
        raise BuildError("Wyvern EPVSP WWEV expansion or native records changed")

    bank = soundbank_editor.SoundBankEditor.from_file(
        staged[shell_plan.target], external_stop_references=shell_plan.external_stop_references
    )
    original = soundbank_editor.SoundBankEditor.from_file(root / shell_plan.source)
    fire.validate_wyverns_fire_hirc(bank)
    for kind, ident in (
        (soundbank_editor.HIRC_EVENT, fire.CHARGE_EVENT),
        (soundbank_editor.HIRC_EVENT, fire.LEFT_EVENT),
        *((soundbank_editor.HIRC_ACTION, aid) for aid in (51_759_545, 648_832_766, 120_830_402)),
    ):
        if bank.hirc.object_body(kind, ident) != original.hirc.object_body(kind, ident):
            raise BuildError(f"Wyvern native Event or Action {ident} changed")
    final_bank = bank.validate()
    for entry in original.original.entries:
        if final_bank.extract_media(media_id=entry.media_id) != original.original.extract_media(media_id=entry.media_id):
            raise BuildError(f"Wyvern original media {entry.media_id} changed")


WYVERNS_FIRE_VALIDATOR = BundleValidator(
    name="wyverns_fire_epvsp_route",
    design_id="wp07_gun_epvsp_shell.wyverns_fire",
    validate=validate_wyverns_fire,
)
