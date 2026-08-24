"""Public exception hierarchy for binary format editors."""


class EditorError(Exception):
    """Base class for user-actionable parsing and editing failures."""


class SoundBankError(EditorError):
    """A SoundBank parsing or editing failure."""


class LmtError(EditorError):
    """An LMT/TIML parsing or editing failure."""


class WwevError(EditorError):
    """A WWEV parsing or editing failure."""
