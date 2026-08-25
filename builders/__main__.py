"""Build the complete six-artifact design-driven release."""

from __future__ import annotations

from .base import ModBuildPlan, run_all_cli
from .hm_cm00_epvsp import PLAN as HM_CM00_EPVSP
from .hm_wp07_snd_ev import PLAN as HM_WP07_SND_EV
from .integration import STATIONARY_DRAW_VALIDATOR
from .w07_00 import PLAN as W07_00
from .wp07_gun_epvsp_shell import PLAN as WP07_GUN_EPVSP_SHELL
from .wp_cmn_epvsp import PLAN as WP_CMN_EPVSP
from .wp_gun_cmn import PLAN as WP_GUN_CMN


ARTIFACT_PLANS = (
    WP07_GUN_EPVSP_SHELL,
    WP_CMN_EPVSP,
    WP_GUN_CMN,
    HM_CM00_EPVSP,
    W07_00,
    HM_WP07_SND_EV,
)

# Kept as a small import compatibility alias for project-side callers.
PLANS = ARTIFACT_PLANS

MOD_PLAN = ModBuildPlan(
    artifacts=ARTIFACT_PLANS,
    validators=(STATIONARY_DRAW_VALIDATOR,),
)


if __name__ == "__main__":
    raise SystemExit(run_all_cli(MOD_PLAN))
