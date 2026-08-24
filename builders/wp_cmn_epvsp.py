"""Build the sharpening-complete voice overlay SoundBank."""

from __future__ import annotations

from tools import soundbank_editor

from .base import MediaAddition, SoundBankBuildPlan, run_single_cli


EVENT_ID = 166_276_485
ORIGINAL_ACTION_ID = 579_012_432
DONOR_SOUND_ID = 890_667_980
DONOR_MEDIA_ID = 838_569_492
VOICE_MEDIA_ID = 2_791_080_207
VOICE_ACTION_ID = 487_645_987
VOICE_SOUND_ID = 84_645_870


def apply_edits(bank: soundbank_editor.SoundBankEditor) -> None:
    """Clone the reviewed donor topology and append one guarded Play Action."""

    bank.media_entry(media_id=VOICE_MEDIA_ID)
    editor = bank.hirc
    editor.clone_sound(
        DONOR_SOUND_ID,
        VOICE_SOUND_ID,
        VOICE_MEDIA_ID,
        expected_source_id=DONOR_MEDIA_ID,
        label="clone sharpening-complete donor Sound",
    )
    action = editor.create_play_action(VOICE_ACTION_ID, VOICE_SOUND_ID, bank.bank_id)
    editor.insert_object(
        soundbank_editor.HIRC_ACTION,
        VOICE_ACTION_ID,
        action[4:],
        before=(soundbank_editor.HIRC_EVENT, EVENT_ID),
        label="add sharpening-complete Play Action",
    )
    editor.append_event_action(
        EVENT_ID,
        VOICE_ACTION_ID,
        expected_actions=(ORIGINAL_ACTION_ID,),
        label="append sharpening-complete voice to Event",
    )


EXPECTED_SUMMARY = soundbank_editor.SoundBankEditSummary(
    replaced_media=(),
    added_media=((72, VOICE_MEDIA_ID),),
    hirc_changed_bytes=1,
    added_hirc_objects=(
        (soundbank_editor.HIRC_SOUND, VOICE_SOUND_ID),
        (soundbank_editor.HIRC_ACTION, VOICE_ACTION_ID),
    ),
    resized_hirc_objects=((soundbank_editor.HIRC_EVENT, EVENT_ID, 12, 16),),
    hirc_size_delta=78,
)


PLAN = SoundBankBuildPlan(
    name="wp_cmn_epvsp",
    design_ids=("wp_cmn_epvsp.sharpen",),
    source="original/nbnk/wp_cmn_epvsp.nbnk",
    target="sound/wwise/Windows/wp_cmn_epvsp.nbnk",
    expected_source_sha256=(
        "76b1bc422e3041fafc5cdb2cd671937d298bd9de86421cfc597df1a61998c3c8"
    ),
    expected_bank_id=1_149_256_632,
    media_additions=(
        MediaAddition(
            72,
            VOICE_MEDIA_ID,
            "audio/wp_cmn_epvsp/sharpen/"
            "raising_heart_charging_completed(movie_1st.raising_heart."
            "charging_completed.1).wav",
        ),
    ),
    apply_edits=apply_edits,
    expected_summary=EXPECTED_SUMMARY,
)


if __name__ == "__main__":
    raise SystemExit(run_single_cli(PLAN))
