"""Build every registered project SoundBank."""

from __future__ import annotations

from .base import run_all_cli
from .cm_hitmark_epvsp import SPEC as CM_HITMARK_EPVSP
from .hm_cm00_epvsp import SPEC as HM_CM00_EPVSP
from .pl_prop_cmn import SPEC as PL_PROP_CMN
from .wp07_gun_epvsp_shell import SPEC as WP07_GUN_EPVSP_SHELL
from .wp_cmn_epvsp import SPEC as WP_CMN_EPVSP
from .wp_gun_cmn import SPEC as WP_GUN_CMN


SPECS = (
    CM_HITMARK_EPVSP,
    HM_CM00_EPVSP,
    PL_PROP_CMN,
    WP07_GUN_EPVSP_SHELL,
    WP_CMN_EPVSP,
    WP_GUN_CMN,
)


if __name__ == "__main__":
    raise SystemExit(run_all_cli(SPECS))
