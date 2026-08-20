"""Build wp07_gun_epvsp_shell.nbnk with full-burst mix corrections."""

from __future__ import annotations

from tools import soundbank_editor

from .base import BankBuildPlan, BuildError, run_single_cli


HIRC_SOUND = 0x02
HIRC_RANDOM_SEQUENCE_CONTAINER = 0x05
FULL_BURST_AUX_BUS = 3015692424


def _disable_populated_aux(
    editor: soundbank_editor.HircEditor,
    sound_id: int,
    flag_offset: int,
    bus_offset: int,
) -> None:
    """Override User Aux Sends and clear the populated reverb bus."""

    editor.patch_u8(
        HIRC_SOUND,
        sound_id,
        flag_offset,
        0x0A,
        0x0D,
        label=f"disable full-burst Aux on Sound {sound_id}",
    )
    editor.patch_u32(
        HIRC_SOUND,
        sound_id,
        bus_offset,
        FULL_BURST_AUX_BUS,
        0,
        label=f"clear full-burst Aux Bus on Sound {sound_id}",
    )


def _disable_empty_aux(
    editor: soundbank_editor.HircEditor, sound_id: int, flag_offset: int
) -> None:
    """Override inherited User Aux Sends on a node with no local Aux Bus array."""

    editor.patch_u8(
        HIRC_SOUND,
        sound_id,
        flag_offset,
        0x00,
        0x05,
        label=f"disable inherited full-burst Aux on Sound {sound_id}",
    )


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Apply the full-burst HIRC settings verified in game.

    A Media ID is not a unique playback path in this Bank. Three, four, and
    five-shell full bursts each use two Event -> Container -> Sound routes:

    * 3 shells: Event 1124197610 -> Container 246916390 -> Sound 641882349,
      and Event 719268880 -> Container 951826648 -> Sound 467996314.
    * 4 shells: Event 680296805 -> Container 505597934 -> Sound 68448090,
      and Event 678619471 -> Container 357463510 -> Sound 862816411.
    * 5 shells: Event 1765608260 -> Container 885313651 -> Sound 994484287,
      and Event 2432475814 -> Container 634598513 -> Sound 196455745.

    Muting one side removed the surround effect but biased the right channel.
    The working mix therefore keeps both routes, removes the -50-cent detune,
    disables the reverb Aux path, and adjusts both sides symmetrically.
    """

    editor = bank.hirc

    # One-shell (Sound 219848096 / Media 768048455) and two-shell
    # (Sound 46149961 / Media 669932693) use one populated Aux route each.
    # The populated routes for 3/4/5 shells use the same reverb bus.
    populated_aux_nodes = (
        (46149961, 0x2B, 0x2C),
        (219848096, 0x2B, 0x2C),
        (641882349, 0x30, 0x31),
        (68448090, 0x30, 0x31),
        (196455745, 0x2B, 0x2C),
        (994484287, 0x2B, 0x2C),
    )
    for sound_id, flag_offset, bus_offset in populated_aux_nodes:
        _disable_populated_aux(editor, sound_id, flag_offset, bus_offset)

    # The second 3-shell and 4-shell Sound objects have no local Aux array, but
    # must explicitly override inherited sends to prevent the same reverb path.
    _disable_empty_aux(editor, 862816411, 0x26)
    _disable_empty_aux(editor, 467996314, 0x26)

    # Preserve both spatial paths while matching their pitch. Only one branch
    # of each 3/4/5-shell pair carried the original -50-cent detune.
    editor.patch_float(
        HIRC_RANDOM_SEQUENCE_CONTAINER,
        246916390,
        0x17,
        -50.0,
        0.0,
        label="normalize 3-shell paired-path Pitch",
    )
    editor.patch_float(
        HIRC_RANDOM_SEQUENCE_CONTAINER,
        505597934,
        0x12,
        -50.0,
        0.0,
        label="normalize 4-shell paired-path Pitch",
    )
    editor.patch_float(
        HIRC_RANDOM_SEQUENCE_CONTAINER,
        885313651,
        0x12,
        -50.0,
        0.0,
        label="normalize 5-shell paired-path Pitch",
    )

    # Lower both active routes for 3 and 4 shells by exactly 1.5 dB.
    for sound_id, volume_offset in (
        (641882349, 0x22),
        (467996314, 0x20),
        (68448090, 0x22),
        (862816411, 0x20),
    ):
        editor.patch_float(
            HIRC_SOUND,
            sound_id,
            volume_offset,
            -5.0,
            -6.5,
            label=f"lower full-burst Volume on Sound {sound_id}",
        )

    # The two 5-shell Sound property bundles originally contained only
    # CenterPCT=100 and GameAuxSendVolume=-6. With Aux disabled, reuse that
    # fixed-size two-property layout as Volume=-1.5 and CenterPCT=100. Property
    # IDs are stored first, followed by their float values.
    for sound_id in (196455745, 994484287):
        editor.patch_u8(
            HIRC_SOUND,
            sound_id,
            0x1F,
            0x0E,
            0x00,
            label=f"add 5-shell Volume property on Sound {sound_id}",
        )
        editor.patch_u8(
            HIRC_SOUND,
            sound_id,
            0x20,
            0x17,
            0x0E,
            label=f"retain 5-shell CenterPCT property on Sound {sound_id}",
        )
        editor.patch_float(
            HIRC_SOUND,
            sound_id,
            0x21,
            100.0,
            -1.5,
            label=f"set 5-shell Volume on Sound {sound_id}",
        )
        editor.patch_float(
            HIRC_SOUND,
            sound_id,
            0x25,
            -6.0,
            100.0,
            label=f"move 5-shell CenterPCT value on Sound {sound_id}",
        )

    # This count is a compact guard against accidentally dropping or widening
    # one of the reviewed field edits while refactoring this builder.
    if editor.changed_byte_count != 54:
        raise BuildError(
            "wp07_gun_epvsp_shell: expected 54 changed HIRC bytes, "
            f"found {editor.changed_byte_count}"
        )


PLAN = BankBuildPlan(name="wp07_gun_epvsp_shell", apply_edits=apply_edits)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
