"""Build shared gunlance voice routes, including charged-shelling start."""

from __future__ import annotations

import hashlib
import struct

from tools import soundbank_editor

from . import clutch_weapon_attack_routes as clutch
from . import mounted_finisher_routes as mounted
from .base import MediaAddition, SoundBankBuildPlan, run_single_cli
from .voice_standard import (
    STANDARD_VOICE_PARENT_ID,
    STANDARD_VOICE_REFERENCE_INPUTS,
    insert_standard_voice_sound,
    standard_voice_sound_body,
)

WYR_STAKE_MEDIA_IDS = (1_484_632_890, 3_113_081_405)
WYR_STAKE_SOUND_IDS = (1_847_466_623, 573_906_608)
WYR_STAKE_EVENT_IDS = (1_289_400_830, 1_358_515_313)
WYR_STAKE_ACTION_IDS = (2_004_285_408, 551_409_861)
WYR_STAKE_PITCH = soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
WYR_STAKE_SOUND_SHA256S = (
    "56f69bfb7ca7002283351feba3c2beb81e6f19dabbdda69c0cc78078bcbd0a70",
    "564dfecdf7e2054a3e86eea6f2768a8a31da359cb6c912d9c2bebd8c3e613fb6",
)
WYR_STAKE_MUTE_EMPTY_EVENT_ID = 3_938_800_881
WYR_STAKE_MUTE_PLAY_ACTION_ID = 1_604_422_970
WYR_STAKE_MUTE_ROUTE_EVENT_ID = 2_846_173_097
WYR_STAKE_MUTE_BODY_GUARDS = (
    (soundbank_editor.HIRC_EVENT, WYR_STAKE_MUTE_EMPTY_EVENT_ID,
     "21525a5823a2687ce13e25a0e09d58d97909bbf80da668325e915651bfcfc040"),
    (soundbank_editor.HIRC_ACTION, WYR_STAKE_MUTE_PLAY_ACTION_ID,
     "7ef8b289c598aab00f84deb221ff22cd47921220296f54848e173f257a172bb9"),
    (soundbank_editor.HIRC_EVENT, WYR_STAKE_MUTE_ROUTE_EVENT_ID,
     "4685644e360014eb448b4937e8c353f5a9359e0d50dea3bb0e649baace7cca04"),
)


WYR_STAKE_ORIGINAL_ROUTES = (
    (2_798_914_977, 193_548_488, 564_339_955,
     "92c0853b4112e8fe3e1a476d2225950c728ea8441e5014ee6d4083b6dbc89a80",
     "bc6d45828f7dba59fa6068d9aaf4420cb961a3765ee868c600384da0f3740e6b"),
    (2_279_772_715, 479_984_650, 68_493_596,
     "0d24089543173b9f1f9a9200a11ab8e05169362751754b03483004a6d11e207c",
     "f4c3e1d1071787fd47d9e83cf385309fac8b92f397164d50e4c83022487fde63"),
)


def validate_wyrmstake_voice_hirc(bank: soundbank_editor.SoundBankEditor) -> None:
    """Guard original common routes and the two independent custom voices."""

    hirc = bank.hirc
    for event, action, target, event_sha, action_sha in WYR_STAKE_ORIGINAL_ROUTES:
        if (
                hirc.event_actions(event) != (action,)
                or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_EVENT, event)).hexdigest() != event_sha
                or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_ACTION, action)).hexdigest() != action_sha
                or struct.unpack_from("<I", hirc.object_body(soundbank_editor.HIRC_ACTION, action), 6)[0] != target
        ):
            raise soundbank_editor.SoundBankError("original Wyrmstake common Event changed")
    positions = {item.object_id: item.index for item in hirc.objects()}
    for index, (media, sound, event, action, sound_sha256) in enumerate(zip(
            WYR_STAKE_MEDIA_IDS, WYR_STAKE_SOUND_IDS,
            WYR_STAKE_EVENT_IDS, WYR_STAKE_ACTION_IDS,
            WYR_STAKE_SOUND_SHA256S, strict=True
    ), 47):
        sound_body = hirc.object_body(soundbank_editor.HIRC_SOUND, sound)
        if (
                bank.media_entry(index=index).media_id != media
                or len(sound_body) != 55
                or hashlib.sha256(sound_body).hexdigest() != sound_sha256
                or hirc.pitch_settings(soundbank_editor.HIRC_SOUND, sound)
                != WYR_STAKE_PITCH
                or hirc.event_actions(event) != (action,)
                or hirc.object_body(soundbank_editor.HIRC_ACTION, action)
                != hirc.create_play_action(action, sound, bank.bank_id)
                or not positions[sound] < positions[action] < positions[event]
        ):
            raise soundbank_editor.SoundBankError("Wyrmstake custom voice route differs")


def _apply_wyrmstake_voice(bank: soundbank_editor.SoundBankEditor) -> None:
    hirc = bank.hirc
    for event, action, target, event_sha, action_sha in WYR_STAKE_ORIGINAL_ROUTES:
        if (
                hirc.event_actions(event) != (action,)
                or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_EVENT, event)).hexdigest() != event_sha
                or hashlib.sha256(hirc.object_body(soundbank_editor.HIRC_ACTION, action)).hexdigest() != action_sha
                or struct.unpack_from("<I", hirc.object_body(soundbank_editor.HIRC_ACTION, action), 6)[0] != target
        ):
            raise soundbank_editor.SoundBankError("original Wyrmstake common donor differs")
    for media, sound, event, action in zip(
            WYR_STAKE_MEDIA_IDS, WYR_STAKE_SOUND_IDS,
            WYR_STAKE_EVENT_IDS, WYR_STAKE_ACTION_IDS, strict=True
    ):
        insert_standard_voice_sound(hirc, sound, media,
                                    label="insert Wyrmstake canonical voice Sound")
        hirc.set_pitch(
            soundbank_editor.HIRC_SOUND, sound,
            expected=soundbank_editor.HircPitchSettings(None, None),
            random_range_cents=WYR_STAKE_PITCH.random_range_cents,
            label="set Wyrmstake custom voice random Pitch",
        )
        hirc.insert_object(soundbank_editor.HIRC_ACTION, action,
                           hirc.create_play_action(action, sound, bank.bank_id)[4:],
                           label="insert Wyrmstake voice Play Action")
        hirc.insert_object(soundbank_editor.HIRC_EVENT, event,
                           struct.pack("<II", 1, action),
                           label="insert Wyrmstake voice Event")
    validate_wyrmstake_voice_hirc(bank)


def validate_wyrmstake_original_voice_mute_hirc(
        bank: soundbank_editor.SoundBankEditor,
) -> None:
    """Require the media-free, single-owner Wyrmstake voice-mute route."""

    hirc = bank.hirc
    for kind, ident, digest in WYR_STAKE_MUTE_BODY_GUARDS:
        if hashlib.sha256(hirc.object_body(kind, ident)).hexdigest() != digest:
            raise soundbank_editor.SoundBankError("Wyrmstake mute HIRC body differs")
    if (
            hirc.event_actions(WYR_STAKE_MUTE_EMPTY_EVENT_ID) != ()
            or hirc.event_actions(WYR_STAKE_MUTE_ROUTE_EVENT_ID)
            != (WYR_STAKE_MUTE_PLAY_ACTION_ID,)
            or hirc.object_body(soundbank_editor.HIRC_ACTION, WYR_STAKE_MUTE_PLAY_ACTION_ID)
            != hirc.create_play_event_action(
        WYR_STAKE_MUTE_PLAY_ACTION_ID, WYR_STAKE_MUTE_EMPTY_EVENT_ID
    )
    ):
        raise soundbank_editor.SoundBankError("Wyrmstake mute Event chain differs")
    objects = hirc.objects()
    positions = {item.object_id: item.index for item in objects}
    if not (
            positions[WYR_STAKE_MUTE_EMPTY_EVENT_ID]
            < positions[WYR_STAKE_MUTE_PLAY_ACTION_ID]
            < positions[WYR_STAKE_MUTE_ROUTE_EVENT_ID]
    ):
        raise soundbank_editor.SoundBankError("Wyrmstake mute HIRC order differs")
    owners = tuple(
        item.object_id for item in objects
        if item.object_type == soundbank_editor.HIRC_EVENT
        and WYR_STAKE_MUTE_PLAY_ACTION_ID in hirc.event_actions(item.object_id)
    )
    if owners != (WYR_STAKE_MUTE_ROUTE_EVENT_ID,):
        raise soundbank_editor.SoundBankError("Wyrmstake mute Action owner differs")


