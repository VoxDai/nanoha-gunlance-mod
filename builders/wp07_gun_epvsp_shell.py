"""Build the full-burst, Wyvern's Fire, and charged-shelling voice routes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli
from .voice_standard import (
    STANDARD_VOICE_PARENT_ID,
    STANDARD_VOICE_REFERENCE_INPUTS,
    insert_standard_voice_sound,
    standard_voice_sound_body,
)


FULL_BURST_MEDIA_IDS = (
    242_768_048,
    954_495_929,
    2_170_495_128,
    2_062_876_979,
)
FULL_BURST_SOUND_IDS = (
    960_803_121,
    479_969_098,
    2_544_331_946,
    4_251_385_954,
)
FULL_BURST_RANDOM_DONOR_ID = 58_172_267
FULL_BURST_RANDOM_DONOR_BODY_SHA256 = (
    "53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7"
)
FULL_BURST_RANDOM_DONOR_PARENT_ID = 717_111_903
FULL_BURST_RANDOM_ID = 853_759_195
FULL_BURST_RANDOM_BODY_SHA256 = (
    "6ed503ce5f4b061e412c7221932068fb105c4cb11b72e68fa4125d76ab879895"
)
FULL_BURST_PLAYLIST = tuple((sound_id, 25_000) for sound_id in FULL_BURST_SOUND_IDS)
STARLIGHT_MEDIA_ID = 322_318_543
STARLIGHT_BREAKER_MEDIA_ID = 3_332_910_283
BREAKER_MEDIA_ID = 2_217_266_443
CHARGED_SHELLING_MEDIA_IDS = (1_793_121_649,)
CHARGED_SHELLING_SOUND_IDS = (3_489_806_140,)
CHARGED_SHELLING_SOUND_SHA256S = (
    "3e27cfd8fa85fccbbee66c9dfe80a86c15e49e863629f120500719054341797c",
)
CHARGED_SHELLING_MEDIA_INDICES = (50,)
CHARGED_SHELLING_ORIGINAL_EVENT_ID = 1_308_679_810
CHARGED_SHELLING_ORIGINAL_ACTION_ID = 485_858_073
CHARGED_SHELLING_ORIGINAL_CONTAINER_ID = 1_044_832_299
CHARGED_SHELLING_ORIGINAL_EVENT_SHA256 = (
    "09b397e743d362043c390fdbab88811990f9867b882cea25cd56b59053c19347"
)
CHARGED_SHELLING_ORIGINAL_ACTION_SHA256 = (
    "0cdb30628eca7abe5b4f19bf4f70c1b08d6d93b5291c4d0b5a3b9734606f7e07"
)
CHARGED_SHELLING_DIVINE_MEDIA_ID = 370_615_719
CHARGED_SHELLING_DIVINE_SOUND_ID = 3_754_878_246
CHARGED_SHELLING_DIVINE_ACTION_ID = 583_060_699
CHARGED_SHELLING_NATIVE_STOP_TARGETS = frozenset(
    (60_034_062, 662_442_083, 1_054_468_797, 956_375_262, 599_243_561)
)
CHARGED_SHELLING_PARENT_GUARDS = (
    (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, 63_659_294, 717_111_903),
    (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, 176_125_134, 717_111_903),
    (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, 847_665_525, 717_111_903),
    (soundbank_editor.HIRC_ACTOR_MIXER, 717_111_903, 972_300_144),
    (soundbank_editor.HIRC_ACTOR_MIXER, 972_300_144, 694_534_885),
    (soundbank_editor.HIRC_ACTOR_MIXER, 694_534_885, 0),
)
WYVERN_LEFT_EVENT_ID = 3_253_425_110
WYVERN_LEFT_ORIGINAL_ACTION_ID = 120_830_402
REMOVED_LEFT_BREAKER_ACTION_ID = 2_807_447_016
REMOVED_LEFT_BREAKER_SOUND_ID = 3_070_096_299


@dataclass(frozen=True)
class FullBurstRoute:
    """One guarded native full-burst route receiving the shared Random."""

    label: str
    event_id: int
    expected_actions: tuple[int, ...]
    original_container_id: int
    donor_sound_id: int
    expected_donor_source_id: int
    action_id: int


@dataclass(frozen=True)
class OverlayRoute:
    """One guarded Event-to-Action-to-Sound overlay route."""

    label: str
    event_id: int
    expected_actions: tuple[int, ...]
    donor_sound_id: int
    expected_donor_source_id: int
    media_id: int
    action_id: int
    sound_id: int


@dataclass(frozen=True)
class StopRoute:
    """One guarded native Stop Action clone for a custom playback root."""

    label: str
    event_id: int
    expected_actions: tuple[int, ...]
    donor_action_id: int
    expected_donor_target_id: int
    expected_donor_body_sha256: str
    action_id: int
    target_id: int


@dataclass(frozen=True)
class ChargedShellingRoute:
    """One guarded native charged-shelling route receiving a voice overlay."""

    label: str
    event_id: int
    expected_actions: tuple[int, ...]
    original_container_id: int
    donor_sound_id: int
    original_media_index: int
    expected_donor_source_id: int
    action_id: int
    sound_id: int
    action_body_sha256: str
    event_body_sha256: str


FULL_BURST_ROUTES = (
    FullBurstRoute(
        "1-shell full burst",
        2_727_643_338,
        (449_657_149,),
        108_007_348,
        219_848_096,
        768_048_455,
        3_386_055_930,
    ),
    FullBurstRoute(
        "2-shell full burst",
        2_727_643_337,
        (646_158_903,),
        58_172_267,
        46_149_961,
        669_932_693,
        4_199_321_359,
    ),
    FullBurstRoute(
        "3-shell full burst",
        1_124_197_610,
        (19_077_629,),
        246_916_390,
        641_882_349,
        31_902_971,
        4_100_049_135,
    ),
    FullBurstRoute(
        "4-shell full burst",
        680_296_805,
        (223_369_281,),
        505_597_934,
        68_448_090,
        385_933_384,
        4_272_498_343,
    ),
    FullBurstRoute(
        "5-shell full burst",
        1_765_608_260,
        (403_102_539,),
        885_313_651,
        994_484_287,
        272_642_002,
        3_047_212_046,
    ),
)

WYVERNS_FIRE_ROUTES = (
    OverlayRoute(
        "Wyvern charge Nanoha Starlight",
        302_768_804,
        (51_759_545,),
        990_545_535,
        477_887_770,
        STARLIGHT_MEDIA_ID,
        4_011_774_951,
        4_149_261_730,
    ),
    OverlayRoute(
        "Wyvern charge Raising Heart Starlight Breaker",
        302_768_804,
        (51_759_545, 4_011_774_951),
        990_545_535,
        477_887_770,
        STARLIGHT_BREAKER_MEDIA_ID,
        254_514_827,
        36_215_958,
    ),
    OverlayRoute(
        "Wyvern explosion right Breaker",
        3_655_102_100,
        (648_832_766,),
        269_350_169,
        401_136_332,
        BREAKER_MEDIA_ID,
        1_866_468_495,
        2_472_459_210,
    ),
)

WYVERNS_FIRE_STOP_ROUTES = (
    StopRoute(
        "Wyvern charge Nanoha Starlight",
        461_444_626,
        (743_936_681,),
        743_936_681,
        60_034_062,
        "137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd",
        2_987_046_856,
        4_149_261_730,
    ),
    StopRoute(
        "Wyvern charge Raising Heart Starlight Breaker",
        461_444_626,
        (743_936_681, 2_987_046_856),
        743_936_681,
        60_034_062,
        "137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd",
        3_645_807_405,
        36_215_958,
    ),
)

CHARGED_SHELLING_ROUTES = (
    ChargedShellingRoute(
        "wide charged shelling explosion Buster",
        3_325_567_640,
        (116_178_715,),
        63_659_294,
        264_207_839,
        4,
        93_971_960,
        858_972_567,
        CHARGED_SHELLING_SOUND_IDS[0],
        "b3f289e77edf96d0160ec722de85a457f28f265088c300b0a610e089f60fbadf",
        "f7ece4560a68eb2ae716df1447419beca7c80990034d80ffca5119f8af136e6f",
    ),
    ChargedShellingRoute(
        "long charged shelling explosion Buster",
        1_962_814_816,
        (409_203_877,),
        176_125_134,
        220_939_954,
        33,
        693_612_246,
        4_053_288_866,
        CHARGED_SHELLING_SOUND_IDS[0],
        "d0b987c001f9f4b5edaa76a5fb978bb0e68746ff5cd0d90c2579ba2561dc8ddf",
        "60e998665371645c5ed27666fdc99753b19a133812ed225b9a7ccf42cea16ab0",
    ),
    ChargedShellingRoute(
        "normal charged shelling explosion Buster",
        2_187_565_051,
        (530_572_411,),
        847_665_525,
        69_557_296,
        37,
        849_663_903,
        3_259_504_927,
        CHARGED_SHELLING_SOUND_IDS[0],
        "d78fa1ee41964c936c18aea567e60f2aaeeb75d9ecefbaec12ed088b18a44be1",
        "a99c56c0cc31fba51053e46e71a98d7c6c8f00feda182b5ee6e767313e250163",
    ),
)


def _guard_sound_source(
    editor: soundbank_editor.HircEditor,
    sound_id: int,
    expected_source_id: int,
    label: str,
) -> None:
    donor = editor.object_body(soundbank_editor.HIRC_SOUND, sound_id)
    if (
        len(donor) < 13
        or donor[8] != 0
        or struct.unpack_from("<I", donor, 9)[0] != expected_source_id
    ):
        raise soundbank_editor.SoundBankError(
            f"target route donor Sound differs from its guard for {label}"
        )


def _guard_full_burst_original(bank: soundbank_editor.SoundBankEditor) -> None:
    editor = bank.hirc
    donor = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        FULL_BURST_RANDOM_DONOR_ID,
    )
    if hashlib.sha256(donor).hexdigest() != FULL_BURST_RANDOM_DONOR_BODY_SHA256:
        raise soundbank_editor.SoundBankError(
            "full-burst Random donor differs from its design guard"
        )
    for route in FULL_BURST_ROUTES:
        if editor.event_actions(route.event_id) != route.expected_actions:
            raise soundbank_editor.SoundBankError(
                f"original Event Action list differs for {route.label}"
            )
        original_action_id = route.expected_actions[0]
        expected_action = editor.create_play_action(
            original_action_id,
            route.original_container_id,
            bank.bank_id,
        )
        if (
            editor.object_body(soundbank_editor.HIRC_ACTION, original_action_id)
            != expected_action
        ):
            raise soundbank_editor.SoundBankError(
                f"original Action no longer targets its Container for {route.label}"
            )
        _guard_sound_source(
            editor,
            route.donor_sound_id,
            route.expected_donor_source_id,
            route.label,
        )


def _validate_full_burst_hirc(bank: soundbank_editor.SoundBankEditor) -> None:
    editor = bank.hirc
    for sound_id, media_id in zip(
        FULL_BURST_SOUND_IDS, FULL_BURST_MEDIA_IDS, strict=True
    ):
        bank.media_entry(media_id=media_id)
        expected = standard_voice_sound_body(
            sound_id,
            media_id,
            direct_parent_id=FULL_BURST_RANDOM_ID,
        )
        if editor.object_body(soundbank_editor.HIRC_SOUND, sound_id) != expected:
            raise soundbank_editor.SoundBankError(
                f"full-burst standard voice Sound differs for {sound_id}"
            )

    random_body = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        FULL_BURST_RANDOM_ID,
    )
    if (
        len(random_body) != 119
        or hashlib.sha256(random_body).hexdigest() != FULL_BURST_RANDOM_BODY_SHA256
        or editor.pitch_settings(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
            FULL_BURST_RANDOM_ID,
        )
        != soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
    ):
        raise soundbank_editor.SoundBankError(
            "full-burst Random playlist, parent, settings, or Pitch differ"
        )

    positions = {item.object_id: item.index for item in editor.objects()}
    if max(positions[sound_id] for sound_id in FULL_BURST_SOUND_IDS) >= positions[
        FULL_BURST_RANDOM_ID
    ]:
        raise soundbank_editor.SoundBankError(
            "full-burst Sounds must serialize before their Random"
        )
    for route in FULL_BURST_ROUTES:
        expected_actions = (*route.expected_actions, route.action_id)
        expected_action = editor.create_play_action(
            route.action_id,
            FULL_BURST_RANDOM_ID,
            bank.bank_id,
        )
        if (
            editor.event_actions(route.event_id) != expected_actions
            or editor.object_body(soundbank_editor.HIRC_ACTION, route.action_id)
            != expected_action
            or not (
                positions[FULL_BURST_RANDOM_ID]
                < positions[route.action_id]
                < positions[route.event_id]
            )
        ):
            raise soundbank_editor.SoundBankError(
                f"full-burst Random Play route differs for {route.label}"
            )


def _apply_full_burst(bank: soundbank_editor.SoundBankEditor) -> None:
    _guard_full_burst_original(bank)
    editor = bank.hirc
    for sound_id, media_id in zip(
        FULL_BURST_SOUND_IDS, FULL_BURST_MEDIA_IDS, strict=True
    ):
        bank.media_entry(media_id=media_id)
        insert_standard_voice_sound(
            editor,
            sound_id,
            media_id,
            direct_parent_id=FULL_BURST_RANDOM_ID,
            label=f"insert full-burst standard voice Sound {sound_id}",
        )

    editor.clone_random_sequence_container(
        FULL_BURST_RANDOM_DONOR_ID,
        FULL_BURST_RANDOM_ID,
        FULL_BURST_PLAYLIST,
        expected_playlist=((46_149_961, 50_000),),
        expected_avoid_repeat_count=1,
        avoid_repeat_count=0,
        label="clone uniform full-burst Random",
    )
    editor.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        FULL_BURST_RANDOM_ID,
        0x0B,
        FULL_BURST_RANDOM_DONOR_PARENT_ID,
        STANDARD_VOICE_PARENT_ID,
        label="parent full-burst Random to voice mixer",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        FULL_BURST_RANDOM_ID,
        expected=soundbank_editor.HircPitchSettings(None, (-50.0, 50.0)),
        random_range_cents=(-50.0, 50.0),
        label="guard full-burst Random plus/minus 50 cents Pitch",
    )

    for route in FULL_BURST_ROUTES:
        action = editor.create_play_action(
            route.action_id,
            FULL_BURST_RANDOM_ID,
            bank.bank_id,
        )
        editor.insert_object(
            soundbank_editor.HIRC_ACTION,
            route.action_id,
            action[4:],
            before=(soundbank_editor.HIRC_EVENT, route.event_id),
            label=f"add shared Random Play Action for {route.label}",
        )
        editor.append_event_action(
            route.event_id,
            route.action_id,
            expected_actions=route.expected_actions,
            label=f"append shared Random Action for {route.label}",
        )
    _validate_full_burst_hirc(bank)


def _add_overlay(
    bank: soundbank_editor.SoundBankEditor, route: OverlayRoute
) -> None:
    editor = bank.hirc
    bank.media_entry(media_id=route.media_id)
    _guard_sound_source(
        editor,
        route.donor_sound_id,
        route.expected_donor_source_id,
        route.label,
    )
    insert_standard_voice_sound(
        editor,
        route.sound_id,
        route.media_id,
        label=f"insert standard custom-voice Sound for {route.label}",
    )
    action = editor.create_play_action(route.action_id, route.sound_id, bank.bank_id)
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        route.action_id,
        action[4:],
        before=(soundbank_editor.HIRC_EVENT, route.event_id),
        label=f"add Play Action for {route.label}",
    )
    editor.append_event_action(
        route.event_id,
        route.action_id,
        expected_actions=route.expected_actions,
        label=f"append overlay Action for {route.label}",
    )


def _add_stop_route(
    bank: soundbank_editor.SoundBankEditor, route: StopRoute
) -> None:
    editor = bank.hirc
    editor.clone_stop_action(
        route.donor_action_id,
        route.action_id,
        route.target_id,
        expected_target_id=route.expected_donor_target_id,
        expected_body_sha256=route.expected_donor_body_sha256,
        before_event_id=route.event_id,
        label=f"clone native Stop Action for {route.label}",
    )
    editor.append_event_action(
        route.event_id,
        route.action_id,
        expected_actions=route.expected_actions,
        label=f"append Stop Action for {route.label}",
    )


def _event_referenced_stop_targets(
    editor: soundbank_editor.HircEditor,
) -> frozenset[int]:
    event_action_ids = {
        action_id
        for item in editor.objects()
        if item.object_type == soundbank_editor.HIRC_EVENT
        for action_id in editor.event_actions(item.object_id)
    }
    targets: set[int] = set()
    for item in editor.objects():
        if (
            item.object_type != soundbank_editor.HIRC_ACTION
            or item.object_id not in event_action_ids
        ):
            continue
        body = editor.object_body(soundbank_editor.HIRC_ACTION, item.object_id)
        if (
            len(body) >= 10
            and struct.unpack_from("<H", body, 4)[0]
            == soundbank_editor.ACTION_STOP
        ):
            targets.add(struct.unpack_from("<I", body, 6)[0])
    return frozenset(targets)


def _guard_charged_shelling_charge_event(
    bank: soundbank_editor.SoundBankEditor,
) -> None:
    editor = bank.hirc
    event_body = editor.object_body(
        soundbank_editor.HIRC_EVENT, CHARGED_SHELLING_ORIGINAL_EVENT_ID
    )
    action_body = editor.object_body(
        soundbank_editor.HIRC_ACTION, CHARGED_SHELLING_ORIGINAL_ACTION_ID
    )
    if (
        editor.event_actions(CHARGED_SHELLING_ORIGINAL_EVENT_ID)
        != (CHARGED_SHELLING_ORIGINAL_ACTION_ID,)
        or hashlib.sha256(event_body).hexdigest()
        != CHARGED_SHELLING_ORIGINAL_EVENT_SHA256
        or hashlib.sha256(action_body).hexdigest()
        != CHARGED_SHELLING_ORIGINAL_ACTION_SHA256
        or action_body
        != editor.create_play_action(
            CHARGED_SHELLING_ORIGINAL_ACTION_ID,
            CHARGED_SHELLING_ORIGINAL_CONTAINER_ID,
            bank.bank_id,
        )
    ):
        raise soundbank_editor.SoundBankError(
            "charged-shelling original charge Event or Action changed"
        )


def _guard_charged_shelling_original(
    bank: soundbank_editor.SoundBankEditor,
) -> None:
    editor = bank.hirc
    _guard_charged_shelling_charge_event(bank)
    for route in CHARGED_SHELLING_ROUTES:
        donor = editor.object_body(soundbank_editor.HIRC_SOUND, route.donor_sound_id)
        original_action_id = route.expected_actions[0]
        if (
            bank.media_entry(index=route.original_media_index).media_id
            != route.expected_donor_source_id
            or editor.event_actions(route.event_id) != route.expected_actions
            or editor.object_body(soundbank_editor.HIRC_ACTION, original_action_id)
            != editor.create_play_action(
                original_action_id, route.original_container_id, bank.bank_id
            )
            or len(donor) < 29
            or donor[8] != 0
            or struct.unpack_from("<I", donor, 9)[0]
            != route.expected_donor_source_id
            or struct.unpack_from("<I", donor, 25)[0]
            != route.original_container_id
        ):
            raise soundbank_editor.SoundBankError(
                f"charged-shelling original route differs for {route.label}"
            )

    for object_type, object_id, expected_parent_id in CHARGED_SHELLING_PARENT_GUARDS:
        body = editor.object_body(object_type, object_id)
        if (
            len(body) < 15
            or struct.unpack_from("<I", body, 11)[0] != expected_parent_id
        ):
            raise soundbank_editor.SoundBankError(
                f"charged-shelling native parent chain differs at {object_id}"
            )

    stop_targets = _event_referenced_stop_targets(editor)
    native_chain = {
        item
        for _, object_id, parent_id in CHARGED_SHELLING_PARENT_GUARDS
        for item in (object_id, parent_id)
    }
    if (
        stop_targets != CHARGED_SHELLING_NATIVE_STOP_TARGETS
        or stop_targets & native_chain
    ):
        raise soundbank_editor.SoundBankError(
            "charged-shelling native Stop Action audit differs"
        )


def validate_charged_shelling_hirc(
    bank: soundbank_editor.SoundBankEditor,
) -> None:
    _guard_charged_shelling_charge_event(bank)
    editor = bank.hirc
    if len(editor.objects()) != 203 or len(editor.build()) != 11_983:
        raise soundbank_editor.SoundBankError(
            "charged-shelling combined HIRC count or payload size differs"
        )

    for index, sound_id, media_id, expected_sha256 in zip(
        CHARGED_SHELLING_MEDIA_INDICES,
        CHARGED_SHELLING_SOUND_IDS,
        CHARGED_SHELLING_MEDIA_IDS,
        CHARGED_SHELLING_SOUND_SHA256S,
        strict=True,
    ):
        sound_body = editor.object_body(soundbank_editor.HIRC_SOUND, sound_id)
        if (
            bank.media_entry(index=index).media_id != media_id
            or sound_body != standard_voice_sound_body(sound_id, media_id)
            or hashlib.sha256(sound_body).hexdigest() != expected_sha256
            or editor.pitch_settings(soundbank_editor.HIRC_SOUND, sound_id)
            != soundbank_editor.HircPitchSettings(None, None)
        ):
            raise soundbank_editor.SoundBankError(
                f"charged-shelling standard voice Sound differs for {sound_id}"
            )

    positions = {item.object_id: item.index for item in editor.objects()}
    play_targets: dict[int, set[int]] = {
        sound_id: set() for sound_id in CHARGED_SHELLING_SOUND_IDS
    }
    for route in CHARGED_SHELLING_ROUTES:
        action_body = editor.object_body(soundbank_editor.HIRC_ACTION, route.action_id)
        event_body = editor.object_body(soundbank_editor.HIRC_EVENT, route.event_id)
        if (
            editor.event_actions(route.event_id)
            != (*route.expected_actions, route.action_id)
            or action_body
            != editor.create_play_action(route.action_id, route.sound_id, bank.bank_id)
            or hashlib.sha256(action_body).hexdigest()
            != route.action_body_sha256
            or hashlib.sha256(event_body).hexdigest() != route.event_body_sha256
            or not (
                positions[route.sound_id]
                < positions[route.action_id]
                < positions[route.event_id]
            )
        ):
            raise soundbank_editor.SoundBankError(
                f"charged-shelling Action or Event differs for {route.label}"
            )
        play_targets[route.sound_id].add(route.action_id)

    if play_targets != {
        CHARGED_SHELLING_SOUND_IDS[0]: {
            858_972_567,
            4_053_288_866,
            3_259_504_927,
        },
    }:
        raise soundbank_editor.SoundBankError(
            "charged-shelling shared voice route differs"
        )

    for item in editor.objects():
        if item.object_type != soundbank_editor.HIRC_ACTION:
            continue
        body = editor.object_body(soundbank_editor.HIRC_ACTION, item.object_id)
        if (
            len(body) >= 10
            and struct.unpack_from("<H", body, 4)[0]
            == soundbank_editor.ACTION_STOP
            and struct.unpack_from("<I", body, 6)[0]
            in CHARGED_SHELLING_SOUND_IDS
        ):
            raise soundbank_editor.SoundBankError(
                "charged-shelling voice unexpectedly received a Stop Action"
            )

    if (
        CHARGED_SHELLING_DIVINE_MEDIA_ID
        in {entry.media_id for entry in bank.original.entries}
        or CHARGED_SHELLING_DIVINE_SOUND_ID in editor.object_ids
        or CHARGED_SHELLING_DIVINE_ACTION_ID in editor.object_ids
    ):
        raise soundbank_editor.SoundBankError(
            "charged-shelling Divine route must not remain in wp07_gun_epvsp_shell"
        )


def _apply_charged_shelling(bank: soundbank_editor.SoundBankEditor) -> None:
    editor = bank.hirc
    for index, sound_id, media_id in zip(
        CHARGED_SHELLING_MEDIA_INDICES,
        CHARGED_SHELLING_SOUND_IDS,
        CHARGED_SHELLING_MEDIA_IDS,
        strict=True,
    ):
        if bank.media_entry(index=index).media_id != media_id:
            raise soundbank_editor.SoundBankError(
                f"charged-shelling DIDX #{index} identity differs"
            )
        insert_standard_voice_sound(
            editor,
            sound_id,
            media_id,
            label=f"insert charged-shelling standard voice Sound {sound_id}",
        )

    for route in CHARGED_SHELLING_ROUTES:
        action = editor.create_play_action(
            route.action_id, route.sound_id, bank.bank_id
        )
        editor.insert_object(
            soundbank_editor.HIRC_ACTION,
            route.action_id,
            action[4:],
            before=(soundbank_editor.HIRC_EVENT, route.event_id),
            label=f"add charged-shelling Play Action for {route.label}",
        )
        editor.append_event_action(
            route.event_id,
            route.action_id,
            expected_actions=route.expected_actions,
            label=f"append charged-shelling voice to {route.label}",
        )
    validate_charged_shelling_hirc(bank)


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Apply the three reviewed designs in deterministic serialization order."""

    if bank.hirc.event_actions(WYVERN_LEFT_EVENT_ID) != (
        WYVERN_LEFT_ORIGINAL_ACTION_ID,
    ):
        raise soundbank_editor.SoundBankError(
            "Wyvern left Event differs from the byte-exact no-voice path guard"
        )
    _guard_charged_shelling_original(bank)
    _apply_full_burst(bank)
    for route in WYVERNS_FIRE_ROUTES:
        _add_overlay(bank, route)
    for route in WYVERNS_FIRE_STOP_ROUTES:
        _add_stop_route(bank, route)
    _apply_charged_shelling(bank)


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=(
        (43, FULL_BURST_MEDIA_IDS[0]),
        (44, STARLIGHT_MEDIA_ID),
        (45, STARLIGHT_BREAKER_MEDIA_ID),
        (46, BREAKER_MEDIA_ID),
        (47, FULL_BURST_MEDIA_IDS[1]),
        (48, FULL_BURST_MEDIA_IDS[2]),
        (49, FULL_BURST_MEDIA_IDS[3]),
        (50, CHARGED_SHELLING_MEDIA_IDS[0]),
    ),
    hirc_changed_bytes=17,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, 960_803_121),
        (soundbank_editor.HIRC_SOUND, 479_969_098),
        (soundbank_editor.HIRC_SOUND, 2_544_331_946),
        (soundbank_editor.HIRC_SOUND, 4_251_385_954),
        (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, FULL_BURST_RANDOM_ID),
        (soundbank_editor.HIRC_ACTION, 3_386_055_930),
        (soundbank_editor.HIRC_ACTION, 4_199_321_359),
        (soundbank_editor.HIRC_ACTION, 4_100_049_135),
        (soundbank_editor.HIRC_ACTION, 4_272_498_343),
        (soundbank_editor.HIRC_ACTION, 3_047_212_046),
        (soundbank_editor.HIRC_SOUND, 4_149_261_730),
        (soundbank_editor.HIRC_ACTION, 4_011_774_951),
        (soundbank_editor.HIRC_SOUND, 36_215_958),
        (soundbank_editor.HIRC_ACTION, 254_514_827),
        (soundbank_editor.HIRC_SOUND, 2_472_459_210),
        (soundbank_editor.HIRC_ACTION, 1_866_468_495),
        (soundbank_editor.HIRC_ACTION, 2_987_046_856),
        (soundbank_editor.HIRC_ACTION, 3_645_807_405),
        (soundbank_editor.HIRC_SOUND, CHARGED_SHELLING_SOUND_IDS[0]),
        (soundbank_editor.HIRC_ACTION, 858_972_567),
        (soundbank_editor.HIRC_ACTION, 4_053_288_866),
        (soundbank_editor.HIRC_ACTION, 3_259_504_927),
    ),
    resized_hirc_objects=(
        (soundbank_editor.HIRC_EVENT, 302_768_804, 12, 20),
        (soundbank_editor.HIRC_EVENT, 461_444_626, 12, 20),
        (soundbank_editor.HIRC_EVENT, 680_296_805, 12, 16),
        (soundbank_editor.HIRC_EVENT, 1_124_197_610, 12, 16),
        (soundbank_editor.HIRC_EVENT, 1_765_608_260, 12, 16),
        (soundbank_editor.HIRC_EVENT, 1_962_814_816, 12, 16),
        (soundbank_editor.HIRC_EVENT, 2_187_565_051, 12, 16),
        (soundbank_editor.HIRC_EVENT, 2_727_643_337, 12, 16),
        (soundbank_editor.HIRC_EVENT, 2_727_643_338, 12, 16),
        (soundbank_editor.HIRC_EVENT, 3_325_567_640, 12, 16),
        (soundbank_editor.HIRC_EVENT, 3_655_102_100, 12, 16),
    ),
    hirc_size_delta=893,
)


