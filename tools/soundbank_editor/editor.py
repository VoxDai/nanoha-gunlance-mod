"""Backward-compatible imports for the former monolithic editor module.

New code should import public symbols from :mod:`tools.soundbank_editor`.
"""

from .errors import SoundBankError
from .hirc import (
    ACTION_PLAY,
    ACTION_PLAY_EVENT,
    ACTION_STOP,
    HIRC_ACTION,
    HIRC_ACTOR_MIXER,
    HIRC_EVENT,
    HIRC_RANDOM_SEQUENCE_CONTAINER,
    HIRC_SOUND,
    HIRC_SWITCH_CONTAINER,
    SUPPORTED_EDIT_VERSION,
    HircEditor,
    HircObject,
    HircPitchSettings,
    SwitchContainerTopology,
    SwitchNodeParams,
)
from .soundbank import (
    ALIGNMENT,
    Chunk,
    EditSummary,
    MediaEntry,
    SoundBank,
    SoundBankDiff,
    SoundBankEditor,
    SoundBankEditSummary,
    validate_wem,
    wwise_fnv1,
)


__all__ = (
    "ACTION_PLAY",
    "ACTION_PLAY_EVENT",
    "ACTION_STOP",
    "ALIGNMENT",
    "HIRC_ACTION",
    "HIRC_ACTOR_MIXER",
    "HIRC_EVENT",
    "HIRC_RANDOM_SEQUENCE_CONTAINER",
    "HIRC_SOUND",
    "HIRC_SWITCH_CONTAINER",
    "SUPPORTED_EDIT_VERSION",
    "Chunk",
    "EditSummary",
    "HircEditor",
    "HircObject",
    "HircPitchSettings",
    "MediaEntry",
    "SoundBank",
    "SoundBankDiff",
    "SoundBankEditor",
    "SoundBankEditSummary",
    "SoundBankError",
    "SwitchContainerTopology",
    "SwitchNodeParams",
    "validate_wem",
    "wwise_fnv1",
)