def _apply_wyrmstake_original_voice_mute(
        bank: soundbank_editor.SoundBankEditor,
) -> None:
    hirc = bank.hirc
    previous = tuple((obj.object_type, obj.object_id, obj.body) for obj in hirc.objects())
    hirc.insert_object(
        soundbank_editor.HIRC_EVENT, WYR_STAKE_MUTE_EMPTY_EVENT_ID,
        struct.pack("<I", 0), label="insert Wyrmstake zero-Action Event",
    )
    hirc.insert_object(
        soundbank_editor.HIRC_ACTION, WYR_STAKE_MUTE_PLAY_ACTION_ID,
        hirc.create_play_event_action(
            WYR_STAKE_MUTE_PLAY_ACTION_ID, WYR_STAKE_MUTE_EMPTY_EVENT_ID
        )[4:], after=(soundbank_editor.HIRC_EVENT, WYR_STAKE_MUTE_EMPTY_EVENT_ID),
        label="insert Wyrmstake voice-mute PlayEvent Action",
    )
    hirc.insert_object(
        soundbank_editor.HIRC_EVENT, WYR_STAKE_MUTE_ROUTE_EVENT_ID,
        struct.pack("<II", 1, WYR_STAKE_MUTE_PLAY_ACTION_ID),
        after=(soundbank_editor.HIRC_ACTION, WYR_STAKE_MUTE_PLAY_ACTION_ID),
        label="insert Wyrmstake voice-mute route Event",
    )
    added = {ident for _, ident, _ in WYR_STAKE_MUTE_BODY_GUARDS}
    if tuple((obj.object_type, obj.object_id, obj.body) for obj in hirc.objects()
             if obj.object_id not in added) != previous:
        raise soundbank_editor.SoundBankError("Wyrmstake mute changed an existing HIRC object")
    validate_wyrmstake_original_voice_mute_hirc(bank)


VOICE_MEDIA_ID = 863_865_614
VOICE_SOUND_ID = 700_212_875
ORIGINAL_ROUTE_ACTION_ID = 267_255_962
VOICE_ACTION_ID = 708_529_406
VOICE_EVENT_ID = 3_176_129_810

STATIONARY_MEDIA_IDS = (
    VOICE_MEDIA_ID, 3_899_958_096, 1_917_220_401, 2_922_118_034, 3_798_249_131, 3_222_869_860,
)
STATIONARY_SOUND_IDS = (
    VOICE_SOUND_ID, 776_774_097, 3_655_378_684, 3_336_805_367, 1_609_904_242, 3_412_709_805,
)
STATIONARY_MEDIA_INDICES = (34, 39, 40, 41, 42, 43)
STATIONARY_RANDOM_ID = 847_783_544
STATIONARY_PLAYLIST = tuple((sound_id, 50_000) for sound_id in STATIONARY_SOUND_IDS)
STATIONARY_RANDOM_DONOR_ID = 522_283_251
STATIONARY_RANDOM_DONOR_SHA256 = (
    "e47758895339f8a1e74a65b122921135b97edf7ee01ad69f5d2a388f66e1955d"
)
STATIONARY_SOUND_DONOR_SHA256 = (
    "708699420d9237c644f13919834d5f4374d67e29a94762dc1bc0b0b98e133186"
)
STATIONARY_RANDOM_SHA256 = (
    "db3a22c71a5c29ad75d077c95b70a2b7f65f98b7c3940b4ba4c8fab2707a6644"
)

ORIGINAL_EVENT_ID = 3_567_942_167
ORIGINAL_EVENT_ACTION_ID = 1_061_269_777
DONOR_SOUND_ID = 233_981_936
DONOR_MEDIA_ID = 867_938_822
POSITIONING_VECTOR_OFFSET = 0x2A

OVERHEAD_VOICE_MEDIA_ID = 1_280_643_898
OVERHEAD_VOICE_SOUND_ID = 1_643_477_631
OVERHEAD_MEDIA_IDS = (OVERHEAD_VOICE_MEDIA_ID, 1_779_645_041)
OVERHEAD_SOUND_IDS = (OVERHEAD_VOICE_SOUND_ID, 3_476_329_532)
OVERHEAD_MEDIA_INDICES = (35, 44)
OVERHEAD_RANDOM_ID = 1_487_507_844
OVERHEAD_PLAYLIST = tuple((sound_id, 50_000) for sound_id in OVERHEAD_SOUND_IDS)
OVERHEAD_RANDOM_DONOR_ID = 570_218_704
OVERHEAD_RANDOM_DONOR_SHA256 = (
    "be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427"
)
OVERHEAD_RANDOM_SHA256 = (
    "14d8a2b8bc85006842ce55cc6be9a29941d92baee5047b3ce049baedabada0f8"
)
OBSOLETE_OVERHEAD_ORIGINAL_ROUTE_ACTION_ID = 2_557_911_997
OVERHEAD_VOICE_ACTION_ID = 3_750_542_142
OVERHEAD_SILENT_PRIME_ACTION_ID = 2_176_868_439
OVERHEAD_SILENT_EVENT_ID = 971_912_882
OVERHEAD_VOICE_EVENT_ID = 2_866_569_635

OVERHEAD_ORIGINAL_EVENT_ID = 1_129_041_389
OVERHEAD_ORIGINAL_EVENT_ACTION_ID = 948_030_399
OVERHEAD_ORIGINAL_CONTAINER_ID = 968_655_714
OVERHEAD_DONOR_SOUND_ID = 959_908_164
OVERHEAD_DONOR_MEDIA_ID = 554_875_117
OVERHEAD_DONOR_MEDIA_INDEX = 13
OVERHEAD_SOUND_PARENT_OFFSET = 0x19
OVERHEAD_SOUND_OVERRIDE_BUS_OFFSET = 0x15
OVERHEAD_SOUND_AUX_OFFSET = 0x2C
OVERHEAD_SOUND_AUX_IDS = (3_015_692_424, 0, 0, 0)

RELOAD_VOICE_MEDIA_ID = 1_284_288_484
RELOAD_VOICE_SOUND_ID = 1_474_128_429
RELOAD_VOICE_ACTION_ID = 3_418_611_510
RELOAD_VOICE_PITCH = soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
RELOAD_VOICE_SOUND_SHA256 = (
    "49b0c3c0cd9a4532abf62b92e701f30cb3f6418d5385c98b1e50ca45d2665c21"
)

RELOAD_EVENT_ID = 3_476_627_122
RELOAD_ORIGINAL_ACTION_ID = 126_049_847
RELOAD_CONTAINER_ID = 411_055_943
RELOAD_DONOR_SOUND_ID = 176_748_589
RELOAD_DONOR_MEDIA_ID = 86_782_159
RELOAD_DONOR_MEDIA_INDEX = 1
RELOAD_SOUND_PARENT_OFFSET = 0x19
RELOAD_SOUND_OVERRIDE_BUS_OFFSET = 0x15
RELOAD_SOUND_AUX_OFFSET = 0x2C
RELOAD_SOUND_AUX_IDS = (3_015_692_424, 0, 0, 0)
RELOAD_CONTAINER_AVOID_REPEAT_OFFSET = 0x40
RELOAD_CONTAINER_MODE_OFFSET = 0x44
RELOAD_CONTAINER_PLAYLIST_OFFSET = 0x46
RELOAD_CONTAINER_PLAYLIST = struct.pack(
    "<IIHII",
    1,
    RELOAD_DONOR_SOUND_ID,
    1,
    RELOAD_DONOR_SOUND_ID,
    50_000,
)

WIDE_SWEEP_MEDIA_IDS = (1_484_106_982, 2_274_559_001)
WIDE_SWEEP_SOUND_IDS = (102_041_635, 3_822_519_236)
WIDE_SWEEP_RANDOM_ID = 3_645_186_695
WIDE_SWEEP_PLAYLIST = ((WIDE_SWEEP_SOUND_IDS[0], 70_000), (WIDE_SWEEP_SOUND_IDS[1], 30_000))
WIDE_SWEEP_ORIGINAL_ROUTE_ACTION_ID = 2_768_755_612
WIDE_SWEEP_VOICE_ACTION_ID = 3_181_937_101
WIDE_SWEEP_EVENT_ID = 4_096_779_774

WIDE_SWEEP_ORIGINAL_EVENT_ID = 2_467_230_206
WIDE_SWEEP_ORIGINAL_ACTION_ID = 281_299_658
WIDE_SWEEP_ORIGINAL_CONTAINER_ID = 5_732_403
WIDE_SWEEP_ORIGINAL_SOUND_ID = 402_899_610
WIDE_SWEEP_ORIGINAL_MEDIA_ID = 367_086_010
WIDE_SWEEP_RANDOM_DONOR_ID = 570_218_704
WIDE_SWEEP_RANDOM_DONOR_SHA256 = (
    "be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427"
)
WIDE_SWEEP_RANDOM_SHA256 = (
    "369e0b6264741e600b9e87a2a05034365fcaafa6ae82a19ed178d66357fc0efd"
)
WIDE_SWEEP_UNUSED_EVENT_IDS = (1_359_210_849, 2_281_439_929)

