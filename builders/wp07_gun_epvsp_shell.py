"""Build the full-burst and Wyvern's Fire voice routes in one SoundBank."""

from __future__ import annotations

from dataclasses import dataclass

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli


FULL_BURST_MEDIA_ID = 242_768_048
STARLIGHT_MEDIA_ID = 322_318_543
STARLIGHT_BREAKER_MEDIA_ID = 3_332_910_283
BREAKER_MEDIA_ID = 2_217_266_443
POSITIONING_VECTOR_OFFSET = 0x2A


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
    local_2d: bool = False


FULL_BURST_ROUTES = (
    OverlayRoute(
        "1-shell full burst",
        2_727_643_338,
        (449_657_149,),
        219_848_096,
        768_048_455,
        FULL_BURST_MEDIA_ID,
        3_386_055_930,
        960_803_121,
        True,
    ),
    OverlayRoute(
        "2-shell full burst",
        2_727_643_337,
        (646_158_903,),
        46_149_961,
        669_932_693,
        FULL_BURST_MEDIA_ID,
        4_199_321_359,
        479_969_098,
        True,
    ),
    OverlayRoute(
        "3-shell full burst",
        1_124_197_610,
        (19_077_629,),
        46_149_961,
        669_932_693,
        FULL_BURST_MEDIA_ID,
        4_100_049_135,
        2_544_331_946,
        True,
    ),
    OverlayRoute(
        "4-shell full burst",
        680_296_805,
        (223_369_281,),
        46_149_961,
        669_932_693,
        FULL_BURST_MEDIA_ID,
        4_272_498_343,
        4_251_385_954,
        True,
    ),
    OverlayRoute(
        "5-shell full burst",
        1_765_608_260,
        (403_102_539,),
        46_149_961,
        669_932_693,
        FULL_BURST_MEDIA_ID,
        3_047_212_046,
        1_519_403_237,
        True,
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
    OverlayRoute(
        "Wyvern explosion left Breaker",
        3_253_425_110,
        (120_830_402,),
        249_028_781,
        661_341_708,
        BREAKER_MEDIA_ID,
        2_807_447_016,
        3_070_096_299,
    ),
)


def _add_overlay(
    bank: soundbank_editor.SoundBankEditor, route: OverlayRoute
) -> None:
    editor = bank.hirc
    bank.media_entry(media_id=route.media_id)
    editor.clone_sound(
        route.donor_sound_id,
        route.sound_id,
        route.media_id,
        expected_source_id=route.expected_donor_source_id,
        label=f"clone donor Sound for {route.label}",
    )
    if route.local_2d:
        editor.patch_u8(
            soundbank_editor.HIRC_SOUND,
            route.sound_id,
            POSITIONING_VECTOR_OFFSET,
            0xC0,
            0xC1,
            label=f"enable local 2D positioning for {route.label}",
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


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Apply the two reviewed designs in deterministic serialization order."""

    for route in (*FULL_BURST_ROUTES, *WYVERNS_FIRE_ROUTES):
        _add_overlay(bank, route)


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=(
        (43, FULL_BURST_MEDIA_ID),
        (44, STARLIGHT_MEDIA_ID),
        (45, STARLIGHT_BREAKER_MEDIA_ID),
        (46, BREAKER_MEDIA_ID),
    ),
    hirc_changed_bytes=14,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, 960_803_121),
        (soundbank_editor.HIRC_ACTION, 3_386_055_930),
        (soundbank_editor.HIRC_SOUND, 479_969_098),
        (soundbank_editor.HIRC_ACTION, 4_199_321_359),
        (soundbank_editor.HIRC_SOUND, 2_544_331_946),
        (soundbank_editor.HIRC_ACTION, 4_100_049_135),
        (soundbank_editor.HIRC_SOUND, 4_251_385_954),
        (soundbank_editor.HIRC_ACTION, 4_272_498_343),
        (soundbank_editor.HIRC_SOUND, 1_519_403_237),
        (soundbank_editor.HIRC_ACTION, 3_047_212_046),
        (soundbank_editor.HIRC_SOUND, 4_149_261_730),
        (soundbank_editor.HIRC_ACTION, 4_011_774_951),
        (soundbank_editor.HIRC_SOUND, 36_215_958),
        (soundbank_editor.HIRC_ACTION, 254_514_827),
        (soundbank_editor.HIRC_SOUND, 2_472_459_210),
        (soundbank_editor.HIRC_ACTION, 1_866_468_495),
        (soundbank_editor.HIRC_SOUND, 3_070_096_299),
        (soundbank_editor.HIRC_ACTION, 2_807_447_016),
    ),
    resized_hirc_objects=(
        (soundbank_editor.HIRC_EVENT, 302_768_804, 12, 20),
        (soundbank_editor.HIRC_EVENT, 680_296_805, 12, 16),
        (soundbank_editor.HIRC_EVENT, 1_124_197_610, 12, 16),
        (soundbank_editor.HIRC_EVENT, 1_765_608_260, 12, 16),
        (soundbank_editor.HIRC_EVENT, 2_727_643_337, 12, 16),
        (soundbank_editor.HIRC_EVENT, 2_727_643_338, 12, 16),
        (soundbank_editor.HIRC_EVENT, 3_253_425_110, 12, 16),
        (soundbank_editor.HIRC_EVENT, 3_655_102_100, 12, 16),
    ),
    hirc_size_delta=832,
)


PLAN = SoundBankBuildPlan(
    name="wp07_gun_epvsp_shell",
    design_ids=(
        "wp07_gun_epvsp_shell.full_burst",
        "wp07_gun_epvsp_shell.wyverns_fire",
    ),
    source="original/nbnk/wp07_gun_epvsp_shell.nbnk",
    target="sound/wwise/Windows/wp07_gun_epvsp_shell.nbnk",
    expected_source_sha256=(
        "41bb0136e89e8434d716caed9c37b399e44cd0cb057f3fa9ab706437696782a1"
    ),
    expected_bank_id=3_273_965_928,
    media_additions=(
        MediaAddition(
            43,
            FULL_BURST_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/full_burst/"
            "nanoha_shoot_01(battle_of_aces.attack_voice.attack_03.1).wav",
        ),
        MediaAddition(
            44,
            STARLIGHT_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/wyverns_fire/"
            "nanoha_starlight_01(gears_of_destiny.attack_voice.attack_06.1).wav",
        ),
        MediaAddition(
            45,
            STARLIGHT_BREAKER_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/wyverns_fire/"
            "raising_heart_starlight_breaker_01(movie_1st.raising_heart."
            "starlight_breaker.1).wav",
        ),
        MediaAddition(
            46,
            BREAKER_MEDIA_ID,
            "audio/wp07_gun_epvsp_shell/wyverns_fire/"
            "nanoha_breaker_01(gears_of_destiny.attack_voice.attack_06.2).wav",
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
