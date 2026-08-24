"""Backward-compatible imports for the former monolithic editor module.

New code should import public symbols from :mod:`tools.soundbank_editor`.
"""

from .errors import SoundBankError
from .hirc import (
    ACTION_PLAY,
    ACTION_PLAY_EVENT,
    HIRC_ACTION,
    HIRC_EVENT,
    HIRC_RANDOM_SEQUENCE_CONTAINER,
    HIRC_SOUND,
    SUPPORTED_EDIT_VERSION,
    HircEditor,
    HircObject,
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
    "ALIGNMENT",
    "HIRC_ACTION",
    "HIRC_EVENT",
    "HIRC_RANDOM_SEQUENCE_CONTAINER",
    "HIRC_SOUND",
    "SUPPORTED_EDIT_VERSION",
    "Chunk",
    "EditSummary",
    "HircEditor",
    "HircObject",
    "MediaEntry",
    "SoundBank",
    "SoundBankDiff",
    "SoundBankEditor",
    "SoundBankEditSummary",
    "SoundBankError",
    "validate_wem",
    "wwise_fnv1",
)