CHARGED_SHELLING_DIVINE_MEDIA_ID = 370_615_719
FIRING_VOICE_EVENT_ID = 2_825_008_231
FIRING_SILENT_ACTION_ID = 3_500_432_807
FIRING_SILENT_EVENT_ID = 3_344_928_599
FIRING_SILENT_BODY_GUARDS = (
    (soundbank_editor.HIRC_ACTION, FIRING_SILENT_ACTION_ID,
     "373a8565c017faed8e9dbe7e0d0bc985c74f7fff140e96be452760fb387de9ed"),
    (soundbank_editor.HIRC_EVENT, FIRING_SILENT_EVENT_ID,
     "b690ca747f5c2f83d75a560d068fbd86abaa6f20ce8a6eeacb4d669ce978277c"),
    (soundbank_editor.HIRC_EVENT, FIRING_VOICE_EVENT_ID,
     "4d0ae624d720e9762e04c1e6bd78afb8045cd44b78d323fe32db3af2563ac1c5"),
)
CHARGED_SHELLING_DIVINE_SOUND_ID = 3_754_878_246
CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID = 1_005_770_249
CHARGED_SHELLING_DIVINE_ACTION_ID = 583_060_699
CHARGED_SHELLING_EVENT_ID = 3_452_820_647
CHARGED_SHELLING_DIVINE_MEDIA_INDEX = 45
CHARGED_SHELLING_DIVINE_MEDIA_IDS = (CHARGED_SHELLING_DIVINE_MEDIA_ID, 3_246_372_848)
CHARGED_SHELLING_DIVINE_SOUND_IDS = (CHARGED_SHELLING_DIVINE_SOUND_ID, 4_035_275_377)
CHARGED_SHELLING_DIVINE_MEDIA_INDICES = (45, 46)
CHARGED_SHELLING_RANDOM_ID = 1_153_640_130
CHARGED_SHELLING_RANDOM_DONOR_ID = 570_218_704
CHARGED_SHELLING_RANDOM_DONOR_SHA256 = (
    "be0beffcec2f1a026d5bea182c34c2fbfcb2a129b1b4efa8c33146bfeb046427"
)
CHARGED_SHELLING_RANDOM_SHA256 = (
    "40b6d65e0aa7f692932836ead31d07e91a63606975dd12d0be46389a4ca8a426"
)
CHARGED_SHELLING_PLAYLIST = tuple((sid, 50_000) for sid in CHARGED_SHELLING_DIVINE_SOUND_IDS)
CHARGED_SHELLING_STOP_BUSTER_ACTION_ID = 1_603_135_794
CHARGED_SHELLING_BUSTER_SOUND_ID = 3_489_806_140
CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS = (CHARGED_SHELLING_STOP_BUSTER_ACTION_ID, 85_406_655, 2_076_396_906)
CHARGED_SHELLING_BUSTER_SOUND_IDS = (CHARGED_SHELLING_BUSTER_SOUND_ID, 3_928_375_835, 690_215_586)
CHARGED_SHELLING_STOP_BUSTER_SHA256S = (
    "f33f2c36a8e9ec2278fe3c85950abe4b8163f58a1770404fed9e531a2b4ebb65",
    "a3e37d407b2de99b7f29088dc93127b5c02a5423a8c702196df2315edfa7b13d",
    "546bee5372b864ea27999bb884e4aa030466b7fda336e9629d9a2b89015bbacb",
)
CHARGED_SHELLING_EXTERNAL_STOPS = tuple(
    soundbank_editor.ExternalStopReference(
        action_id, 3_273_965_928, sound_id, body_sha256,
    )
    for action_id, sound_id, body_sha256 in zip(
        CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS,
        CHARGED_SHELLING_BUSTER_SOUND_IDS,
        (
            "bbc603bac06e30ea54aa58de3b749e1d413c8275c2834a931e015b8835c7e06d",
            "2e5a7e3eb467114ad41a2a742e5204f51a5dcf9bf45bc0a011f8c1a3cd8663a4",
            "8851587d5cec37e5055865facfd818745aa344bf30ca4a001f5caea89b87bcf0",
        ),
        strict=True,
    )
)
CHARGED_SHELLING_ORIGINAL_EVENT_SHA256 = (
    "cdf654b3ef9e93d51971da97cc9479fcfd85ad8baaa6923f1a94bb6784844f15"
)
CHARGED_SHELLING_ORIGINAL_ACTION_SHA256 = (
    "6c8f6ba1362064c06db17ed2248d1f9f288a3f0459caba8c77131d8b487c810a"
)
CHARGED_SHELLING_DIVINE_SOUND_SHA256S = (
    "251b8841b03f2489535afa09e60afae689137fbc3249a0a60bab8cd7481e372d",
    "047453c18d735292b6965b2dfb4e83b79803bf9311836232b60bad6a9da27b87",
)
CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_SHA256 = (
    "c87314f918eb3d617c61c98cf8842b0132f85e688d3ad0e8d10da6d1d41bafca"
)
CHARGED_SHELLING_DIVINE_ACTION_SHA256 = (
    "ac01f6c3c01f4b9870cf14af9c1f6614cc78fa2d2d1f01dcc16bed071da1be38"
)
CHARGED_SHELLING_EVENT_SHA256 = (
    "8e966f8f23233c1839a1f9a464e3e2a26eda29b3c457e30ddfbe7935ea3f5582"
)
CHARGED_SHELLING_NATIVE_PARENT_GUARDS = (
    (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, 522_283_251, 768_813_060),
    (soundbank_editor.HIRC_ACTOR_MIXER, 768_813_060, 972_300_144),
    (soundbank_editor.HIRC_ACTOR_MIXER, 972_300_144, 694_534_885),
    (soundbank_editor.HIRC_ACTOR_MIXER, 694_534_885, 0),
)


def _guard_stationary_draw_original(bank: soundbank_editor.SoundBankEditor) -> None:
    editor = bank.hirc
    if (
        editor.event_actions(ORIGINAL_EVENT_ID) != (ORIGINAL_EVENT_ACTION_ID,)
        or editor.object_body(soundbank_editor.HIRC_ACTION, ORIGINAL_EVENT_ACTION_ID)
        != editor.create_play_action(
            ORIGINAL_EVENT_ACTION_ID, STATIONARY_RANDOM_DONOR_ID, bank.bank_id
        )
        or bank.media_entry(index=27).media_id != DONOR_MEDIA_ID
        or hashlib.sha256(editor.object_body(
            soundbank_editor.HIRC_SOUND, DONOR_SOUND_ID
        )).hexdigest() != STATIONARY_SOUND_DONOR_SHA256
        or hashlib.sha256(editor.object_body(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, STATIONARY_RANDOM_DONOR_ID
        )).hexdigest() != STATIONARY_RANDOM_DONOR_SHA256
    ):
        raise soundbank_editor.SoundBankError("stationary-draw original route or donor changed")


def validate_stationary_draw_hirc(bank: soundbank_editor.SoundBankEditor) -> None:
    """Verify the six-choice voice route in callbacks and staged bundles."""

    _guard_stationary_draw_original(bank)
    editor = bank.hirc
    random_body = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, STATIONARY_RANDOM_ID
    )
    if (
        hashlib.sha256(random_body).hexdigest() != STATIONARY_RANDOM_SHA256
        or editor.pitch_settings(soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, STATIONARY_RANDOM_ID)
        != soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
    ):
        raise soundbank_editor.SoundBankError(
            "stationary-draw Random selection, parent, or Pitch differ"
        )
    for index, sound_id, media_id in zip(
        STATIONARY_MEDIA_INDICES, STATIONARY_SOUND_IDS, STATIONARY_MEDIA_IDS, strict=True
    ):
        if (
            bank.media_entry(index=index).media_id != media_id
            or editor.object_body(soundbank_editor.HIRC_SOUND, sound_id)
            != standard_voice_sound_body(sound_id, media_id, direct_parent_id=STATIONARY_RANDOM_ID)
        ):
            raise soundbank_editor.SoundBankError("stationary-draw voice Sound or DIDX order differs")
    actions = (ORIGINAL_ROUTE_ACTION_ID, VOICE_ACTION_ID)
    if (
        editor.event_actions(VOICE_EVENT_ID) != actions
        or editor.object_body(soundbank_editor.HIRC_ACTION, actions[0])
        != editor.create_play_event_action(actions[0], ORIGINAL_EVENT_ID)
        or editor.object_body(soundbank_editor.HIRC_ACTION, actions[1])
        != editor.create_play_action(actions[1], STATIONARY_RANDOM_ID, bank.bank_id)
    ):
        raise soundbank_editor.SoundBankError("stationary-draw original delegation or voice Play differs")
    positions = {obj.object_id: obj.index for obj in editor.objects()}
    ordered = (*STATIONARY_SOUND_IDS, STATIONARY_RANDOM_ID, *actions, VOICE_EVENT_ID, ORIGINAL_EVENT_ID)
    if any(positions[left] >= positions[right] for left, right in zip(ordered, ordered[1:])):
        raise soundbank_editor.SoundBankError("stationary-draw HIRC serialization order differs")


