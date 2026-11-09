"""Build reviewed isolated weapon-sound requests, preserving native routes."""

from __future__ import annotations

from tools import soundbank_editor

from . import clutch_weapon_attack_routes as clutch
from .base import WwevBuildPlan, run_single_cli


DONOR_REQUEST = 6470
DONOR_EVENT_ID = 3_567_942_167
DONOR_MODE = 2
DONOR_RECORD_SHA256 = (
    "1c6fd120501ce70925b00d8ab0166a38b132934e220a1095506424024a33e53f"
)
NEW_REQUEST = 6592
NEW_EVENT_ID = 3_176_129_810

OVERHEAD_ORIGINAL_REQUEST = 6505
OVERHEAD_ORIGINAL_EVENT_ID = 1_129_041_389
OVERHEAD_ORIGINAL_MODE = 100
OVERHEAD_ORIGINAL_RECORD_SHA256 = (
    "716e10c4bb841822f8d5b178580980d654f4367e5753403474bc8b50cfb7f2c8"
)

WIDE_SWEEP_DONOR_REQUEST = 6486
WIDE_SWEEP_DONOR_EVENT_ID = 2_467_230_206
WIDE_SWEEP_DONOR_MODE = 100
WIDE_SWEEP_DONOR_RECORD_SHA256 = (
    "7acef10768c67f1bd791873f65a0c345e00c9e24c50428e4c5ad2cae4bbabbfb"
)
WIDE_SWEEP_NEW_REQUEST = 6596
WIDE_SWEEP_NEW_EVENT_ID = 4_096_779_774
WIDE_SWEEP_NEW_RECORD_SHA256 = (
    "d4a45c5e6c512f1b9688decbe9ad966e606a5674b7307ad469e6a8c60a9b8637"
)

CHARGED_SHELLING_DONOR_REQUEST = DONOR_REQUEST
CHARGED_SHELLING_DONOR_EVENT_ID = DONOR_EVENT_ID
CHARGED_SHELLING_DONOR_MODE = DONOR_MODE
CHARGED_SHELLING_DONOR_RECORD_SHA256 = DONOR_RECORD_SHA256
CHARGED_SHELLING_NEW_REQUEST = 6599
CHARGED_SHELLING_NEW_EVENT_ID = 3_452_820_647
CHARGED_SHELLING_NEW_RECORD_SHA256 = (
    "0b6c6e87c3c78c669ac6bc6cd09112c54445e7bce5401380fc68e2fad136e8ee"
)

WYR_STAKE_ROUTES = (
    (6456, 2_798_914_977, 100,
     "0cd7f3f60ba152c1d3a4e0ed7cba9c0256734fb9175fd7bcfff06cd5ed3202d7",
     6610, 2_456_922_025),
    (6570, 1_517_840_452, 100,
     "031bca6cf48747ae66243e53702d31b824a8a4fe4f01f7d31a9a2ed6476057b1",
     6611, 4_272_667_772),
    (6525, 2_279_772_715, 200,
     "e60a91a79ea0e6c8488818862ab9ea9ade123cd9e8599668ec29b75fa0def7cb",
     6612, 3_413_751_962),
)
WYR_STAKE_NEW_RECORD_SHA256S = (
    "318a4299d8c16e1450dfa072e3cfd9080f2de1c45b5a610289209bcb8dccc2db",
    "94447d2580119dbb23821e040464b0e457b6e84eacabbc39ebb208dcea03f62a",
    "c473b030f54c3b11d63f1dac581dda3a524eeb0c412f62bded65539a7ed15ecf",
)


