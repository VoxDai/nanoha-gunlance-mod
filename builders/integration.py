"""Cross-format validators for routes that span LMT, WWEV, and NBNK."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import struct

from tools import soundbank_editor

from .base import BuildError, BundleValidator
from .hm_wp07_snd_ev import (
    NEW_EVENT_ID,
    NEW_REQUEST,
    OVERHEAD_NEW_EVENT_ID,
    OVERHEAD_NEW_REQUEST,
)
from .w07_00 import (
    EVENT_GROUP,
    MOTION_ID,
    OVERHEAD_MOTION_ID,
    OVERHEAD_SLOT,
    SLOT,
)
from .wp_gun_cmn import (
    DONOR_MEDIA_ID,
    DONOR_SOUND_ID,
    ORIGINAL_EVENT_ACTION_ID,
    ORIGINAL_EVENT_ID,
    ORIGINAL_ROUTE_ACTION_ID,
    OVERHEAD_DONOR_MEDIA_ID,
    OVERHEAD_DONOR_MEDIA_INDEX,
    OVERHEAD_DONOR_SOUND_ID,
    OVERHEAD_ORIGINAL_CONTAINER_ID,
    OVERHEAD_ORIGINAL_EVENT_ACTION_ID,
    OVERHEAD_ORIGINAL_EVENT_ID,
    OVERHEAD_ORIGINAL_ROUTE_ACTION_ID,
    OVERHEAD_VOICE_ACTION_ID,
    OVERHEAD_VOICE_EVENT_ID,
    OVERHEAD_VOICE_MEDIA_ID,
    OVERHEAD_VOICE_SOUND_ID,
    VOICE_ACTION_ID,
    VOICE_EVENT_ID,
    VOICE_MEDIA_ID,
    VOICE_SOUND_ID,
)
from .voice_standard import standard_voice_sound_body


LMT_TARGET = Path("hm/wp/wp07/mot/w07_00/w07_00.lmt")
WWEV_TARGET = Path("sound/pl/hm_wp07_snd_ev.wwev")
BANK_TARGET = Path("sound/wwise/Windows/wp_gun_cmn.nbnk")
ORIGINAL_CONTAINER_ID = 522_283_251


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

    hirc = soundbank_editor.HircEditor(bank.hirc_payload, version=bank.version)
    if VOICE_EVENT_ID != NEW_EVENT_ID:
        raise BuildError("stationary draw WWEV and Bank Event IDs diverged")
    expected_actions = (ORIGINAL_ROUTE_ACTION_ID, VOICE_ACTION_ID)
    if hirc.event_actions(VOICE_EVENT_ID) != expected_actions:
        raise BuildError(
            f"stationary draw Event {VOICE_EVENT_ID} does not contain "
            f"{expected_actions} in order"
        )

    original_route = hirc.object_body(
        soundbank_editor.HIRC_ACTION, ORIGINAL_ROUTE_ACTION_ID
    )
    expected_original_route = hirc.create_play_event_action(
        ORIGINAL_ROUTE_ACTION_ID, ORIGINAL_EVENT_ID
    )
    if original_route != expected_original_route:
        raise BuildError("stationary draw PlayEvent Action does not preserve the original Event")
    if hirc.event_actions(ORIGINAL_EVENT_ID) != (ORIGINAL_EVENT_ACTION_ID,):
        raise BuildError("stationary draw original Event route changed")

    original_action = hirc.object_body(
        soundbank_editor.HIRC_ACTION, ORIGINAL_EVENT_ACTION_ID
    )
    if (
        struct.unpack_from("<H", original_action, 4)[0]
        != soundbank_editor.ACTION_PLAY
        or struct.unpack_from("<I", original_action, 6)[0] != ORIGINAL_CONTAINER_ID
    ):
        raise BuildError("stationary draw original Event no longer targets its Container")
    container = hirc.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, ORIGINAL_CONTAINER_ID
    )
    if struct.pack("<I", DONOR_SOUND_ID) not in container:
        raise BuildError("stationary draw original Container no longer contains its donor Sound")
    donor_sound = hirc.object_body(soundbank_editor.HIRC_SOUND, DONOR_SOUND_ID)
    if struct.unpack_from("<I", donor_sound, 9)[0] != DONOR_MEDIA_ID:
        raise BuildError("stationary draw original Sound no longer references original media")
    if bank.media_entry(index=27).media_id != DONOR_MEDIA_ID:
        raise BuildError("stationary draw original DIDX #27 identity changed")

    voice_action = hirc.object_body(soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID)
    expected_voice_action = hirc.create_play_action(
        VOICE_ACTION_ID, VOICE_SOUND_ID, bank.bank_id
    )
    if voice_action != expected_voice_action:
        raise BuildError("stationary draw voice Action does not target the new Sound")
    voice_sound = hirc.object_body(soundbank_editor.HIRC_SOUND, VOICE_SOUND_ID)
    if voice_sound != standard_voice_sound_body(VOICE_SOUND_ID, VOICE_MEDIA_ID):
        raise BuildError("stationary draw voice Sound is not the standard custom-voice body")
    if bank.media_entry(index=34).media_id != VOICE_MEDIA_ID:
        raise BuildError("stationary draw added DIDX #34 identity changed")

    positions = {
        (item.object_type, item.object_id): index
        for index, item in enumerate(hirc.objects())
    }
    if not (
        positions[(soundbank_editor.HIRC_ACTION, ORIGINAL_ROUTE_ACTION_ID)]
        < positions[(soundbank_editor.HIRC_EVENT, VOICE_EVENT_ID)]
        and positions[(soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID)]
        < positions[(soundbank_editor.HIRC_EVENT, VOICE_EVENT_ID)]
        < positions[(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID)]
    ):
        raise BuildError("stationary draw HIRC objects violate Wwise v120 load order")


STATIONARY_DRAW_VALIDATOR = BundleValidator(
    name="stationary_draw_route",
    design_id="wp_gun_cmn.stationary_draw",
    validate=validate_stationary_draw,
)


def validate_overhead_smash(staged: Mapping[Path, Path]) -> None:
    """Require the isolated frame-32 overhead-smash route and original audio."""

    validate_stationary_draw(staged)
    lmt = soundbank_editor.LmtFile.from_file(
        _path(staged, LMT_TARGET, "overhead smash")
    )
    wwev = soundbank_editor.WwevFile.from_file(
        _path(staged, WWEV_TARGET, "overhead smash")
    )
    bank = soundbank_editor.SoundBank.from_file(
        _path(staged, BANK_TARGET, "overhead smash")
    )

    routes = tuple(
        route
        for route in lmt.triggered_requests(wwev)
        if route.request_no == OVERHEAD_NEW_REQUEST
        or route.event_id == OVERHEAD_NEW_EVENT_ID
    )
    expected_route = soundbank_editor.TriggeredRequest(
        motion_id=OVERHEAD_MOTION_ID,
        frame_count=199,
        timl_offset=0xEF7C0,
        shared_timl_motions=(OVERHEAD_MOTION_ID,),
        event_group=EVENT_GROUP,
        trigger_frame=32.0,
        trigger_mask=0x20,
        slot=OVERHEAD_SLOT,
        request_no=OVERHEAD_NEW_REQUEST,
        wwev_record=45,
        wwev_mode=100,
        event_id=OVERHEAD_NEW_EVENT_ID,
    )
    if routes != (expected_route,):
        raise BuildError(
            "overhead smash bundle expected exactly one reviewed cross-format route; "
            f"found {routes!r}"
        )

    hirc = soundbank_editor.HircEditor(bank.hirc_payload, version=bank.version)
    if OVERHEAD_VOICE_EVENT_ID != OVERHEAD_NEW_EVENT_ID:
        raise BuildError("overhead smash WWEV and Bank Event IDs diverged")
    expected_actions = (
        OVERHEAD_ORIGINAL_ROUTE_ACTION_ID,
        OVERHEAD_VOICE_ACTION_ID,
    )
    if hirc.event_actions(OVERHEAD_VOICE_EVENT_ID) != expected_actions:
        raise BuildError(
            f"overhead smash Event {OVERHEAD_VOICE_EVENT_ID} does not contain "
            f"{expected_actions} in order"
        )

    original_route = hirc.object_body(
        soundbank_editor.HIRC_ACTION, OVERHEAD_ORIGINAL_ROUTE_ACTION_ID
    )
    expected_original_route = hirc.create_play_event_action(
        OVERHEAD_ORIGINAL_ROUTE_ACTION_ID, OVERHEAD_ORIGINAL_EVENT_ID
    )
    if original_route != expected_original_route:
        raise BuildError("overhead smash PlayEvent Action does not preserve the original Event")
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

    voice_action = hirc.object_body(
        soundbank_editor.HIRC_ACTION, OVERHEAD_VOICE_ACTION_ID
    )
    expected_voice_action = hirc.create_play_action(
        OVERHEAD_VOICE_ACTION_ID, OVERHEAD_VOICE_SOUND_ID, bank.bank_id
    )
    if voice_action != expected_voice_action:
        raise BuildError("overhead smash voice Action does not target the new Sound")
    voice_sound = hirc.object_body(
        soundbank_editor.HIRC_SOUND, OVERHEAD_VOICE_SOUND_ID
    )
    if voice_sound != standard_voice_sound_body(
        OVERHEAD_VOICE_SOUND_ID, OVERHEAD_VOICE_MEDIA_ID
    ):
        raise BuildError("overhead smash voice Sound is not the standard custom-voice body")
    if bank.media_entry(index=35).media_id != OVERHEAD_VOICE_MEDIA_ID:
        raise BuildError("overhead smash added DIDX #35 identity changed")
    if sum(
        entry.media_id == OVERHEAD_VOICE_MEDIA_ID for entry in bank.entries
    ) != 1:
        raise BuildError("overhead smash voice Media ID is not unique")

    positions = {
        (item.object_type, item.object_id): index
        for index, item in enumerate(hirc.objects())
    }
    if not (
        positions[
            (soundbank_editor.HIRC_ACTION, OVERHEAD_ORIGINAL_ROUTE_ACTION_ID)
        ]
        < positions[(soundbank_editor.HIRC_EVENT, OVERHEAD_VOICE_EVENT_ID)]
        and positions[(soundbank_editor.HIRC_ACTION, OVERHEAD_VOICE_ACTION_ID)]
        < positions[(soundbank_editor.HIRC_EVENT, OVERHEAD_VOICE_EVENT_ID)]
        < positions[(soundbank_editor.HIRC_EVENT, OVERHEAD_ORIGINAL_EVENT_ID)]
    ):
        raise BuildError("overhead smash HIRC objects violate Wwise v120 load order")


OVERHEAD_SMASH_VALIDATOR = BundleValidator(
    name="overhead_smash_route",
    design_id="wp_gun_cmn.overhead_smash",
    validate=validate_overhead_smash,
)
