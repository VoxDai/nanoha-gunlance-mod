"""Build the full-burst, Wyvern's Fire, and charged-shelling voice routes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli
from .wyverns_fire_routes import CLIPS as WYVERN_CLIPS, EXTRA_FILENAMES, apply_wyverns_fire
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
CHARGED_SHELLING_MEDIA_IDS = (1_793_121_649, 570_980_126, 2_785_082_779)
CHARGED_SHELLING_SOUND_IDS = (3_489_806_140, 3_928_375_835, 690_215_586)
CHARGED_SHELLING_SOUND_SHA256S = (
    "bbc603bac06e30ea54aa58de3b749e1d413c8275c2834a931e015b8835c7e06d",
    "2e5a7e3eb467114ad41a2a742e5204f51a5dcf9bf45bc0a011f8c1a3cd8663a4",
    "8851587d5cec37e5055865facfd818745aa344bf30ca4a001f5caea89b87bcf0",
)
CHARGED_SHELLING_MEDIA_INDICES = (50, 51, 59)
WYR_STAKE_STRIKE_MEDIA_ID = 949_600_199
WYR_STAKE_STRIKE_SOUND_ID = 38_895_430
WYR_STAKE_STRIKE_ACTION_ID = 1_821_689_211
WYR_STAKE_STRIKE_EVENT_ID = 1_581_859_410
WYR_STAKE_STRIKE_ORIGINAL_ACTION_ID = 705_609_317
WYR_STAKE_STRIKE_ORIGINAL_CONTAINER_ID = 75_663_767
WYR_STAKE_STRIKE_ORIGINAL_SOUND_ID = 151_638_268
WYR_STAKE_STRIKE_ORIGINAL_MEDIA_ID = 629_066_097
WYR_STAKE_ACS_STANDBY_MEDIA_ID = 938_668_400
WYR_STAKE_ACS_STANDBY_SOUND_ID = 1_727_570_929
WYR_STAKE_HIT_RANDOM_ID = 2_393_951_905
WYR_STAKE_HIT_RANDOM_DONOR_ID = 58_172_267
WYR_STAKE_HIT_RANDOM_DONOR_SHA256 = "53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7"
WYR_STAKE_HIT_PLAYLIST = (
    (WYR_STAKE_STRIKE_SOUND_ID, 50_000),
    (WYR_STAKE_ACS_STANDBY_SOUND_ID, 50_000),
)
WYR_STAKE_STRIKE_SOUND_SHA256 = "05b6321f093b39b5a0ebd59c8bf0208b117680a6541d60eabd1d64868f38ca3b"
WYR_STAKE_ACS_STANDBY_SOUND_SHA256 = "ad97250dde54b4126721605eca752ca090b214d0ec40b135cf930ee07bd8528c"
WYR_STAKE_HIT_RANDOM_SHA256 = "7a018ec43f7d5f17ff03bddb144b2f8237f5d04d108ecc04a5bf68b7045dd95c"
WYR_STAKE_HIT_PITCH = soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
WYR_STAKE_STRIKE_ACTION_SHA256 = "5f4a3da7a272d283668687ca5cc137ce3cc3d1e7b9944ca2ccde2f95a6005d78"
WYR_STAKE_STRIKE_EVENT_SHA256 = "a47d26b6238ffb6d0552bd9b3438dfb2cba86a15cc59a266d1f6d5b412ce7fa6"
WYR_STAKE_STRIKE_NATIVE_GUARDS = (
    (28, WYR_STAKE_STRIKE_ORIGINAL_MEDIA_ID, WYR_STAKE_STRIKE_EVENT_ID,
     WYR_STAKE_STRIKE_ORIGINAL_ACTION_ID, WYR_STAKE_STRIKE_ORIGINAL_CONTAINER_ID,
     "5e098d73a0645fc0d81188cadafe728e3325fd9eda7c67230d85579676e9b26d",
     "29045c6ed5c13a286828f7c6e351b3b75a6f8b781539a59861b0cde3aa700521"),
    (38, 858_252_802, 3_115_395_173, 951_626_294, 1_049_048_275,
     "fe73b26bcad55501da8c1dcbc4298069cf4e3748d81e12589b61b203089b1340",
     "d4e189a50744ef1b00b429df4ee15fc90e93a466089d139c4f519d2313e29c19"),
    (40, 932_229_979, 1_465_516_383, 208_572_495, 969_725_659,
     "2c7b630cdd0276e580e69fcbe8a751ff13f4faee6df765cf87887cdc75fd1962",
     "62d140af4d2431b7da43e4ca08246271d73da2d2cc544b7d78bd8839c9452450"),
)
WYR_STAKE_STRIKE_CONTAINER_SHA256 = "43f44064e18427629d77e5a482d03f415822739ce82b138d07a4372a74cfceb8"
WYR_STAKE_STRIKE_ORIGINAL_SOUND_SHA256 = "a1208fe2fdb8a16dd7ec60f1c904ff593922a5d6d06e892a19ea0bbe6192f8b5"
WYR_STAKE_STRIKE_NATIVE_PARENT_CHAIN = (
    (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, 75_663_767, 717_111_903),
    (soundbank_editor.HIRC_ACTOR_MIXER, 717_111_903, 972_300_144),
    (soundbank_editor.HIRC_ACTOR_MIXER, 972_300_144, 694_534_885),
    (soundbank_editor.HIRC_ACTOR_MIXER, 694_534_885, 0),
)
WYR_STAKE_STRIKE_NATIVE_STOP_TARGETS = {
    60_034_062, 662_442_083, 1_054_468_797, 956_375_262, 599_243_561,
}

CHARGED_SHELLING_RANDOM_ID = 2_510_752_860
CHARGED_SHELLING_RANDOM_DONOR_ID = 58_172_267
CHARGED_SHELLING_RANDOM_DONOR_SHA256 = (
    "53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7"
)
CHARGED_SHELLING_RANDOM_SHA256 = (
    "1d3240b0b6205ac132d53ddf81f7647375ae2c56a365e4c904d7819491862a33"
)
CHARGED_SHELLING_PLAYLIST = tuple((sid, 50_000) for sid in CHARGED_SHELLING_SOUND_IDS)
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
CHARGED_SHELLING_DIVINE_MEDIA_IDS = (CHARGED_SHELLING_DIVINE_MEDIA_ID, 3_246_372_848)
CHARGED_SHELLING_DIVINE_SOUND_IDS = (CHARGED_SHELLING_DIVINE_SOUND_ID, 4_035_275_377)
CHARGED_SHELLING_DIVINE_RANDOM_ID = 1_153_640_130
# Every Event owns separate Actions for both opposite-phase candidate Sounds.
CHARGED_SHELLING_STOP_ACTIONS = {
    3_325_567_640: (1_426_818_832, 515_837_897),
    1_962_814_816: (1_225_287_532, 1_287_808_358),
    2_187_565_051: (728_690_884, 1_267_644_869),
}
CHARGED_SHELLING_STOP_SHA256S = {
    1_426_818_832: "f8a9743e56e31058af5bff91c2ae436b5072e3e9a63eb7b16e4d6cba44dd4afe",
    1_225_287_532: "7e8d8ce0db11ffde1a86d83040ee5812dad92236b33609a912b36ef890268c51",
    728_690_884: "f35bb797fa57be95f56310f8c2ab6e5d25bee71e19485095d816fe0c35a23e03",
    515_837_897: "528b713f34e7cadf416b2612ba9cc56a7813ad1f54409fcdcb4172610f114de7",
    1_287_808_358: "6f9143c623e3e346b9a72f77961b896c8e67b70101113fac9ade4f8ddae9f051",
    1_267_644_869: "e13eb2147999bf1de1e6e4b45a82ff8d241ee91ad564d1a34068f9fd4b2f9724",
}
CHARGED_SHELLING_EXTERNAL_STOPS = tuple(
    soundbank_editor.ExternalStopReference(
        action_id, 939_294_496, sound_id, body_sha256,
    )
    for action_ids in CHARGED_SHELLING_STOP_ACTIONS.values()
    for action_id, sound_id, body_sha256 in zip(
        action_ids,
        CHARGED_SHELLING_DIVINE_SOUND_IDS,
        (
            "251b8841b03f2489535afa09e60afae689137fbc3249a0a60bab8cd7481e372d",
            "047453c18d735292b6965b2dfb4e83b79803bf9311836232b60bad6a9da27b87",
        ),
        strict=True,
    )
)
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
    target_id: int
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
        CHARGED_SHELLING_RANDOM_ID,
        "0fe2ec6e037d63bc1a91eb264ff999ed2d1adf856a8604e181ac9f436c1f9a1d",
        "8d8857c2dfce5ebc9121f055016074b8b131b98c624b344b8833c30860726dae",
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
        CHARGED_SHELLING_RANDOM_ID,
        "878806e7a14fe72a5cb1ff69a7d60f5db611861c3032ac10c8fb67b299458989",
        "4785364970e4080e0ddbec1853ed77f428c4dabd1a73028b8a3ff6f9072f6214",
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
        CHARGED_SHELLING_RANDOM_ID,
        "f0fa0a8665a23264e891f26ddbe4335aed7815ae8afb6733e3e35feb46d64992",
        "a8a3fd311a313491b6b4871b35668004d7195b0ad9b64b26c3024f845d4cff24",
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
    donor = bank.hirc.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_DONOR_ID
    )
    if hashlib.sha256(donor).hexdigest() != CHARGED_SHELLING_RANDOM_DONOR_SHA256:
        raise soundbank_editor.SoundBankError("charged-shelling Buster Random donor changed")
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
    with_hit_release_voice = WYR_STAKE_STRIKE_ACTION_ID in editor.object_ids
    expected_count, expected_size = (226, 13_246) if with_hit_release_voice else (222, 13_017)
    if len(editor.objects()) != expected_count or len(editor.build()) != expected_size:
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
                or sound_body != standard_voice_sound_body(
            sound_id, media_id, direct_parent_id=CHARGED_SHELLING_RANDOM_ID,
        )
            or hashlib.sha256(sound_body).hexdigest() != expected_sha256
            or editor.pitch_settings(soundbank_editor.HIRC_SOUND, sound_id)
            != soundbank_editor.HircPitchSettings(None, None)
        ):
            raise soundbank_editor.SoundBankError(
                f"charged-shelling standard voice Sound differs for {sound_id}"
            )

    random_body = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID
    )
    if (
            len(random_body) != 107
            or hashlib.sha256(random_body).hexdigest() != CHARGED_SHELLING_RANDOM_SHA256
            or editor.pitch_settings(soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID)
            != soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
    ):
        raise soundbank_editor.SoundBankError("charged-shelling Buster Random weights, parent or Pitch differ")
    positions = {item.object_id: item.index for item in editor.objects()}
    ordered = (*CHARGED_SHELLING_SOUND_IDS, CHARGED_SHELLING_RANDOM_ID)
    if any(positions[a] >= positions[b] for a, b in zip(ordered, ordered[1:])):
        raise soundbank_editor.SoundBankError("charged-shelling Sounds must serialize before Random")
    play_targets: dict[int, set[int]] = {CHARGED_SHELLING_RANDOM_ID: set()}
    if bank.external_stop_references != CHARGED_SHELLING_EXTERNAL_STOPS:
        raise soundbank_editor.SoundBankError("charged-shelling external Stop declarations differ")
    for route in CHARGED_SHELLING_ROUTES:
        stop_ids = CHARGED_SHELLING_STOP_ACTIONS[route.event_id]
        for stop_id, sound_id in zip(stop_ids, CHARGED_SHELLING_DIVINE_SOUND_IDS, strict=True):
            stop = editor.object_body(soundbank_editor.HIRC_ACTION, stop_id)
            if (
                    stop != editor.create_stop_action(stop_id, sound_id, transition_ms=50)
                    or hashlib.sha256(stop).hexdigest() != CHARGED_SHELLING_STOP_SHA256S[stop_id]
            ):
                raise soundbank_editor.SoundBankError("charged-shelling Divine Stop body differs")
        action_body = editor.object_body(soundbank_editor.HIRC_ACTION, route.action_id)
        event_body = editor.object_body(soundbank_editor.HIRC_EVENT, route.event_id)
        if (
            editor.event_actions(route.event_id)
                != (*route.expected_actions, *stop_ids, route.action_id)
            or action_body
                != editor.create_play_action(route.action_id, route.target_id, bank.bank_id)
            or hashlib.sha256(action_body).hexdigest()
            != route.action_body_sha256
            or hashlib.sha256(event_body).hexdigest() != route.event_body_sha256
            or not (
                positions[route.target_id]
                < positions[stop_ids[0]]
                < positions[stop_ids[1]]
                < positions[route.action_id]
                < positions[route.event_id]
            )
        ):
            raise soundbank_editor.SoundBankError(
                f"charged-shelling Action or Event differs for {route.label}"
            )
        play_targets[route.target_id].add(route.action_id)

    if play_targets != {
        CHARGED_SHELLING_RANDOM_ID: {
            858_972_567,
            4_053_288_866,
            3_259_504_927,
        },
    }:
        raise soundbank_editor.SoundBankError(
            "charged-shelling shared voice route differs"
        )

    divine_stops = {
        item.object_id for item in editor.objects()
        if item.object_type == soundbank_editor.HIRC_ACTION and len(item.body) >= 10
        and struct.unpack_from("<H", item.body, 4)[0] == soundbank_editor.ACTION_STOP
           and struct.unpack_from("<I", item.body, 6)[0] in CHARGED_SHELLING_DIVINE_SOUND_IDS
    }
    if divine_stops != {aid for aids in CHARGED_SHELLING_STOP_ACTIONS.values() for aid in aids}:
        raise soundbank_editor.SoundBankError("charged-shelling Divine Stop trigger set differs")
    for item in editor.objects():
        if item.object_type != soundbank_editor.HIRC_ACTION:
            continue
        body = editor.object_body(soundbank_editor.HIRC_ACTION, item.object_id)
        if (
            len(body) >= 10
            and struct.unpack_from("<H", body, 4)[0]
            == soundbank_editor.ACTION_STOP
            and struct.unpack_from("<I", body, 6)[0]
                in (*CHARGED_SHELLING_SOUND_IDS, CHARGED_SHELLING_RANDOM_ID)
        ):
            raise soundbank_editor.SoundBankError(
                "charged-shelling voice unexpectedly received a Stop Action"
            )

    if (
            set(CHARGED_SHELLING_DIVINE_MEDIA_IDS)
            & {entry.media_id for entry in bank.validate().entries}
            or set(CHARGED_SHELLING_DIVINE_SOUND_IDS) & editor.object_ids
            or CHARGED_SHELLING_DIVINE_RANDOM_ID in editor.object_ids
        or CHARGED_SHELLING_DIVINE_ACTION_ID in editor.object_ids
    ):
        raise soundbank_editor.SoundBankError(
            "charged-shelling Divine route must not remain in wp07_gun_epvsp_shell"
        )


def _guard_wyrmstake_strike_native(bank: soundbank_editor.SoundBankEditor) -> None:
    """Lock the hit release, miss release, explosion, and Stop branches."""

    hirc = bank.hirc
    for index, media, event, action, container, event_sha, action_sha in WYR_STAKE_STRIKE_NATIVE_GUARDS:
        if (
            bank.media_entry(index=index).media_id != media
            or hirc.event_actions(event) != (action,)
            or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_EVENT, event)).hexdigest()
            != event_sha
            or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_ACTION, action)).hexdigest()
            != action_sha
            or hirc.object_body(soundbank_editor.HIRC_ACTION, action)
            != hirc.create_play_action(action, container, bank.bank_id)
        ):
            raise soundbank_editor.SoundBankError(
                f"Wyrmstake native DIDX #{index} route differs"
            )
    container = hirc.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        WYR_STAKE_STRIKE_ORIGINAL_CONTAINER_ID,
    )
    original_sound = hirc.object_body(
        soundbank_editor.HIRC_SOUND, WYR_STAKE_STRIKE_ORIGINAL_SOUND_ID,
    )
    if (
        hashlib.sha256(container).hexdigest() != WYR_STAKE_STRIKE_CONTAINER_SHA256
        or hashlib.sha256(original_sound).hexdigest()
        != WYR_STAKE_STRIKE_ORIGINAL_SOUND_SHA256
        or struct.unpack_from("<I", original_sound, 9)[0]
        != WYR_STAKE_STRIKE_ORIGINAL_MEDIA_ID
        or struct.unpack_from("<I", original_sound, 25)[0]
        != WYR_STAKE_STRIKE_ORIGINAL_CONTAINER_ID
    ):
        raise soundbank_editor.SoundBankError("Wyrmstake native hit-release Sound differs")
    for kind, ident, parent in WYR_STAKE_STRIKE_NATIVE_PARENT_CHAIN:
        body = hirc.object_body(kind, ident)
        if struct.unpack_from("<I", body, 11)[0] != parent:
            raise soundbank_editor.SoundBankError("Wyrmstake hit-release parent chain differs")
    stop_targets = _event_referenced_stop_targets(hirc)
    if not WYR_STAKE_STRIKE_NATIVE_STOP_TARGETS.issubset(stop_targets):
        raise soundbank_editor.SoundBankError("Wyrmstake native Stop audit differs")
    native_chain = {
        WYR_STAKE_STRIKE_ORIGINAL_SOUND_ID,
        *(ident for _, ident, _ in WYR_STAKE_STRIKE_NATIVE_PARENT_CHAIN),
    }
    if native_chain & stop_targets:
        raise soundbank_editor.SoundBankError("Wyrmstake native Stop reaches hit release")


def validate_wyrmstake_hit_release_hirc(
    bank: soundbank_editor.SoundBankEditor,
) -> None:
    """Require one equal-weight random voice on the native hit-release Event."""

    hirc = bank.hirc
    for index, media, event, action, container, event_sha, action_sha in WYR_STAKE_STRIKE_NATIVE_GUARDS[1:]:
        if (
            bank.media_entry(index=index).media_id != media
            or hirc.event_actions(event) != (action,)
            or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_EVENT, event)).hexdigest()
            != event_sha
            or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_ACTION, action)).hexdigest()
            != action_sha
            or hirc.object_body(soundbank_editor.HIRC_ACTION, action)
            != hirc.create_play_action(action, container, bank.bank_id)
        ):
            raise soundbank_editor.SoundBankError("Wyrmstake miss release or explosion route changed")
    original_container = hirc.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER,
        WYR_STAKE_STRIKE_ORIGINAL_CONTAINER_ID,
    )
    original_sound = hirc.object_body(
        soundbank_editor.HIRC_SOUND, WYR_STAKE_STRIKE_ORIGINAL_SOUND_ID,
    )
    original_action = hirc.object_body(
        soundbank_editor.HIRC_ACTION, WYR_STAKE_STRIKE_ORIGINAL_ACTION_ID
    )
    action = hirc.object_body(soundbank_editor.HIRC_ACTION, WYR_STAKE_STRIKE_ACTION_ID)
    event = hirc.object_body(soundbank_editor.HIRC_EVENT, WYR_STAKE_STRIKE_EVENT_ID)
    if (
            hashlib.sha256(original_container).hexdigest()
        != WYR_STAKE_STRIKE_CONTAINER_SHA256
        or hashlib.sha256(original_sound).hexdigest()
        != WYR_STAKE_STRIKE_ORIGINAL_SOUND_SHA256
        or original_action != hirc.create_play_action(
            WYR_STAKE_STRIKE_ORIGINAL_ACTION_ID,
            WYR_STAKE_STRIKE_ORIGINAL_CONTAINER_ID, bank.bank_id,
        )
        or hashlib.sha256(original_action).hexdigest()
        != WYR_STAKE_STRIKE_NATIVE_GUARDS[0][6]
        or action != hirc.create_play_action(
        WYR_STAKE_STRIKE_ACTION_ID, WYR_STAKE_HIT_RANDOM_ID, bank.bank_id
        )
        or hashlib.sha256(action).hexdigest() != WYR_STAKE_STRIKE_ACTION_SHA256
        or hirc.event_actions(WYR_STAKE_STRIKE_EVENT_ID)
        != (WYR_STAKE_STRIKE_ORIGINAL_ACTION_ID, WYR_STAKE_STRIKE_ACTION_ID)
        or hashlib.sha256(event).hexdigest() != WYR_STAKE_STRIKE_EVENT_SHA256
    ):
        raise soundbank_editor.SoundBankError("Wyrmstake hit-release Event route differs")
    for index, media, sound_id, body_sha in (
            (52, WYR_STAKE_STRIKE_MEDIA_ID, WYR_STAKE_STRIKE_SOUND_ID,
             WYR_STAKE_STRIKE_SOUND_SHA256),
            (53, WYR_STAKE_ACS_STANDBY_MEDIA_ID, WYR_STAKE_ACS_STANDBY_SOUND_ID,
             WYR_STAKE_ACS_STANDBY_SOUND_SHA256),
    ):
        sound = hirc.object_body(soundbank_editor.HIRC_SOUND, sound_id)
        if (
                bank.media_entry(index=index).media_id != media
                or sound != standard_voice_sound_body(
            sound_id, media, direct_parent_id=WYR_STAKE_HIT_RANDOM_ID
        )
                or hashlib.sha256(sound).hexdigest() != body_sha
                or hirc.pitch_settings(soundbank_editor.HIRC_SOUND, sound_id)
                != soundbank_editor.HircPitchSettings(None, None)
        ):
            raise soundbank_editor.SoundBankError(
                f"Wyrmstake hit-release Sound {sound_id} differs"
            )
    random_body = hirc.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WYR_STAKE_HIT_RANDOM_ID
    )
    if (
            len(random_body) != 95
            or hashlib.sha256(random_body).hexdigest() != WYR_STAKE_HIT_RANDOM_SHA256
            or hirc.pitch_settings(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WYR_STAKE_HIT_RANDOM_ID
    ) != WYR_STAKE_HIT_PITCH
    ):
        raise soundbank_editor.SoundBankError("Wyrmstake hit-release Random differs")
    objects = hirc.objects()
    positions = {item.object_id: item.index for item in objects}
    if not (
            max(positions[sound_id] for sound_id, _ in WYR_STAKE_HIT_PLAYLIST)
            < positions[WYR_STAKE_HIT_RANDOM_ID]
        < positions[WYR_STAKE_STRIKE_ACTION_ID]
        < positions[WYR_STAKE_STRIKE_EVENT_ID]
    ):
        raise soundbank_editor.SoundBankError("Wyrmstake hit-release Random order differs")
    owners = tuple(
        item.object_id for item in objects
        if item.object_type == soundbank_editor.HIRC_EVENT
        and WYR_STAKE_STRIKE_ACTION_ID in hirc.event_actions(item.object_id)
    )
    if owners != (WYR_STAKE_STRIKE_EVENT_ID,):
        raise soundbank_editor.SoundBankError("Wyrmstake hit-release Action owner differs")


def _apply_wyrmstake_hit_release(bank: soundbank_editor.SoundBankEditor) -> None:
    _guard_wyrmstake_strike_native(bank)
    hirc = bank.hirc
    for sound_id, media_id in (
            (WYR_STAKE_STRIKE_SOUND_ID, WYR_STAKE_STRIKE_MEDIA_ID),
            (WYR_STAKE_ACS_STANDBY_SOUND_ID, WYR_STAKE_ACS_STANDBY_MEDIA_ID),
    ):
        bank.media_entry(media_id=media_id)
        insert_standard_voice_sound(
            hirc, sound_id, media_id,
            direct_parent_id=WYR_STAKE_HIT_RANDOM_ID,
            label=f"insert Wyrmstake hit-release Sound {sound_id}",
        )
    donor = hirc.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WYR_STAKE_HIT_RANDOM_DONOR_ID
    )
    if hashlib.sha256(donor).hexdigest() != WYR_STAKE_HIT_RANDOM_DONOR_SHA256:
        raise soundbank_editor.SoundBankError("Wyrmstake hit-release Random donor changed")
    hirc.clone_random_sequence_container(
        WYR_STAKE_HIT_RANDOM_DONOR_ID, WYR_STAKE_HIT_RANDOM_ID,
        WYR_STAKE_HIT_PLAYLIST,
        expected_playlist=((46_149_961, 50_000),),
        expected_avoid_repeat_count=1,
        avoid_repeat_count=0,
        label="clone equal-weight Wyrmstake hit-release Random",
    )
    hirc.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WYR_STAKE_HIT_RANDOM_ID,
        0x0B, 717_111_903, STANDARD_VOICE_PARENT_ID,
        label="parent Wyrmstake hit-release Random to voice mixer",
    )
    hirc.set_pitch(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WYR_STAKE_HIT_RANDOM_ID,
        expected=WYR_STAKE_HIT_PITCH,
        random_range_cents=WYR_STAKE_HIT_PITCH.random_range_cents,
        label="guard Wyrmstake hit-release Random Pitch",
    )
    action = hirc.create_play_action(
        WYR_STAKE_STRIKE_ACTION_ID, WYR_STAKE_HIT_RANDOM_ID, bank.bank_id
    )
    hirc.insert_object(
        soundbank_editor.HIRC_ACTION, WYR_STAKE_STRIKE_ACTION_ID, action[4:],
        before=(soundbank_editor.HIRC_EVENT, WYR_STAKE_STRIKE_EVENT_ID),
        label="add Wyrmstake hit-release Random Play Action",
    )
    hirc.append_event_action(
        WYR_STAKE_STRIKE_EVENT_ID, WYR_STAKE_STRIKE_ACTION_ID,
        expected_actions=(WYR_STAKE_STRIKE_ORIGINAL_ACTION_ID,),
        label="append Random voice to Wyrmstake hit-release Event",
    )
    validate_wyrmstake_hit_release_hirc(bank)


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
            direct_parent_id=CHARGED_SHELLING_RANDOM_ID,
            label=f"insert charged-shelling standard voice Sound {sound_id}",
        )
    editor.clone_random_sequence_container(
        CHARGED_SHELLING_RANDOM_DONOR_ID, CHARGED_SHELLING_RANDOM_ID, CHARGED_SHELLING_PLAYLIST,
        expected_playlist=((46_149_961, 50_000),), expected_avoid_repeat_count=1,
        avoid_repeat_count=0, label="clone uniform charged-shelling Buster Random",
    )
    editor.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID, 0x0B,
        717_111_903, STANDARD_VOICE_PARENT_ID, label="parent Buster Random to voice mixer",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID,
        expected=soundbank_editor.HircPitchSettings(None, (-50.0, 50.0)),
        random_range_cents=(-50.0, 50.0),
    )
    for route in CHARGED_SHELLING_ROUTES:
        actions = route.expected_actions
        for stop_id, sound_id in zip(
                CHARGED_SHELLING_STOP_ACTIONS[route.event_id], CHARGED_SHELLING_DIVINE_SOUND_IDS, strict=True,
        ):
            stop = editor.create_stop_action(stop_id, sound_id, transition_ms=50)
            editor.insert_object(
                soundbank_editor.HIRC_ACTION, stop_id, stop[4:],
                before=(soundbank_editor.HIRC_EVENT, route.event_id),
                label=f"add independent Divine Stop for {route.label}",
            )
            editor.append_event_action(route.event_id, stop_id, expected_actions=actions)
            actions = (*actions, stop_id)
        action = editor.create_play_action(
            route.action_id, route.target_id, bank.bank_id
        )
        editor.insert_object(
            soundbank_editor.HIRC_ACTION,
            route.action_id,
            action[4:],
            before=(soundbank_editor.HIRC_EVENT, route.event_id),
            label=f"add charged-shelling Play Action for {route.label}",
        )
        editor.append_event_action(route.event_id, route.action_id, expected_actions=actions)
    validate_charged_shelling_hirc(bank)


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Apply the four reviewed designs in deterministic serialization order."""

    if bank.hirc.event_actions(WYVERN_LEFT_EVENT_ID) != (
        WYVERN_LEFT_ORIGINAL_ACTION_ID,
    ):
        raise soundbank_editor.SoundBankError(
            "Wyvern left Event differs from the byte-exact no-voice path guard"
        )
    _guard_charged_shelling_original(bank)
    _apply_full_burst(bank)
    apply_wyverns_fire(bank)
    _apply_charged_shelling(bank)
    _apply_wyrmstake_hit_release(bank)


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=(
        (43, 242768048),
        (44, 322318543),
        (45, 3332910283),
        (46, 2217266443),
        (47, 954495929),
        (48, 2170495128),
        (49, 2062876979),
        (50, 1793121649),
        (51, 570980126),
        (52, 949600199),
        (53, 938668400),
        (54, 2014220448),
        (55, 3735305437),
        (56, 941385580),
        (57, 3696251564),
        (58, 631532425),
        (59, 2785082779),
    ),
    hirc_changed_bytes=42,
    added_hirc_objects=(
        (2, 960803121),
        (2, 479969098),
        (2, 2544331946),
        (2, 4251385954),
        (5, 853759195),
        (3, 3386055930),
        (3, 4199321359),
        (3, 4100049135),
        (3, 4272498343),
        (3, 3047212046),
        (2, 4149261730),
        (2, 36215958),
        (2, 2472459210),
        (2, 2849114849),
        (2, 1620588112),
        (2, 1229173909),
        (2, 3984040149),
        (2, 3346634804),
        (5, 3610379736),
        (5, 3391377780),
        (5, 362366644),
        (3, 3388979775),
        (3, 4011774951),
        (3, 254514827),
        (3, 1866468495),
        (4, 281273126),
        (3, 2987046856),
        (3, 3645807405),
        (2, 3489806140),
        (2, 3928375835),
        (2, 690215586),
        (5, 2510752860),
        (3, 1426818832),
        (3, 515837897),
        (3, 858972567),
        (3, 1225287532),
        (3, 1287808358),
        (3, 4053288866),
        (3, 728690884),
        (3, 1267644869),
        (3, 3259504927),
        (2, 38895430),
        (2, 1727570929),
        (5, 2393951905),
        (3, 1821689211),
    ),
    resized_hirc_objects=(
        (4, 461444626, 12, 20),
        (4, 680296805, 12, 16),
        (4, 1124197610, 12, 16),
        (4, 1581859410, 12, 16),
        (4, 1765608260, 12, 16),
        (4, 1962814816, 12, 24),
        (4, 2187565051, 12, 24),
        (4, 2727643337, 12, 16),
        (4, 2727643338, 12, 16),
        (4, 3325567640, 12, 24),
        (4, 3655102100, 12, 16),
    ),
    hirc_size_delta=2156,
)