PLAN = SoundBankBuildPlan(
    name="wp07_gun_epvsp_shell",
    design_ids=(
        "wp07_gun_epvsp_shell.full_burst",
        "wp07_gun_epvsp_shell.wyverns_fire",
        "wp07_gun_epvsp_shell.charged_shelling",
    ),
    source="original/nbnk/wp07_gun_epvsp_shell.nbnk",
    target="sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk",
    expected_source_sha256=(
        "41bb0136e89e8434d716caed9c37b399e44cd0cb057f3fa9ab706437696782a1"
    ),
    expected_bank_id=3_273_965_928,
    reference_inputs=STANDARD_VOICE_REFERENCE_INPUTS,
    media_additions=(
        MediaAddition(
            43,
            FULL_BURST_MEDIA_IDS[0],
            "audio/wp07_gun_epvsp_shell/full_burst/"
            "nanoha_shoot_01(battle_of_aces.attack_voice.attack_03.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            44,
            STARLIGHT_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/wyverns_fire/"
            "nanoha_starlight_01(gears_of_destiny.attack_voice.attack_06.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            45,
            STARLIGHT_BREAKER_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/wyverns_fire/"
            "raising_heart_starlight_breaker_01(movie_1st.raising_heart."
            "starlight_breaker.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            46,
            BREAKER_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/wyverns_fire/"
            "nanoha_breaker_01(gears_of_destiny.attack_voice.attack_06.2).wav",
            wem_channels=1,
        ),
        MediaAddition(
            47,
            FULL_BURST_MEDIA_IDS[1],
            "audio/wp07_gun_epvsp_shell/full_burst/"
            "nanoha_shoot_02(gears_of_destiny.attack_voice.attack_03.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            48,
            FULL_BURST_MEDIA_IDS[2],
            "audio/wp07_gun_epvsp_shell/full_burst/"
            "nanoha_shoot_03(movie_1st.nanoha.shoot_02.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            49,
            FULL_BURST_MEDIA_IDS[3],
            "audio/wp07_gun_epvsp_shell/full_burst/"
            "nanoha_shoot_04(movie_1st.nanoha.shoot_03.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            50,
            CHARGED_SHELLING_MEDIA_IDS[0],
            "audio/wp07_gun_epvsp_shell/charged_shelling/"
            "nanoha_buster_01(battle_of_aces.attack_004.2).wav",
            wem_channels=1,
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
