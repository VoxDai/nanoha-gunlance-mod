"""Guarded Wyvern's Fire voice routes shared by the three artifact owners."""

import hashlib
import struct

from tools import soundbank_editor as se

from .voice_standard import (
    STANDARD_VOICE_PARENT_ID, insert_standard_voice_sound, standard_voice_sound_body,
)

DESIGN_ID = "wp07_gun_epvsp_shell.wyverns_fire"
CHARGE_EVENT = 302_768_804
PRIVATE_EVENT = 281_273_126
NATIVE_PLAY_EVENT = 3_388_979_775
STOP_EVENT = 461_444_626
NATIVE_STOP = 743_936_681
STOP_DONOR_SHA256 = "137f38d973a5e3b84d35d84146d2b562e21e575abbfee532b8531d3583ae0ebd"
RIGHT_EVENT = 3_655_102_100
LEFT_EVENT = 3_253_425_110
NEW_REQUEST = 26690
DONOR_RECORD_SHA256 = "9fea5c28772ab6bc99423844a29926803733ac708639e15eb16d0de280c1da89"
EPVSP_OLD_ROW = (0, 26501, 26502, 2000, 0)
EPVSP_NEW_ROW = (0, NEW_REQUEST, 26502, 2000, 0)
EPVSP_CLUTCH_ROW = (0, 26501, 26502, 2020, 0)
RANDOM_DONOR = 58_172_267
RANDOM_DONOR_SHA256 = "53ce24846e01ef33e99c2c66575a9e50e367730b25231c53289fc2e772c4aff7"
PITCH = se.HircPitchSettings(None, (-50.0, 50.0))
CONTAINERS = (3_610_379_736, 3_391_377_780, 362_366_644)
PLAY_ACTIONS = (4_011_774_951, 254_514_827, 1_866_468_495)
STOP_ACTIONS = (2_987_046_856, 3_645_807_405)
# DIDX index, Media ID, Sound ID, voice family index.
CLIPS = (
    (44, 322_318_543, 4_149_261_730, 0),
    (45, 3_332_910_283, 36_215_958, 1),
    (46, 2_217_266_443, 2_472_459_210, 2),
    (54, 2_014_220_448, 2_849_114_849, 0),
    (55, 3_735_305_437, 1_620_588_112, 0),
    (56, 941_385_580, 1_229_173_909, 1),
    (57, 3_696_251_564, 3_984_040_149, 2),
    (58, 631_532_425, 3_346_634_804, 2),
)
EXTRA_FILENAMES = (
    "nanoha_starlight_02(battle_of_aces.attack_voice.attack_01.1).wav",
    "nanoha_starlight_03(movie_1st.nanoha.starlight_breaker.1).wav",
    "raising_heart_starlight_breaker_02(movie_2nd_as.raising_heart.starlight_breaker.1).wav",
    "nanoha_breaker_02(battle_of_aces.attack_voice.attack_01.2).wav",
    "nanoha_breaker_03(movie_1st.nanoha.starlight_breaker.2).wav",
)
# Exact bodies from the guarded prototype, including playlist and pitch.
CONTAINER_BODY_SHA256S = (
    "1e448d3da356472e8305b9247cb8518aa7292ce67b40150bdcae96cfe7f69c8c",
    "4e837dd3701b18dd8d4113ada5535974e0a6e9ca60a09605f451ef652df8b610",
    "1a6016233c7c433dba061964d783e44889891ff67394984189773a35cdc0e263",
)


def _require(condition, message):
    if not condition:
        raise se.SoundBankError(f"Wyvern's Fire: {message}")


def _play(hirc, bank_id, family):
    return hirc.create_play_action(
        PLAY_ACTIONS[family], CONTAINERS[family], bank_id,
        delay_random_range_ms=(0, 50) if family == 1 else None,
    )


