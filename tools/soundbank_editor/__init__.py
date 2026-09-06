"""Public Python API for lossless MHW audio-format parsing and guarded editing.

Import from ``tools.soundbank_editor``; ``__all__`` defines the public surface.
See README.md for API navigation and examples, and the soundbank-workflow
skill for format principles, route analysis, and the artifact workflow.

Attributes:
    ALIGNMENT: Rebuilt DATA media alignment, 16 bytes.
    SUPPORTED_EDIT_VERSION: Wwise version for structural authoring, 120;
        individual low-level operations have their own version checks.
    SUPPORTED_LMT_VERSION: Accepted LMT version, 95.
    SUPPORTED_WWEV_VERSION: Accepted WWEV version, 19.
    HIRC_SOUND: Sound object type, 0x02.
    HIRC_ACTION: Action object type, 0x03.
    HIRC_EVENT: Event object type, 0x04.
    HIRC_RANDOM_SEQUENCE_CONTAINER: Random/Sequence object type, 0x05.
    HIRC_SWITCH_CONTAINER: Switch object type, 0x06.
    HIRC_ACTOR_MIXER: Actor-Mixer object type, 0x07.
    ACTION_STOP: Stop Action code, 0x0103.
    ACTION_PLAY: Play Action code, 0x0403.
    ACTION_PLAY_EVENT: PlayEvent Action code, 0x2103.
    EVENT_GROUP_HASHES: Mapping from unsigned timeline hashes to
        EventGroup00 through EventGroup10 names.
    REQUEST_SLOT_HASHES: Ordered transform hashes for ReqNo slots A-H.
    SLOT_NAMES: String ``ABCDEFGH`` in low trigger-bit order.
    TRIGGER_HASH: Unsigned mTrigger transform hash, 2575924291.
    EditSummary: Compatibility alias of SoundBankEditSummary.

Notes:
    Parsed files and reports are immutable data objects; HIRC query objects
    are detached mutable copies. Editors accumulate changes in memory.
    Library errors derive from EditorError, while filesystem errors may
    propagate as OSError. No generic deletion operation is exported.
"""

from .errors import EditorError, LmtError, SoundBankError, WwevError
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
from .lmt import (
    EVENT_GROUP_HASHES,
    REQUEST_SLOT_HASHES,
    SLOT_NAMES,
    SUPPORTED_LMT_VERSION,
    TRIGGER_HASH,
    LmtAction,
    LmtEditSummary,
    LmtEditor,
    LmtFile,
    LmtRequestEdit,
    TimlKeyframe,
    TimlTransform,
    TimlType,
    TriggeredRequest,
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
from .wwev import (
    SUPPORTED_WWEV_VERSION,
    WwevEditSummary,
    WwevEditor,
    WwevFile,
    WwevRecord,
    WwevRecordEdit,
)

__all__ = (
    "ACTION_PLAY",
    "ACTION_PLAY_EVENT",
    "ACTION_STOP",
    "ALIGNMENT",
    "EditorError",
    "EVENT_GROUP_HASHES",
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
    "LmtAction",
    "LmtEditSummary",
    "LmtEditor",
    "LmtError",
    "LmtFile",
    "LmtRequestEdit",
    "MediaEntry",
    "REQUEST_SLOT_HASHES",
    "SLOT_NAMES",
    "SUPPORTED_LMT_VERSION",
    "SUPPORTED_WWEV_VERSION",
    "SoundBank",
    "SoundBankDiff",
    "SoundBankEditor",
    "SoundBankEditSummary",
    "SoundBankError",
    "SwitchContainerTopology",
    "SwitchNodeParams",
    "TRIGGER_HASH",
    "TimlKeyframe",
    "TimlTransform",
    "TimlType",
    "TriggeredRequest",
    "WwevEditSummary",
    "WwevEditor",
    "WwevError",
    "WwevFile",
    "WwevRecord",
    "WwevRecordEdit",
    "validate_external_stop_references",
    "validate_wem",
    "wwise_fnv1",
)
