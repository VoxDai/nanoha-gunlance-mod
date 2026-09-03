"""Public exception hierarchy for format parsing, guards, and validation.

Notes:
    Catch EditorError to handle Library-defined failures across formats.
    This hierarchy does not wrap ordinary filesystem OSError exceptions or
    every invalid Python argument type accepted by an unvalidated code path.
"""


class EditorError(Exception):
    """Base exception for Library-defined parsing and editing failures."""


class SoundBankError(EditorError):
    """NBNK, HIRC, WEM, or Wwise ID validation failure."""


class LmtError(EditorError):
    """LMT/TIML parsing, request guard, or read-back validation failure."""


class WwevError(EditorError):
    """WWEV parsing, record guard, or read-back validation failure."""