def _guard_wide_sweep_original(bank: soundbank_editor.SoundBankEditor) -> None:
    editor = bank.hirc
    if (
        editor.event_actions(WIDE_SWEEP_ORIGINAL_EVENT_ID) != (WIDE_SWEEP_ORIGINAL_ACTION_ID,)
        or editor.object_body(soundbank_editor.HIRC_ACTION, WIDE_SWEEP_ORIGINAL_ACTION_ID)
        != editor.create_play_action(
            WIDE_SWEEP_ORIGINAL_ACTION_ID, WIDE_SWEEP_ORIGINAL_CONTAINER_ID, bank.bank_id
        )
        or bank.media_entry(index=6).media_id != WIDE_SWEEP_ORIGINAL_MEDIA_ID
    ):
        raise soundbank_editor.SoundBankError("wide-sweep original Event/Action/media route changed")
    sound = editor.object_body(soundbank_editor.HIRC_SOUND, WIDE_SWEEP_ORIGINAL_SOUND_ID)
    if (
        struct.unpack_from("<I", sound, 9)[0] != WIDE_SWEEP_ORIGINAL_MEDIA_ID
        or struct.unpack_from("<I", sound, 0x19)[0] != WIDE_SWEEP_ORIGINAL_CONTAINER_ID
        or hashlib.sha256(editor.object_body(
            soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WIDE_SWEEP_RANDOM_DONOR_ID
        )).hexdigest() != WIDE_SWEEP_RANDOM_DONOR_SHA256
    ):
        raise soundbank_editor.SoundBankError("wide-sweep original Sound or Random donor changed")


def validate_wide_sweep_hirc(bank: soundbank_editor.SoundBankEditor) -> None:
    """Guard the complete weighted voice route in both callbacks and staged bundles."""

    _guard_wide_sweep_original(bank)
    editor = bank.hirc
    random_body = editor.object_body(soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WIDE_SWEEP_RANDOM_ID)
    if (
        hashlib.sha256(random_body).hexdigest() != WIDE_SWEEP_RANDOM_SHA256
        or editor.pitch_settings(soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WIDE_SWEEP_RANDOM_ID)
        != soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
    ):
        raise soundbank_editor.SoundBankError("wide-sweep Random weights, repeat, parent, or Pitch differ")
    for index, sound_id, media_id in zip((37, 38), WIDE_SWEEP_SOUND_IDS, WIDE_SWEEP_MEDIA_IDS):
        if (
            bank.media_entry(index=index).media_id != media_id
            or editor.object_body(soundbank_editor.HIRC_SOUND, sound_id)
            != standard_voice_sound_body(sound_id, media_id, direct_parent_id=WIDE_SWEEP_RANDOM_ID)
        ):
            raise soundbank_editor.SoundBankError("wide-sweep voice Sound or DIDX order differs")
    actions = (WIDE_SWEEP_ORIGINAL_ROUTE_ACTION_ID, WIDE_SWEEP_VOICE_ACTION_ID)
    if (
        editor.event_actions(WIDE_SWEEP_EVENT_ID) != actions
        or editor.object_body(soundbank_editor.HIRC_ACTION, actions[0])
        != editor.create_play_event_action(actions[0], WIDE_SWEEP_ORIGINAL_EVENT_ID)
        or editor.object_body(soundbank_editor.HIRC_ACTION, actions[1])
        != editor.create_play_action(actions[1], WIDE_SWEEP_RANDOM_ID, bank.bank_id)
    ):
        raise soundbank_editor.SoundBankError("wide-sweep original delegation or voice Play differs")
    if any(event in editor.object_ids for event in WIDE_SWEEP_UNUSED_EVENT_IDS):
        raise soundbank_editor.SoundBankError("wide-sweep unused timing Events must not be present")
    positions = {obj.object_id: obj.index for obj in editor.objects()}
    ordered = (*WIDE_SWEEP_SOUND_IDS, WIDE_SWEEP_RANDOM_ID, *actions, WIDE_SWEEP_EVENT_ID)
    if any(positions[left] >= positions[right] for left, right in zip(ordered, ordered[1:])):
        raise soundbank_editor.SoundBankError("wide-sweep HIRC serialization order differs")


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


def _guard_charged_shelling_divine_original(
    bank: soundbank_editor.SoundBankEditor,
) -> None:
    editor = bank.hirc
    donor = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_DONOR_ID
    )
    if hashlib.sha256(donor).hexdigest() != CHARGED_SHELLING_RANDOM_DONOR_SHA256:
        raise soundbank_editor.SoundBankError("charged-shelling Divine Random donor changed")
    original_event = editor.object_body(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID)
    original_action = editor.object_body(
        soundbank_editor.HIRC_ACTION, ORIGINAL_EVENT_ACTION_ID
    )
    if (
        bank.media_entry(index=27).media_id != DONOR_MEDIA_ID
        or editor.event_actions(ORIGINAL_EVENT_ID) != (ORIGINAL_EVENT_ACTION_ID,)
        or hashlib.sha256(original_event).hexdigest()
        != CHARGED_SHELLING_ORIGINAL_EVENT_SHA256
        or hashlib.sha256(original_action).hexdigest()
        != CHARGED_SHELLING_ORIGINAL_ACTION_SHA256
        or original_action
        != editor.create_play_action(
            ORIGINAL_EVENT_ACTION_ID, STATIONARY_RANDOM_DONOR_ID, bank.bank_id
        )
    ):
        raise soundbank_editor.SoundBankError(
            "charged-shelling Divine donor Event, Action, or media changed"
        )

    for object_type, object_id, expected_parent_id in (
        CHARGED_SHELLING_NATIVE_PARENT_GUARDS
    ):
        body = editor.object_body(object_type, object_id)
        if len(body) < 15 or struct.unpack_from("<I", body, 11)[0] != expected_parent_id:
            raise soundbank_editor.SoundBankError(
                f"charged-shelling Divine native parent chain differs at {object_id}"
            )
    native_chain = {
        item
        for _, object_id, parent_id in CHARGED_SHELLING_NATIVE_PARENT_GUARDS
        for item in (object_id, parent_id)
        if item
    }
    if _event_referenced_stop_targets(editor) & native_chain:
        raise soundbank_editor.SoundBankError(
            "charged-shelling Divine donor route unexpectedly has a matching Stop"
        )


def validate_firing_silence_hirc(bank: soundbank_editor.SoundBankEditor) -> None:
    """Require the exact same-Bank silent wrapper, without playable media."""
    hirc = bank.hirc
    for kind, ident, digest in FIRING_SILENT_BODY_GUARDS:
        if hashlib.sha256(hirc.object_body(kind, ident)).hexdigest() != digest:
            raise soundbank_editor.SoundBankError("firing silence HIRC body differs")
    if (hirc.event_actions(FIRING_VOICE_EVENT_ID) != (FIRING_SILENT_ACTION_ID,)
            or hirc.event_actions(FIRING_SILENT_EVENT_ID) != ()
            or hirc.object_body(soundbank_editor.HIRC_ACTION, FIRING_SILENT_ACTION_ID)
            != hirc.create_play_event_action(FIRING_SILENT_ACTION_ID, FIRING_SILENT_EVENT_ID)):
        raise soundbank_editor.SoundBankError("firing silence wrapper route differs")
    positions = {obj.object_id: obj.index for obj in hirc.objects()}
    ordered = (CHARGED_SHELLING_EVENT_ID, FIRING_SILENT_ACTION_ID,
               FIRING_SILENT_EVENT_ID, FIRING_VOICE_EVENT_ID, ORIGINAL_EVENT_ID)
    if any(positions[a] >= positions[b] for a, b in zip(ordered, ordered[1:])):
        raise soundbank_editor.SoundBankError("firing silence serialization order differs")


def _apply_firing_silence(bank: soundbank_editor.SoundBankEditor) -> None:
    hirc = bank.hirc
    before = tuple((obj.object_type, obj.object_id, obj.body) for obj in hirc.objects())
    bodies = (
        (soundbank_editor.HIRC_ACTION, FIRING_SILENT_ACTION_ID,
         hirc.create_play_event_action(FIRING_SILENT_ACTION_ID, FIRING_SILENT_EVENT_ID)[4:]),
        (soundbank_editor.HIRC_EVENT, FIRING_SILENT_EVENT_ID, struct.pack("<I", 0)),
        (soundbank_editor.HIRC_EVENT, FIRING_VOICE_EVENT_ID, struct.pack("<II", 1, FIRING_SILENT_ACTION_ID)),
    )
    for kind, ident, body in bodies:
        hirc.insert_object(kind, ident, body, before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
                           label="add ordinary/charged firing silence")
    added = {ident for _, ident, _ in bodies}
    if tuple((obj.object_type, obj.object_id, obj.body) for obj in hirc.objects()
             if obj.object_id not in added) != before:
        raise soundbank_editor.SoundBankError("firing silence changed an existing object")
    validate_firing_silence_hirc(bank)


