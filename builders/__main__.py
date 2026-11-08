"""Build the complete registered design-driven release."""

from __future__ import annotations

from .base import ModBuildPlan, run_all_cli
from .clutch_weapon_attack_routes import VALIDATOR as CLUTCH_WEAPON_ATTACK_VALIDATOR
from .hm_cm00_epvsp import PLAN as HM_CM00_EPVSP
from .hm_wp07_epvsp import PLAN as HM_WP07_EPVSP
from .hm_wp07_epvsp_snd_ev import PLAN as HM_WP07_EPVSP_SND_EV
from .hm_wp07_snd_ev import PLAN as HM_WP07_SND_EV
from .integration import (
    CHARGED_SHELLING_VALIDATOR,
    OVERHEAD_SMASH_VALIDATOR,
    STATIONARY_DRAW_VALIDATOR,
    WIDE_SWEEP_VALIDATOR,
    WYR_STAKE_VALIDATOR,
    WYVERNS_FIRE_VALIDATOR,
)
from .pl_wp_par_op_event_structure import PLAN as PL_WP_PAR_OP_EVENT_STRUCTURE
from .pl_prop_cmn import PLAN as PL_PROP_CMN
from .pl_voice import PLAN as PL_VOICE
from .w07_00 import PLAN as W07_00
from .wp07_gun_epvsp_shell import PLAN as WP07_GUN_EPVSP_SHELL
from .wp_cmn_epvsp import PLAN as WP_CMN_EPVSP
from .wp_gun_cmn import PLAN as WP_GUN_CMN


ARTIFACT_PLANS = (
    WP07_GUN_EPVSP_SHELL,
    WP_CMN_EPVSP,
    WP_GUN_CMN,
    PL_WP_PAR_OP_EVENT_STRUCTURE,
    HM_CM00_EPVSP,
    W07_00,
    HM_WP07_SND_EV,
    PL_PROP_CMN,
    PL_VOICE,
    HM_WP07_EPVSP,
    HM_WP07_EPVSP_SND_EV,
)

# Kept as a small import compatibility alias for project-side callers.
PLANS = ARTIFACT_PLANS

MOD_PLAN = ModBuildPlan(
    artifacts=ARTIFACT_PLANS,
    validators=(
        STATIONARY_DRAW_VALIDATOR,
        OVERHEAD_SMASH_VALIDATOR,
        WIDE_SWEEP_VALIDATOR,
        CHARGED_SHELLING_VALIDATOR,
        WYR_STAKE_VALIDATOR,
        WYVERNS_FIRE_VALIDATOR,
        CLUTCH_WEAPON_ATTACK_VALIDATOR,
    ),
)


if __name__ == "__main__":
    raise SystemExit(run_all_cli(MOD_PLAN))
