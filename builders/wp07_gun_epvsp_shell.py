"""Build wp07_gun_epvsp_shell.nbnk with full-burst voice overlays."""

from __future__ import annotations

from dataclasses import dataclass

from tools import soundbank_editor

from .base import BankBuildPlan, BuildError, MappingMediaOverlay, run_single_cli


FULL_BURST_OVERLAY_MEDIA_ID = 242768048
FULL_BURST_MAPPING_INDICES = (2, 9, 15, 30, 34)
POSITIONING_VECTOR_OFFSET = 0x2A


@dataclass(frozen=True)
class FullBurstOverlayRoute:
    """One Event that receives a single additional Play Action and Sound."""

    shells: int
    event_id: int
    expected_action_id: int
    donor_sound_id: int
    expected_donor_source_id: int
    action_id: int
    sound_id: int


FULL_BURST_OVERLAY_ROUTES = (
    FullBurstOverlayRoute(
        1,
        2727643338,
        449657149,
        219848096,
        768048455,
        3386055930,
        960803121,
    ),
    FullBurstOverlayRoute(
        2,
        2727643337,
        646158903,
        46149961,
        669932693,
        4199321359,
        479969098,
    ),
    FullBurstOverlayRoute(
        3,
        1124197610,
        19077629,
        46149961,
        669932693,
        4100049135,
        2544331946,
    ),
    FullBurstOverlayRoute(
        4,
        680296805,
        223369281,
        46149961,
        669932693,
        4272498343,
        4251385954,
    ),
    FullBurstOverlayRoute(
        5,
        1765608260,
        403102539,
        46149961,
        669932693,
        3047212046,
        1519403237,
    ),
)


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Add one locally positioned voice overlay for each full-burst shell count.

    The original full-burst media, Sounds, Containers, Actions, and paired
    spatial routes remain unchanged. Three, four, and five shells use only one
    of their paired Events for the overlay, preventing duplicate voice playback.
    Their new Sounds clone the in-game-verified balanced two-shell topology.
    """

    bank.media_entry(media_id=FULL_BURST_OVERLAY_MEDIA_ID)
    editor = bank.hirc
    expected_added: list[tuple[int, int]] = []

    for route in FULL_BURST_OVERLAY_ROUTES:
        editor.clone_sound(
            route.donor_sound_id,
            route.sound_id,
            FULL_BURST_OVERLAY_MEDIA_ID,
            expected_source_id=route.expected_donor_source_id,
            label=(
                f"clone balanced donor Sound {route.donor_sound_id} for "
                f"{route.shells}-shell overlay"
            ),
        )
        expected_added.append((soundbank_editor.HIRC_SOUND, route.sound_id))
        editor.patch_u8(
            soundbank_editor.HIRC_SOUND,
            route.sound_id,
            POSITIONING_VECTOR_OFFSET,
            0xC0,
            0xC1,
            label=(
                f"enable local 2D positioning override on {route.shells}-shell "
                f"Sound {route.sound_id}"
            ),
        )
        action = editor.create_play_action(route.action_id, route.sound_id, bank.bank_id)
        editor.insert_object(
            soundbank_editor.HIRC_ACTION,
            route.action_id,
            action[4:],
            before=(soundbank_editor.HIRC_EVENT, route.event_id),
            label=(
                f"add {route.shells}-shell overlay Play Action {route.action_id}"
            ),
        )
        expected_added.append((soundbank_editor.HIRC_ACTION, route.action_id))
        editor.append_event_action(
            route.event_id,
            route.action_id,
            expected_actions=(route.expected_action_id,),
            label=(
                f"append {route.shells}-shell overlay to Event {route.event_id}"
            ),
        )

    if editor.changed_byte_count != 10:
        raise BuildError(
            "wp07_gun_epvsp_shell: expected 10 changed HIRC bytes, "
            f"found {editor.changed_byte_count}"
        )
    if editor.added_objects != tuple(expected_added):
        raise BuildError(
            "wp07_gun_epvsp_shell: added HIRC objects differ from the reviewed plan"
        )
    expected_resized = {
        (soundbank_editor.HIRC_EVENT, route.event_id, 12, 16)
        for route in FULL_BURST_OVERLAY_ROUTES
    }
    if set(editor.resized_objects) != expected_resized:
        raise BuildError(
            "wp07_gun_epvsp_shell: resized Events differ from the reviewed plan"
        )
    size_delta = len(editor.build()) - len(bank.original.hirc_payload)
    if size_delta != 520:
        raise BuildError(
            "wp07_gun_epvsp_shell: expected HIRC size delta +520, "
            f"found {size_delta:+d}"
        )


PLAN = BankBuildPlan(
    name="wp07_gun_epvsp_shell",
    apply_edits=apply_edits,
    media_overlays=(
        MappingMediaOverlay(
            indices=FULL_BURST_MAPPING_INDICES,
            media_id=FULL_BURST_OVERLAY_MEDIA_ID,
        ),
    ),
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
