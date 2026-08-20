"""Safe parsing and editing for Monster Hunter: World Wwise SoundBanks."""

from .editor import (
    ALIGNMENT,
    HIRC_ACTION,
    HIRC_EVENT,
    HIRC_RANDOM_SEQUENCE_CONTAINER,
    HIRC_SOUND,
    SUPPORTED_EDIT_VERSION,
    Chunk,
    EditSummary,
    HircEditor,
    HircObject,
    MediaEntry,
    SoundBank,
    SoundBankDiff,
    SoundBankEditor,
    SoundBankError,
    validate_wem,
    wwise_fnv1,
)

__all__ = (
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
    "SoundBankError",
    "validate_wem",
    "wwise_fnv1",
)