def validate_charged_shelling_divine_hirc(
    bank: soundbank_editor.SoundBankEditor,
) -> None:
    """Verify the isolated charge-start original delegation and Divine overlay."""

    _guard_charged_shelling_divine_original(bank)
    editor = bank.hirc
    validate_firing_silence_hirc(bank)

    for index, sound_id, media_id, body_sha256 in zip(
            CHARGED_SHELLING_DIVINE_MEDIA_INDICES,
            CHARGED_SHELLING_DIVINE_SOUND_IDS,
            CHARGED_SHELLING_DIVINE_MEDIA_IDS,
            CHARGED_SHELLING_DIVINE_SOUND_SHA256S,
            strict=True,
    ):
        sound_body = editor.object_body(soundbank_editor.HIRC_SOUND, sound_id)
        if (
                bank.media_entry(index=index).media_id != media_id
                or sound_body != standard_voice_sound_body(
            sound_id, media_id, direct_parent_id=CHARGED_SHELLING_RANDOM_ID,
        )
                or hashlib.sha256(sound_body).hexdigest() != body_sha256
                or editor.pitch_settings(soundbank_editor.HIRC_SOUND, sound_id)
                != soundbank_editor.HircPitchSettings(None, None)
        ):
            raise soundbank_editor.SoundBankError(f"charged-shelling Divine Sound {sound_id} differs")
    random_body = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID
    )
    if (
            len(random_body) != 95
            or hashlib.sha256(random_body).hexdigest() != CHARGED_SHELLING_RANDOM_SHA256
            or editor.pitch_settings(soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID)
            != soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
    ):
        raise soundbank_editor.SoundBankError("charged-shelling Divine Random weights, parent or Pitch differ")
    original_route = editor.object_body(
        soundbank_editor.HIRC_ACTION, CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID
    )
    divine_action = editor.object_body(
        soundbank_editor.HIRC_ACTION, CHARGED_SHELLING_DIVINE_ACTION_ID
    )
    event_body = editor.object_body(
        soundbank_editor.HIRC_EVENT, CHARGED_SHELLING_EVENT_ID
    )
    if (
            original_route
        != editor.create_play_event_action(
            CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID, ORIGINAL_EVENT_ID
        )
        or hashlib.sha256(original_route).hexdigest()
        != CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_SHA256
        or divine_action
        != editor.create_play_action(
            CHARGED_SHELLING_DIVINE_ACTION_ID,
        CHARGED_SHELLING_RANDOM_ID,
            bank.bank_id,
        )
        or hashlib.sha256(divine_action).hexdigest()
        != CHARGED_SHELLING_DIVINE_ACTION_SHA256
        or editor.event_actions(CHARGED_SHELLING_EVENT_ID)
        != (
            CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID,
            *CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS,
            CHARGED_SHELLING_DIVINE_ACTION_ID,
        )
        or hashlib.sha256(event_body).hexdigest() != CHARGED_SHELLING_EVENT_SHA256
    ):
        raise soundbank_editor.SoundBankError(
            "charged-shelling Divine Sound, Action, Event, or media differs"
        )

    positions = {item.object_id: item.index for item in editor.objects()}
    ordered = (
        *CHARGED_SHELLING_DIVINE_SOUND_IDS,
        CHARGED_SHELLING_RANDOM_ID,
        CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID,
        *CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS,
        CHARGED_SHELLING_DIVINE_ACTION_ID,
        CHARGED_SHELLING_EVENT_ID,
        ORIGINAL_EVENT_ID,
    )
    if any(positions[left] >= positions[right] for left, right in zip(ordered, ordered[1:])):
        raise soundbank_editor.SoundBankError(
            "charged-shelling Divine HIRC serialization order differs"
        )
    if (
        bank.external_stop_references != CHARGED_SHELLING_EXTERNAL_STOPS
            or _event_referenced_stop_targets(editor) != set(CHARGED_SHELLING_BUSTER_SOUND_IDS)
    ):
        raise soundbank_editor.SoundBankError("charged-shelling Buster Stop contract differs")
    for action_id, sound_id, body_sha256 in zip(
            CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS,
            CHARGED_SHELLING_BUSTER_SOUND_IDS,
            CHARGED_SHELLING_STOP_BUSTER_SHA256S,
            strict=True,
    ):
        stop = editor.object_body(soundbank_editor.HIRC_ACTION, action_id)
        if (
                stop != editor.create_stop_action(action_id, sound_id, transition_ms=50)
                or hashlib.sha256(stop).hexdigest() != body_sha256
        ):
            raise soundbank_editor.SoundBankError("charged-shelling Buster Stop body differs")


def _apply_charged_shelling_divine(
    bank: soundbank_editor.SoundBankEditor,
) -> None:
    editor = bank.hirc
    for index, sound_id, media_id in zip(
            CHARGED_SHELLING_DIVINE_MEDIA_INDICES,
            CHARGED_SHELLING_DIVINE_SOUND_IDS,
            CHARGED_SHELLING_DIVINE_MEDIA_IDS,
            strict=True,
    ):
        if bank.media_entry(index=index).media_id != media_id:
            raise soundbank_editor.SoundBankError("charged-shelling Divine DIDX identity differs")
        insert_standard_voice_sound(
            editor, sound_id, media_id, direct_parent_id=CHARGED_SHELLING_RANDOM_ID,
            label="insert charged-shelling Divine standard voice Sound",
        )
    editor.clone_random_sequence_container(
        CHARGED_SHELLING_RANDOM_DONOR_ID, CHARGED_SHELLING_RANDOM_ID, CHARGED_SHELLING_PLAYLIST,
        expected_playlist=((647_150_707, 50_000),), expected_avoid_repeat_count=1,
        avoid_repeat_count=0, label="clone uniform charged-shelling Divine Random",
    )
    editor.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID, 0x0B,
        768_813_060, STANDARD_VOICE_PARENT_ID, label="parent Divine Random to voice mixer",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID,
        expected=soundbank_editor.HircPitchSettings(None, (-50.0, 50.0)),
        random_range_cents=(-50.0, 50.0),
    )
    original_route = editor.create_play_event_action(
        CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID, ORIGINAL_EVENT_ID
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID,
        original_route[4:],
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add charged-shelling original-route PlayEvent Action",
    )
    for action_id, sound_id in zip(
            CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS, CHARGED_SHELLING_BUSTER_SOUND_IDS, strict=True,
    ):
        stop = editor.create_stop_action(action_id, sound_id, transition_ms=50)
        editor.insert_object(
            soundbank_editor.HIRC_ACTION, action_id, stop[4:],
            before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
            label="add independent charged-shelling Buster Stop Action",
        )
    divine_action = editor.create_play_action(
        CHARGED_SHELLING_DIVINE_ACTION_ID,
        CHARGED_SHELLING_RANDOM_ID,
        bank.bank_id,
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        CHARGED_SHELLING_DIVINE_ACTION_ID,
        divine_action[4:],
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add charged-shelling Divine Play Action",
    )
    editor.insert_object(
        soundbank_editor.HIRC_EVENT,
        CHARGED_SHELLING_EVENT_ID,
        struct.pack(
            "<IIIIII",
            5,
            CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID,
            *CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS,
            CHARGED_SHELLING_DIVINE_ACTION_ID,
        ),
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add isolated charged-shelling start Event",
    )
    _apply_firing_silence(bank)
    validate_charged_shelling_divine_hirc(bank)


def _apply_wide_sweep(bank: soundbank_editor.SoundBankEditor) -> None:
    _guard_wide_sweep_original(bank)
    editor = bank.hirc
    for sound_id, media_id in zip(WIDE_SWEEP_SOUND_IDS, WIDE_SWEEP_MEDIA_IDS):
        bank.media_entry(media_id=media_id)
        insert_standard_voice_sound(
            editor, sound_id, media_id, direct_parent_id=WIDE_SWEEP_RANDOM_ID,
            label="insert standard wide-sweep voice Sound",
        )
    editor.clone_random_sequence_container(
        WIDE_SWEEP_RANDOM_DONOR_ID, WIDE_SWEEP_RANDOM_ID, WIDE_SWEEP_PLAYLIST,
        expected_playlist=((647_150_707, 50_000),), expected_avoid_repeat_count=1,
        avoid_repeat_count=0, label="clone weighted one-shot wide-sweep Random",
    )
    editor.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WIDE_SWEEP_RANDOM_ID, 0x0B,
        768_813_060, STANDARD_VOICE_PARENT_ID, label="parent wide-sweep Random to voice mixer",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WIDE_SWEEP_RANDOM_ID,
        expected=soundbank_editor.HircPitchSettings(None, (-50.0, 50.0)),
        random_range_cents=(-50.0, 50.0),
    )
    for action_id, body in (
        (WIDE_SWEEP_ORIGINAL_ROUTE_ACTION_ID, editor.create_play_event_action(
            WIDE_SWEEP_ORIGINAL_ROUTE_ACTION_ID, WIDE_SWEEP_ORIGINAL_EVENT_ID)),
        (WIDE_SWEEP_VOICE_ACTION_ID, editor.create_play_action(
            WIDE_SWEEP_VOICE_ACTION_ID, WIDE_SWEEP_RANDOM_ID, bank.bank_id)),
    ):
        editor.insert_object(soundbank_editor.HIRC_ACTION, action_id, body[4:])
    editor.insert_object(
        soundbank_editor.HIRC_EVENT, WIDE_SWEEP_EVENT_ID,
        struct.pack("<III", 2, WIDE_SWEEP_ORIGINAL_ROUTE_ACTION_ID, WIDE_SWEEP_VOICE_ACTION_ID),
        label="add isolated frame-11 wide-sweep Event",
    )
    validate_wide_sweep_hirc(bank)
    if len(editor.objects()) != 148 or len(editor.build()) != 8_394:
        raise soundbank_editor.SoundBankError("wide-sweep combined HIRC counts differ")


