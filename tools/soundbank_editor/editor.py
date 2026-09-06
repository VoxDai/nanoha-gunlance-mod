"""Compatibility imports for the former monolithic SoundBank editor module.

Notes:
    New code should import from ``tools.soundbank_editor``. These names
    reference the same implementations and constants, including the
    EditSummary alias; this module defines no separate editing behavior.
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
    ExternalStopReference,
    MediaEntry,
    SoundBank,
    SoundBankDiff,
    SoundBankEditor,
    SoundBankEditSummary,
    validate_external_stop_references,
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
    "ExternalStopReference",
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
    "validate_external_stop_references",
    "validate_wem",
    "wwise_fnv1",
)