def apply_edits(editor: soundbank_editor.WwevEditor) -> None:
    """Clone reviewed weapon requests and preserve original records."""

    editor.append_cloned_record(
        donor_request=DONOR_REQUEST,
        expected_donor_event_id=DONOR_EVENT_ID,
        expected_donor_mode=DONOR_MODE,
        expected_donor_sha256=DONOR_RECORD_SHA256,
        new_request=NEW_REQUEST,
        new_event_id=NEW_EVENT_ID,
    )
    editor.append_cloned_record(
        donor_request=WIDE_SWEEP_DONOR_REQUEST,
        expected_donor_event_id=WIDE_SWEEP_DONOR_EVENT_ID,
        expected_donor_mode=WIDE_SWEEP_DONOR_MODE,
        expected_donor_sha256=WIDE_SWEEP_DONOR_RECORD_SHA256,
        new_request=WIDE_SWEEP_NEW_REQUEST,
        new_event_id=WIDE_SWEEP_NEW_EVENT_ID,
    )
    editor.append_cloned_record(
        donor_request=CHARGED_SHELLING_DONOR_REQUEST,
        expected_donor_event_id=CHARGED_SHELLING_DONOR_EVENT_ID,
        expected_donor_mode=CHARGED_SHELLING_DONOR_MODE,
        expected_donor_sha256=CHARGED_SHELLING_DONOR_RECORD_SHA256,
        new_request=CHARGED_SHELLING_NEW_REQUEST,
        new_event_id=CHARGED_SHELLING_NEW_EVENT_ID,
    )
    for donor_request, donor_event, mode, digest, new_request, new_event in WYR_STAKE_ROUTES:
        editor.append_cloned_record(
            donor_request=donor_request,
            expected_donor_event_id=donor_event,
            expected_donor_mode=mode,
            expected_donor_sha256=digest,
            new_request=new_request,
            new_event_id=new_event,
        )

    (charge,) = clutch.WRAPPERS
    editor.append_cloned_record(
        donor_request=charge.edit.donor_request,
        expected_donor_event_id=charge.edit.donor_event_id,
        expected_donor_mode=2,
        expected_donor_sha256=charge.donor_sha256,
        new_request=charge.edit.new_request,
        new_event_id=charge.edit.new_event_id,
    )



EXPECTED_SUMMARY = soundbank_editor.WwevEditSummary(
    record_count_before=43,
    record_count_after=50,
    appended_size=903,
    edits=(
        soundbank_editor.WwevRecordEdit(
            donor_record_index=17,
            donor_request=DONOR_REQUEST,
            donor_event_id=DONOR_EVENT_ID,
            added_record_index=44,
            new_request=NEW_REQUEST,
            new_event_id=NEW_EVENT_ID,
            appended_size=129,
        ),
        soundbank_editor.WwevRecordEdit(
            donor_record_index=22,
            donor_request=WIDE_SWEEP_DONOR_REQUEST,
            donor_event_id=WIDE_SWEEP_DONOR_EVENT_ID,
            added_record_index=45,
            new_request=WIDE_SWEEP_NEW_REQUEST,
            new_event_id=WIDE_SWEEP_NEW_EVENT_ID,
            appended_size=129,
        ),
        soundbank_editor.WwevRecordEdit(
            donor_record_index=17,
            donor_request=CHARGED_SHELLING_DONOR_REQUEST,
            donor_event_id=CHARGED_SHELLING_DONOR_EVENT_ID,
            added_record_index=46,
            new_request=CHARGED_SHELLING_NEW_REQUEST,
            new_event_id=CHARGED_SHELLING_NEW_EVENT_ID,
            appended_size=129,
        ),
        soundbank_editor.WwevRecordEdit(13, 6456, 2_798_914_977, 47, 6610, 2_456_922_025, 129),
        soundbank_editor.WwevRecordEdit(38, 6570, 1_517_840_452, 48, 6611, 4_272_667_772, 129),
        soundbank_editor.WwevRecordEdit(10, 6525, 2_279_772_715, 49, 6612, 3_413_751_962, 129),
    ) + tuple(wrapper.edit for wrapper in clutch.WRAPPERS),
)


PLAN = WwevBuildPlan(
    name="hm_wp07_snd_ev",
    design_ids=(
        "wp_gun_cmn.stationary_draw",
        "wp_gun_cmn.overhead_smash",
        "wp_gun_cmn.wide_sweep",
        "wp07_gun_epvsp_shell.charged_shelling",
        "wp07_gun_epvsp_shell.wyrmstake_cannon",
        clutch.DESIGN_ID,
    ),
    source="original/wwev/hm_wp07_snd_ev.wwev",
    target="sound/pl/hm_wp07_snd_ev.wwev",
    expected_source_sha256=(
        "82c7162f3cb502e3ce3e1e7c1e6ff4823d373a764148d6d761f675420bcd2a0f"
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