def _apply_stationary_draw(bank: soundbank_editor.SoundBankEditor) -> None:
    _guard_stationary_draw_original(bank)
    editor = bank.hirc
    for sound_id, media_id in zip(STATIONARY_SOUND_IDS, STATIONARY_MEDIA_IDS, strict=True):
        bank.media_entry(media_id=media_id)
        insert_standard_voice_sound(
            editor, sound_id, media_id, direct_parent_id=STATIONARY_RANDOM_ID,
            label="insert standard stationary-draw voice Sound",
        )
    editor.clone_random_sequence_container(
        STATIONARY_RANDOM_DONOR_ID, STATIONARY_RANDOM_ID, STATIONARY_PLAYLIST,
        expected_playlist=((DONOR_SOUND_ID, 50_000),), expected_avoid_repeat_count=1,
        avoid_repeat_count=0, label="clone uniform stationary-draw Random",
    )
    editor.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, STATIONARY_RANDOM_ID, 0x0B,
        768_813_060, STANDARD_VOICE_PARENT_ID, label="parent stationary-draw Random to voice mixer",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, STATIONARY_RANDOM_ID,
        expected=soundbank_editor.HircPitchSettings(None, (-50.0, 50.0)),
        random_range_cents=(-50.0, 50.0),
    )

    original_route = editor.create_play_event_action(
        ORIGINAL_ROUTE_ACTION_ID, ORIGINAL_EVENT_ID
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        ORIGINAL_ROUTE_ACTION_ID,
        original_route[4:],
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add stationary-draw PlayEvent Action for the original route",
    )
    voice = editor.create_play_action(VOICE_ACTION_ID, STATIONARY_RANDOM_ID, bank.bank_id)
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        VOICE_ACTION_ID,
        voice[4:],
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add stationary-draw voice Play Action",
    )
    editor.insert_object(
        soundbank_editor.HIRC_EVENT,
        VOICE_EVENT_ID,
        struct.pack("<III", 2, ORIGINAL_ROUTE_ACTION_ID, VOICE_ACTION_ID),
        before=(soundbank_editor.HIRC_EVENT, ORIGINAL_EVENT_ID),
        label="add isolated stationary-draw Event",
    )
    validate_stationary_draw_hirc(bank)


def _validate_reload_hirc(bank: soundbank_editor.SoundBankEditor) -> None:
    """Verify the complete reload voice overlay and its local random Pitch."""

    editor = bank.hirc
    sound_body = editor.object_body(
        soundbank_editor.HIRC_SOUND, RELOAD_VOICE_SOUND_ID
    )
    if (
        bank.media_entry(index=36).media_id != RELOAD_VOICE_MEDIA_ID
        or len(sound_body) != 55
        or hashlib.sha256(sound_body).hexdigest() != RELOAD_VOICE_SOUND_SHA256
        or editor.pitch_settings(
            soundbank_editor.HIRC_SOUND, RELOAD_VOICE_SOUND_ID
        )
        != RELOAD_VOICE_PITCH
    ):
        raise soundbank_editor.SoundBankError(
            "reload voice Sound, media, parent, positioning, or Pitch differ"
        )
    if (
        editor.object_body(soundbank_editor.HIRC_ACTION, RELOAD_VOICE_ACTION_ID)
        != editor.create_play_action(
            RELOAD_VOICE_ACTION_ID, RELOAD_VOICE_SOUND_ID, bank.bank_id
        )
        or editor.event_actions(RELOAD_EVENT_ID)
        != (RELOAD_ORIGINAL_ACTION_ID, RELOAD_VOICE_ACTION_ID)
    ):
        raise soundbank_editor.SoundBankError(
            "reload voice Action or Event route differs"
        )
    positions = {item.object_id: item.index for item in editor.objects()}
    if not (
        positions[RELOAD_VOICE_SOUND_ID]
        < positions[RELOAD_VOICE_ACTION_ID]
        < positions[RELOAD_EVENT_ID]
    ):
        raise soundbank_editor.SoundBankError(
            "reload voice HIRC objects violate Wwise v120 load order"
        )


