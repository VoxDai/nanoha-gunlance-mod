"""Cross-format validators for routes that span LMT, WWEV, and NBNK."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
import struct

from tools import soundbank_editor

from .base import BuildError, BundleValidator
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
    DONOR_EVENT_ID as ORIGINAL_GRUNT_EVENT_ID,
    DONOR_REQUEST as ORIGINAL_GRUNT_REQUEST,
    NEW_EVENT_ID as OVERHEAD_REPLACEMENT_EVENT_ID,
    NEW_RECORD_SHA256 as OVERHEAD_REPLACEMENT_RECORD_SHA256,
    NEW_REQUEST as OVERHEAD_REPLACEMENT_REQUEST,
)
from .w07_00 import (
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
    CHARGED_SHELLING_EXTERNAL_STOPS as COMMON_EXTERNAL_STOPS,
    CHARGED_SHELLING_DIVINE_MEDIA_ID,
    CHARGED_SHELLING_DIVINE_MEDIA_INDEX,
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
)


LMT_TARGET = Path("hm/wp/wp07/mot/w07_00/w07_00.lmt")
WWEV_TARGET = Path("sound/pl/hm_wp07_snd_ev.wwev")
PL_VOICE_WWEV_TARGET = Path("sound/pl/pl_voice.wwev")
BANK_TARGET = Path("sound/wwise/Windows/wp_gun_cmn.nbnk")
SHELL_BANK_TARGET = Path("sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk")
OBSOLETE_OVERHEAD_REQUEST = 6593
CONTROL_MOTION_ID = 151


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
    if len(wwev.records) != 46 or any(wwev.records_for_request(request) for request in (6597, 6598)):
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
    """Require the three charge-start routes and both migrated voice layers."""

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
    ) or len(wwev.records) != 46:
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
    _validate_mono_wwise_pcm(
        common_bank,
        index=CHARGED_SHELLING_DIVINE_MEDIA_INDEX,
        media_id=CHARGED_SHELLING_DIVINE_MEDIA_ID,
        sample_count=42_000,
        label="charged-shelling Divine",
    )
    _validate_mono_wwise_pcm(
        shell_bank,
        index=CHARGED_SHELLING_BUSTER_MEDIA_INDICES[0],
        media_id=CHARGED_SHELLING_BUSTER_MEDIA_IDS[0],
        sample_count=54_000,
        label="charged-shelling Buster",
    )


CHARGED_SHELLING_VALIDATOR = BundleValidator(
    name="charged_shelling_route",
    design_id="wp07_gun_epvsp_shell.charged_shelling",
    validate=validate_charged_shelling,
)