PLAN = SoundBankBuildPlan(
    name="wp07_gun_epvsp_shell",
    design_ids=(
        "wp07_gun_epvsp_shell.full_burst",
        "wp07_gun_epvsp_shell.wyverns_fire",
        "wp07_gun_epvsp_shell.charged_shelling",
        "wp07_gun_epvsp_shell.wyrmstake_cannon",
    ),
    source="original/nbnk/wp07_gun_epvsp_shell.nbnk",
    target="sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk",
    expected_source_sha256=(
        "41bb0136e89e8434d716caed9c37b399e44cd0cb057f3fa9ab706437696782a1"
    ),
    expected_bank_id=3_273_965_928,
    reference_inputs=STANDARD_VOICE_REFERENCE_INPUTS,
    external_stop_references=CHARGED_SHELLING_EXTERNAL_STOPS,
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
            "nanoha_buster_01(battle_of_aces.attack_04.2).wav",
            wem_channels=1,
        ),
        MediaAddition(
            51,
            CHARGED_SHELLING_MEDIA_IDS[1],
            "audio/wp07_gun_epvsp_shell/charged_shelling/"
            "nanoha_buster_02(gears_of_destiny.attack_voice.attack_04.2).wav",
            wem_channels=1,
        ),
        MediaAddition(
            52,
            WYR_STAKE_STRIKE_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/wyrmstake_cannon/"
            "raising_heart_unit_set_01(movie_detonation.raising_heart.unit_set.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            53,
            WYR_STAKE_ACS_STANDBY_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/wyrmstake_cannon/"
            "raising_heart_acs_standby_01(movie_2nd_as.raising_heart.acs_standby.1).wav",
            wem_channels=1,
        ),
        *(MediaAddition(index, media, f"audio/wp07_gun_epvsp_shell/wyverns_fire/{name}", wem_channels=1)
          for (index, media, _, _), name in zip(WYVERN_CLIPS[3:], EXTRA_FILENAMES, strict=True)),
        MediaAddition(
            59,
            CHARGED_SHELLING_MEDIA_IDS[2],
            "audio/wp07_gun_epvsp_shell/charged_shelling/"
            "nanoha_buster_03(movie_reflection.nanoha.excellion_buster.1).wav",
            wem_channels=1,
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
