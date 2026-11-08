"""Route only the verified Wyvern's Fire EPVSP start to its private request."""

from tools.soundbank_editor import EpvspEditor, EpvspStartEdit

from .base import EpvspBuildPlan, run_single_cli
from .wyverns_fire_routes import DESIGN_ID, EPVSP_NEW_ROW, EPVSP_OLD_ROW, NEW_REQUEST


def apply_edits(editor: EpvspEditor) -> None:
    editor.replace_start_request(0, expected=EPVSP_OLD_ROW, new_request=NEW_REQUEST)


PLAN = EpvspBuildPlan(
    name="hm_wp07_epvsp",
    design_ids=(DESIGN_ID,),
    source="original/epvsp/hm_wp07.epvsp",
    target="wp/gun/sound/hm_wp07.epvsp",
    expected_source_sha256="befb83e2d078777763446dc5f4585f02e2ca5cf2b0d9592aceb988c577e80adf",
    apply_edits=apply_edits,
    expected_summary=(EpvspStartEdit(0, EPVSP_OLD_ROW, EPVSP_NEW_ROW),),
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