def apply_wyverns_fire(bank):
    hirc = bank.hirc
    for event, actions in (
        (CHARGE_EVENT, (51_759_545,)),
        (STOP_EVENT, (NATIVE_STOP,)),
        (RIGHT_EVENT, (648_832_766,)),
        (LEFT_EVENT, (120_830_402,)),
    ):
        _require(hirc.event_actions(event) == actions, f"original Event {event} changed")
    donor = hirc.object_body(se.HIRC_RANDOM_SEQUENCE_CONTAINER, RANDOM_DONOR)
    _require(hashlib.sha256(donor).hexdigest() == RANDOM_DONOR_SHA256, "Random donor changed")
    for index, media, sound, family in CLIPS:
        _require(bank.media_entry(index=index).media_id == media, f"DIDX #{index} changed")
        insert_standard_voice_sound(hirc, sound, media, direct_parent_id=CONTAINERS[family])
    for family, container in enumerate(CONTAINERS):
        playlist = tuple((sound, 50_000) for _, _, sound, group in CLIPS if group == family)
        hirc.clone_random_sequence_container(
            RANDOM_DONOR, container, playlist,
            expected_playlist=((46_149_961, 50_000),),
            expected_avoid_repeat_count=1, avoid_repeat_count=0,
        )
        hirc.patch_u32(se.HIRC_RANDOM_SEQUENCE_CONTAINER, container, 0x0B,
                       717_111_903, STANDARD_VOICE_PARENT_ID, label="Wyvern voice parent")
        hirc.set_pitch(se.HIRC_RANDOM_SEQUENCE_CONTAINER, container,
                       expected=PITCH, random_range_cents=PITCH.random_range_cents)
    body = hirc.create_play_event_action(NATIVE_PLAY_EVENT, CHARGE_EVENT)
    hirc.insert_object(se.HIRC_ACTION, NATIVE_PLAY_EVENT, body[4:])
    for family, action in enumerate(PLAY_ACTIONS):
        hirc.insert_object(
            se.HIRC_ACTION, action, _play(hirc, bank.bank_id, family)[4:],
            before=(se.HIRC_EVENT, RIGHT_EVENT) if family == 2 else None,
        )
    hirc.insert_object(se.HIRC_EVENT, PRIVATE_EVENT,
                       struct.pack("<IIII", 3, NATIVE_PLAY_EVENT, *PLAY_ACTIONS[:2]))
    hirc.append_event_action(RIGHT_EVENT, PLAY_ACTIONS[2], expected_actions=(648_832_766,))
    actions = (NATIVE_STOP,)
    for stop, target in zip(STOP_ACTIONS, CONTAINERS[:2], strict=True):
        hirc.clone_stop_action(NATIVE_STOP, stop, target,
                               expected_target_id=60_034_062,
                               expected_body_sha256=STOP_DONOR_SHA256,
                               before_event_id=STOP_EVENT)
        hirc.append_event_action(STOP_EVENT, stop, expected_actions=actions)
        actions += (stop,)
    validate_wyverns_fire_hirc(bank)


def validate_wyverns_fire_hirc(bank):
    hirc = bank.hirc
    expected_lists = {
        CHARGE_EVENT: (51_759_545,),
        STOP_EVENT: (NATIVE_STOP, *STOP_ACTIONS),
        RIGHT_EVENT: (648_832_766, PLAY_ACTIONS[2]),
        LEFT_EVENT: (120_830_402,),
        PRIVATE_EVENT: (NATIVE_PLAY_EVENT, *PLAY_ACTIONS[:2]),
    }
    objects = hirc.objects()
    positions = {o.object_id: o.index for o in objects}
    all_events = {o.object_id: hirc.event_actions(o.object_id)
                  for o in objects if o.object_type == se.HIRC_EVENT}
    for event, actions in expected_lists.items():
        _require(all_events.get(event) == actions, f"Event {event} actions differ")
    for event, actions in (
        (PRIVATE_EVENT, (NATIVE_PLAY_EVENT, *PLAY_ACTIONS[:2])),
        (RIGHT_EVENT, PLAY_ACTIONS[2:]),
        (STOP_EVENT, STOP_ACTIONS),
    ):
        for action in actions:
            owners = [e for e, owned in all_events.items() if action in owned]
            _require(owners == [event] and positions[action] < positions[event],
                     f"Action {action} ownership or serialization order differs")
    _require(hirc.object_body(se.HIRC_ACTION, NATIVE_PLAY_EVENT) ==
             hirc.create_play_event_action(NATIVE_PLAY_EVENT, CHARGE_EVENT),
             "private Event no longer calls the original charge")
    for family, action in enumerate(PLAY_ACTIONS):
        _require(hirc.object_body(se.HIRC_ACTION, action) == _play(hirc, bank.bank_id, family),
                 f"Container {family + 1} Play or delay differs")
    donor = hirc.object_body(se.HIRC_ACTION, NATIVE_STOP)
    _require(hashlib.sha256(donor).hexdigest() == STOP_DONOR_SHA256, "native Stop differs")
    for action, target in zip(STOP_ACTIONS, CONTAINERS[:2], strict=True):
        expected = struct.pack("<I", action) + donor[4:6] + struct.pack("<I", target) + donor[10:]
        _require(hirc.object_body(se.HIRC_ACTION, action) == expected, "Stop clone differs")
    for index, media, sound, family in CLIPS:
        _require(bank.media_entry(index=index).media_id == media, f"DIDX #{index} differs")
        _require(hirc.object_body(se.HIRC_SOUND, sound) ==
                 standard_voice_sound_body(sound, media, direct_parent_id=CONTAINERS[family]),
                 f"voice Sound {sound} differs")
        _require(positions[sound] < positions[CONTAINERS[family]] < positions[PLAY_ACTIONS[family]],
                 "Sound, Container and Play order differs")
    for container, expected in zip(CONTAINERS, CONTAINER_BODY_SHA256S, strict=True):
        body = hirc.object_body(se.HIRC_RANDOM_SEQUENCE_CONTAINER, container)
        _require(hashlib.sha256(body).hexdigest() == expected,
                 f"Container {container} playlist, parent or pitch differs")