def validate_overhead_smash_hirc(bank: soundbank_editor.SoundBankEditor) -> None:
    """Verify both Accel choices, inherited Pitch, and silent-prime load order."""

    editor = bank.hirc
    random_body = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, OVERHEAD_RANDOM_ID
    )
    if (
            hashlib.sha256(random_body).hexdigest() != OVERHEAD_RANDOM_SHA256
            or editor.pitch_settings(soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, OVERHEAD_RANDOM_ID)
            != soundbank_editor.HircPitchSettings(None, (-50.0, 50.0))
    ):
        raise soundbank_editor.SoundBankError(
            "overhead-smash Random weights, repeat, parent, or Pitch differ"
        )
    for index, sound_id, media_id in zip(
            OVERHEAD_MEDIA_INDICES, OVERHEAD_SOUND_IDS, OVERHEAD_MEDIA_IDS, strict=True
    ):
        if (
                bank.media_entry(index=index).media_id != media_id
                or editor.object_body(soundbank_editor.HIRC_SOUND, sound_id)
                != standard_voice_sound_body(sound_id, media_id, direct_parent_id=OVERHEAD_RANDOM_ID)
                or editor.pitch_settings(soundbank_editor.HIRC_SOUND, sound_id)
                != soundbank_editor.HircPitchSettings(None, None)
        ):
            raise soundbank_editor.SoundBankError(
                "overhead-smash voice Sound, inherited Pitch, or DIDX order differs"
            )
    actions = (OVERHEAD_SILENT_PRIME_ACTION_ID, OVERHEAD_VOICE_ACTION_ID)
    if (
            editor.event_actions(OVERHEAD_VOICE_EVENT_ID) != actions
            or editor.event_actions(OVERHEAD_SILENT_EVENT_ID) != ()
            or editor.object_body(soundbank_editor.HIRC_ACTION, actions[0])
            != editor.create_play_event_action(actions[0], OVERHEAD_SILENT_EVENT_ID)
            or editor.object_body(soundbank_editor.HIRC_ACTION, actions[1])
            != editor.create_play_action(actions[1], OVERHEAD_RANDOM_ID, bank.bank_id)
            or OBSOLETE_OVERHEAD_ORIGINAL_ROUTE_ACTION_ID in editor.object_ids
    ):
        raise soundbank_editor.SoundBankError(
            "overhead-smash silent prime or Random Play route differs"
        )
    positions = {obj.object_id: obj.index for obj in editor.objects()}
    ordered = (
        *OVERHEAD_SOUND_IDS, OVERHEAD_RANDOM_ID, OVERHEAD_VOICE_ACTION_ID,
        OVERHEAD_SILENT_PRIME_ACTION_ID, OVERHEAD_SILENT_EVENT_ID,
        OVERHEAD_VOICE_EVENT_ID, OVERHEAD_ORIGINAL_EVENT_ID,
    )
    if any(positions[left] >= positions[right] for left, right in zip(ordered, ordered[1:])):
        raise soundbank_editor.SoundBankError("overhead-smash HIRC serialization order differs")


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Create the reviewed shared-Bank voice routes in deterministic order."""

    _guard_charged_shelling_divine_original(bank)
    _apply_stationary_draw(bank)
    editor = bank.hirc

    bank.media_entry(media_id=OVERHEAD_VOICE_MEDIA_ID)
    if bank.media_entry(index=OVERHEAD_DONOR_MEDIA_INDEX).media_id != OVERHEAD_DONOR_MEDIA_ID:
        raise soundbank_editor.SoundBankError(
            "overhead-smash donor DIDX identity differs from its design guard"
        )
    if editor.event_actions(OVERHEAD_ORIGINAL_EVENT_ID) != (
        OVERHEAD_ORIGINAL_EVENT_ACTION_ID,
    ):
        raise soundbank_editor.SoundBankError(
            "original overhead-smash Event route differs from its design guard"
        )
    original_action = editor.object_body(
        soundbank_editor.HIRC_ACTION, OVERHEAD_ORIGINAL_EVENT_ACTION_ID
    )
    if (
        struct.unpack_from("<H", original_action, 4)[0]
        != soundbank_editor.ACTION_PLAY
        or struct.unpack_from("<I", original_action, 6)[0]
        != OVERHEAD_ORIGINAL_CONTAINER_ID
    ):
        raise soundbank_editor.SoundBankError(
            "original overhead-smash Action no longer targets its Container"
        )
    donor_sound = editor.object_body(
        soundbank_editor.HIRC_SOUND, OVERHEAD_DONOR_SOUND_ID
    )
    if (
        len(donor_sound) != 72
        or struct.unpack_from("<I", donor_sound, 9)[0] != OVERHEAD_DONOR_MEDIA_ID
        or struct.unpack_from("<I", donor_sound, OVERHEAD_SOUND_OVERRIDE_BUS_OFFSET)[0]
        != 0
        or struct.unpack_from("<I", donor_sound, OVERHEAD_SOUND_PARENT_OFFSET)[0]
        != OVERHEAD_ORIGINAL_CONTAINER_ID
        or donor_sound[POSITIONING_VECTOR_OFFSET] != 0xC0
        or struct.unpack_from("<4I", donor_sound, OVERHEAD_SOUND_AUX_OFFSET)
        != OVERHEAD_SOUND_AUX_IDS
    ):
        raise soundbank_editor.SoundBankError(
            "overhead-smash donor Sound topology differs from its design guard"
        )

    random_donor = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, OVERHEAD_RANDOM_DONOR_ID
    )
    if hashlib.sha256(random_donor).hexdigest() != OVERHEAD_RANDOM_DONOR_SHA256:
        raise soundbank_editor.SoundBankError("overhead-smash Random donor changed")
    for sound_id, media_id in zip(OVERHEAD_SOUND_IDS, OVERHEAD_MEDIA_IDS, strict=True):
        bank.media_entry(media_id=media_id)
        insert_standard_voice_sound(
            editor, sound_id, media_id, direct_parent_id=OVERHEAD_RANDOM_ID,
            label="insert standard overhead-smash custom-voice Sound",
        )
    editor.clone_random_sequence_container(
        OVERHEAD_RANDOM_DONOR_ID, OVERHEAD_RANDOM_ID, OVERHEAD_PLAYLIST,
        expected_playlist=((647_150_707, 50_000),), expected_avoid_repeat_count=1,
        avoid_repeat_count=0, label="clone uniform one-shot overhead-smash Random",
    )
    editor.patch_u32(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, OVERHEAD_RANDOM_ID, 0x0B,
        768_813_060, STANDARD_VOICE_PARENT_ID, label="parent overhead-smash Random to voice mixer",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, OVERHEAD_RANDOM_ID,
        expected=soundbank_editor.HircPitchSettings(None, (-50.0, 50.0)),
        random_range_cents=(-50.0, 50.0),
    )

    overhead_voice = editor.create_play_action(
        OVERHEAD_VOICE_ACTION_ID, OVERHEAD_RANDOM_ID, bank.bank_id
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        OVERHEAD_VOICE_ACTION_ID,
        overhead_voice[4:],
        before=(soundbank_editor.HIRC_EVENT, OVERHEAD_ORIGINAL_EVENT_ID),
        label="add overhead-smash Accel Play Action",
    )

    silent_prime = editor.create_play_event_action(
        OVERHEAD_SILENT_PRIME_ACTION_ID, OVERHEAD_SILENT_EVENT_ID
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        OVERHEAD_SILENT_PRIME_ACTION_ID,
        silent_prime[4:],
        before=(soundbank_editor.HIRC_EVENT, OVERHEAD_ORIGINAL_EVENT_ID),
        label="add overhead-smash silent-prime PlayEvent Action",
    )
    editor.insert_object(
        soundbank_editor.HIRC_EVENT,
        OVERHEAD_SILENT_EVENT_ID,
        struct.pack("<I", 0),
        before=(soundbank_editor.HIRC_EVENT, OVERHEAD_ORIGINAL_EVENT_ID),
        label="add overhead-smash zero-Action silent Event",
    )
    editor.insert_object(
        soundbank_editor.HIRC_EVENT,
        OVERHEAD_VOICE_EVENT_ID,
        struct.pack(
            "<III",
            2,
            OVERHEAD_SILENT_PRIME_ACTION_ID,
            OVERHEAD_VOICE_ACTION_ID,
        ),
        before=(soundbank_editor.HIRC_EVENT, OVERHEAD_ORIGINAL_EVENT_ID),
        label="add overhead-smash character-voice replacement Event",
    )
    validate_overhead_smash_hirc(bank)

    bank.media_entry(media_id=RELOAD_VOICE_MEDIA_ID)
    if bank.media_entry(index=RELOAD_DONOR_MEDIA_INDEX).media_id != RELOAD_DONOR_MEDIA_ID:
        raise soundbank_editor.SoundBankError(
            "reload donor DIDX identity differs from its design guard"
        )
    if editor.event_actions(RELOAD_EVENT_ID) != (RELOAD_ORIGINAL_ACTION_ID,):
        raise soundbank_editor.SoundBankError(
            "original reload Event route differs from its design guard"
        )
    reload_action = editor.object_body(
        soundbank_editor.HIRC_ACTION, RELOAD_ORIGINAL_ACTION_ID
    )
    if (
        struct.unpack_from("<H", reload_action, 4)[0]
        != soundbank_editor.ACTION_PLAY
        or struct.unpack_from("<I", reload_action, 6)[0] != RELOAD_CONTAINER_ID
    ):
        raise soundbank_editor.SoundBankError(
            "original reload Action no longer targets its Container"
        )
    reload_donor = editor.object_body(
        soundbank_editor.HIRC_SOUND, RELOAD_DONOR_SOUND_ID
    )
    if (
        len(reload_donor) != 72
        or reload_donor[8] != 0
        or struct.unpack_from("<I", reload_donor, 9)[0] != RELOAD_DONOR_MEDIA_ID
        or struct.unpack_from(
            "<I", reload_donor, RELOAD_SOUND_OVERRIDE_BUS_OFFSET
        )[0]
        != 0
        or struct.unpack_from("<I", reload_donor, RELOAD_SOUND_PARENT_OFFSET)[0]
        != RELOAD_CONTAINER_ID
        or reload_donor[POSITIONING_VECTOR_OFFSET] != 0xC0
        or struct.unpack_from("<4I", reload_donor, RELOAD_SOUND_AUX_OFFSET)
        != RELOAD_SOUND_AUX_IDS
    ):
        raise soundbank_editor.SoundBankError(
            "reload donor Sound topology differs from its design guard"
        )
    reload_container = editor.object_body(
        soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, RELOAD_CONTAINER_ID
    )
    if (
        len(reload_container) != 88
        or struct.unpack_from(
            "<H", reload_container, RELOAD_CONTAINER_AVOID_REPEAT_OFFSET
        )[0]
        != 1
        or reload_container[RELOAD_CONTAINER_MODE_OFFSET] != 0
        or reload_container[RELOAD_CONTAINER_PLAYLIST_OFFSET:]
        != RELOAD_CONTAINER_PLAYLIST
    ):
        raise soundbank_editor.SoundBankError(
            "reload Container playlist differs from its design guard"
        )

    insert_standard_voice_sound(
        editor,
        RELOAD_VOICE_SOUND_ID,
        RELOAD_VOICE_MEDIA_ID,
        label="insert standard reload custom-voice Sound",
    )
    editor.set_pitch(
        soundbank_editor.HIRC_SOUND,
        RELOAD_VOICE_SOUND_ID,
        expected=soundbank_editor.HircPitchSettings(None, None),
        random_range_cents=RELOAD_VOICE_PITCH.random_range_cents,
        label="set reload voice Pitch to plus/minus 50 cents",
    )
    reload_voice = editor.create_play_action(
        RELOAD_VOICE_ACTION_ID,
        RELOAD_VOICE_SOUND_ID,
        bank.bank_id,
    )
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        RELOAD_VOICE_ACTION_ID,
        reload_voice[4:],
        before=(soundbank_editor.HIRC_EVENT, RELOAD_EVENT_ID),
        label="add Raising Heart reload Play Action",
    )
    editor.append_event_action(
        RELOAD_EVENT_ID,
        RELOAD_VOICE_ACTION_ID,
        expected_actions=(RELOAD_ORIGINAL_ACTION_ID,),
        label="append Raising Heart voice to reload Event",
    )
    _validate_reload_hirc(bank)
    _apply_wide_sweep(bank)
    _apply_charged_shelling_divine(bank)
    _apply_wyrmstake_voice(bank)
    _apply_wyrmstake_original_voice_mute(bank)
    clutch.apply_voices(bank)
    mounted.apply_voice(bank)


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=(
        (34, VOICE_MEDIA_ID),
        (35, OVERHEAD_VOICE_MEDIA_ID),
        (36, RELOAD_VOICE_MEDIA_ID),
        (37, WIDE_SWEEP_MEDIA_IDS[0]),
        (38, WIDE_SWEEP_MEDIA_IDS[1]),
        (39, STATIONARY_MEDIA_IDS[1]),
        (40, STATIONARY_MEDIA_IDS[2]),
        (41, STATIONARY_MEDIA_IDS[3]),
        (42, STATIONARY_MEDIA_IDS[4]),
        (43, STATIONARY_MEDIA_IDS[5]),
        (44, OVERHEAD_MEDIA_IDS[1]),
        (45, CHARGED_SHELLING_DIVINE_MEDIA_ID),
        (46, CHARGED_SHELLING_DIVINE_MEDIA_IDS[1]),
        (47, WYR_STAKE_MEDIA_IDS[0]),
        (48, WYR_STAKE_MEDIA_IDS[1]),
    ) + tuple((voice.media.expected_index, voice.media.media_id) for voice in clutch.VOICES)
    + ((mounted.MEDIA.expected_index, mounted.MEDIA.media_id),),
    hirc_changed_bytes=57,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_ID),
        (soundbank_editor.HIRC_SOUND, STATIONARY_SOUND_IDS[1]),
        (soundbank_editor.HIRC_SOUND, STATIONARY_SOUND_IDS[2]),
        (soundbank_editor.HIRC_SOUND, STATIONARY_SOUND_IDS[3]),
        (soundbank_editor.HIRC_SOUND, STATIONARY_SOUND_IDS[4]),
        (soundbank_editor.HIRC_SOUND, STATIONARY_SOUND_IDS[5]),
        (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, STATIONARY_RANDOM_ID),
        (soundbank_editor.HIRC_ACTION, ORIGINAL_ROUTE_ACTION_ID),
        (soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, VOICE_EVENT_ID),
        (soundbank_editor.HIRC_SOUND, OVERHEAD_VOICE_SOUND_ID),
        (soundbank_editor.HIRC_SOUND, OVERHEAD_SOUND_IDS[1]),
        (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, OVERHEAD_RANDOM_ID),
        (soundbank_editor.HIRC_ACTION, OVERHEAD_VOICE_ACTION_ID),
        (soundbank_editor.HIRC_ACTION, OVERHEAD_SILENT_PRIME_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, OVERHEAD_SILENT_EVENT_ID),
        (soundbank_editor.HIRC_EVENT, OVERHEAD_VOICE_EVENT_ID),
        (soundbank_editor.HIRC_SOUND, RELOAD_VOICE_SOUND_ID),
        (soundbank_editor.HIRC_ACTION, RELOAD_VOICE_ACTION_ID),
        (soundbank_editor.HIRC_SOUND, WIDE_SWEEP_SOUND_IDS[0]),
        (soundbank_editor.HIRC_SOUND, WIDE_SWEEP_SOUND_IDS[1]),
        (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, WIDE_SWEEP_RANDOM_ID),
        (soundbank_editor.HIRC_ACTION, WIDE_SWEEP_ORIGINAL_ROUTE_ACTION_ID),
        (soundbank_editor.HIRC_ACTION, WIDE_SWEEP_VOICE_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, WIDE_SWEEP_EVENT_ID),
        (soundbank_editor.HIRC_SOUND, CHARGED_SHELLING_DIVINE_SOUND_ID),
        (soundbank_editor.HIRC_SOUND, CHARGED_SHELLING_DIVINE_SOUND_IDS[1]),
        (soundbank_editor.HIRC_RANDOM_SEQUENCE_CONTAINER, CHARGED_SHELLING_RANDOM_ID),
        (
            soundbank_editor.HIRC_ACTION,
            CHARGED_SHELLING_ORIGINAL_ROUTE_ACTION_ID,
        ),
        (soundbank_editor.HIRC_ACTION, CHARGED_SHELLING_STOP_BUSTER_ACTION_ID),
        (soundbank_editor.HIRC_ACTION, CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS[1]),
        (soundbank_editor.HIRC_ACTION, CHARGED_SHELLING_STOP_BUSTER_ACTION_IDS[2]),
        (soundbank_editor.HIRC_ACTION, CHARGED_SHELLING_DIVINE_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, CHARGED_SHELLING_EVENT_ID),
        (soundbank_editor.HIRC_ACTION, FIRING_SILENT_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, FIRING_SILENT_EVENT_ID),
        (soundbank_editor.HIRC_EVENT, FIRING_VOICE_EVENT_ID),
        (soundbank_editor.HIRC_SOUND, WYR_STAKE_SOUND_IDS[0]),
        (soundbank_editor.HIRC_ACTION, WYR_STAKE_ACTION_IDS[0]),
        (soundbank_editor.HIRC_EVENT, WYR_STAKE_EVENT_IDS[0]),
        (soundbank_editor.HIRC_SOUND, WYR_STAKE_SOUND_IDS[1]),
        (soundbank_editor.HIRC_ACTION, WYR_STAKE_ACTION_IDS[1]),
        (soundbank_editor.HIRC_EVENT, WYR_STAKE_EVENT_IDS[1]),
        (soundbank_editor.HIRC_EVENT, WYR_STAKE_MUTE_EMPTY_EVENT_ID),
        (soundbank_editor.HIRC_ACTION, WYR_STAKE_MUTE_PLAY_ACTION_ID),
        (soundbank_editor.HIRC_EVENT, WYR_STAKE_MUTE_ROUTE_EVENT_ID),
    ) + clutch.VOICE_OBJECTS + mounted.VOICE_OBJECTS,
    resized_hirc_objects=(
        (soundbank_editor.HIRC_EVENT, RELOAD_EVENT_ID, 12, 16),
    ),
    hirc_size_delta=2000,
)


PLAN = SoundBankBuildPlan(
    name="wp_gun_cmn",
    design_ids=(
        "wp_gun_cmn.stationary_draw",
        "wp_gun_cmn.overhead_smash",
        "wp_gun_cmn.reload",
        "wp_gun_cmn.wide_sweep",
        "wp07_gun_epvsp_shell.charged_shelling",
        "wp07_gun_epvsp_shell.wyrmstake_cannon",
        clutch.DESIGN_ID,
        mounted.DESIGN_ID,
    ),
    source="original/nbnk/wp_gun_cmn.nbnk",
    target="sound/wwise/Windows/wp_gun_cmn.nbnk",
    expected_source_sha256=(
        "bba3b716b0bbaf06dfe562adf9867c43dd78b29dd5132b150f1f08142b54cfa1"
    ),
    expected_bank_id=939_294_496,
    reference_inputs=STANDARD_VOICE_REFERENCE_INPUTS,
    external_stop_references=CHARGED_SHELLING_EXTERNAL_STOPS,
    media_additions=(
        MediaAddition(
            34,
            VOICE_MEDIA_ID,
            "audio/wp_gun_cmn/stationary_draw/"
            "raising_heart_standby_ready_01(movie_1st.raising_heart."
            "standby_ready_set_up.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            35,
            OVERHEAD_VOICE_MEDIA_ID,
            "audio/wp_gun_cmn/overhead_smash/"
            "nanoha_accel_01(battle_of_aces.attack_voice.attack_03.2).wav",
            wem_channels=1,
        ),
        MediaAddition(
            36,
            RELOAD_VOICE_MEDIA_ID,
            "audio/wp_gun_cmn/reload/"
            "raising_heart_reload_01(movie_2nd_as.raising_heart.reload.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            37, WIDE_SWEEP_MEDIA_IDS[0],
            "audio/wp_gun_cmn/wide_sweep/"
            "nanoha_smasher_01(gears_of_destiny.attack_voice.attack_05.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            38, WIDE_SWEEP_MEDIA_IDS[1],
            "audio/wp_gun_cmn/wide_sweep/"
            "nanoha_smasher_02(movie_2nd_as.nanoha.smasher.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            39, STATIONARY_MEDIA_IDS[1],
            "audio/wp_gun_cmn/stationary_draw/"
            "raising_heart_standby_ready_02(movie_1st.raising_heart.standby_ready_01.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            40, STATIONARY_MEDIA_IDS[2],
            "audio/wp_gun_cmn/stationary_draw/"
            "raising_heart_standby_ready_03(movie_1st.raising_heart.standby_ready_02.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            41, STATIONARY_MEDIA_IDS[3],
            "audio/wp_gun_cmn/stationary_draw/"
            "raising_heart_standby_ready_04(movie_1st.raising_heart.standby_ready_03.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            42, STATIONARY_MEDIA_IDS[4],
            "audio/wp_gun_cmn/stationary_draw/"
            "raising_heart_standby_ready_05(movie_1st.raising_heart.standby_ready_04.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            43, STATIONARY_MEDIA_IDS[5],
            "audio/wp_gun_cmn/stationary_draw/"
            "raising_heart_standby_ready_06(movie_1st.raising_heart.standby_ready_05.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            44, OVERHEAD_MEDIA_IDS[1],
            "audio/wp_gun_cmn/overhead_smash/"
            "nanoha_accel_02(gears_of_destiny.attack_voice.attack_03.1+"
            "movie_2nd_as.nanoha.accel_shooter.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            CHARGED_SHELLING_DIVINE_MEDIA_INDEX,
            CHARGED_SHELLING_DIVINE_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/charged_shelling/"
            "nanoha_divine_01(battle_of_aces.attack_04.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            46, CHARGED_SHELLING_DIVINE_MEDIA_IDS[1],
            "audio/wp07_gun_epvsp_shell/charged_shelling/"
            "nanoha_divine_02(gears_of_destiny.attack_voice.attack_04.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            47, WYR_STAKE_MEDIA_IDS[0],
            "audio/wp07_gun_epvsp_shell/wyrmstake_cannon/"
            "nanoha_acs_01(gears_of_destiny.attack_voice.attack_02.1).wav",
            wem_channels=1,
        ),
        MediaAddition(
            48, WYR_STAKE_MEDIA_IDS[1],
            "audio/wp07_gun_epvsp_shell/wyrmstake_cannon/"
            "nanoha_drive_01(gears_of_destiny.attack_voice.attack_02.2).wav",
            wem_channels=1,
        ),
        *(voice.media for voice in clutch.VOICES),
        mounted.MEDIA,
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
