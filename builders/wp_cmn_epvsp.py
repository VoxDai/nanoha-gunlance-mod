"""Build wp_cmn_epvsp.nbnk from its mapping table."""

from __future__ import annotations

from tools import soundbank_editor

from .base import BankBuildPlan, run_single_cli


def apply_edits(editor: soundbank_editor.SoundBankEditor) -> None:
    """Keep the original HIRC; this Bank currently needs no node settings."""


PLAN = BankBuildPlan(name="wp_cmn_epvsp", apply_edits=apply_edits)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
