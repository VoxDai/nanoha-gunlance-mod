"""Append the private Wyvern's Fire charge request without changing native records."""

from tools.soundbank_editor import WwevEditor, WwevEditSummary, WwevRecordEdit

from .base import WwevBuildPlan, run_single_cli
from .wyverns_fire_routes import (
    CHARGE_EVENT, DESIGN_ID, DONOR_RECORD_SHA256, NEW_REQUEST, PRIVATE_EVENT,
)


def apply_edits(editor: WwevEditor) -> None:
    editor.append_cloned_record(
        donor_request=26501,
        expected_donor_event_id=CHARGE_EVENT,
        expected_donor_mode=-1,
        expected_donor_sha256=DONOR_RECORD_SHA256,
        new_request=NEW_REQUEST,
        new_event_id=PRIVATE_EVENT,
    )


PLAN = WwevBuildPlan(
    name="hm_wp07_epvsp_snd_ev",
    design_ids=(DESIGN_ID,),
    source="original/wwev/hm_wp07_epvsp_snd_ev.wwev",
    target="sound/pl/hm_wp07_epvsp_snd_ev.wwev",
    expected_source_sha256="777d84a431c3e12b18ab8d701f058ed1f187ead1888e8c625f4245a09ddf79a4",
    apply_edits=apply_edits,
    expected_summary=WwevEditSummary(
        26, 27, 129, (WwevRecordEdit(1, 26501, CHARGE_EVENT, 27, NEW_REQUEST, PRIVATE_EVENT, 129),)
    ),
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
