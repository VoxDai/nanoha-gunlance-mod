"""Build hm_cm00_epvsp.nbnk from its mapping table."""

from __future__ import annotations

from .base import BankSpec, HircEditor, run_single_cli


def apply_settings(editor: HircEditor) -> None:
    """Keep the original HIRC; this Bank currently needs no node settings."""


SPEC = BankSpec(name="hm_cm00_epvsp", apply_settings=apply_settings)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(SPEC))
