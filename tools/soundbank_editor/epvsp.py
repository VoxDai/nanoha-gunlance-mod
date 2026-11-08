"""Guarded editing of the request-only ESP v8 layout used by MHW weapons."""

from dataclasses import dataclass
from pathlib import Path
import struct

from .errors import EditorError

_HEADER = struct.Struct("<I4sII")
_ROW = struct.Struct("<iiiII")
_U32 = struct.Struct("<I")
RequestRow = tuple[int, int, int, int, int]


@dataclass(frozen=True)
class EpvspFile:
    """Parsed ESP v8 file with a WWCT path and no TriggerData rows."""

    header: bytes
    requests: tuple[RequestRow, ...]

    @classmethod
    def from_bytes(cls, data: bytes) -> "EpvspFile":
        if len(data) < _HEADER.size or _HEADER.unpack_from(data) != (
            0x18091001, b"ESP\0", 8, 0x45185BED
        ):
            raise EditorError("Expected ESP v8 with the WWCT path layout")
        end = data.find(b"\0", _HEADER.size)
        if end <= _HEADER.size or end + 9 > len(data):
            raise EditorError("Missing EPVSP WWCT path or record counts")
        start = end + 1
        count, = _U32.unpack_from(data, start)
        tail = start + _U32.size + count * _ROW.size
        if tail + _U32.size != len(data) or data[tail:] != bytes(4):
            raise EditorError("Unsupported EPVSP request layout or nonzero TriggerData")
        return cls(data[:start], tuple(_ROW.iter_unpack(data[start + 4:tail])))

    @classmethod
    def from_file(cls, path: Path) -> "EpvspFile":
        return cls.from_bytes(Path(path).read_bytes())

    def to_bytes(self) -> bytes:
        return (self.header + _U32.pack(len(self.requests))
                + b"".join(_ROW.pack(*r) for r in self.requests) + bytes(4))


@dataclass(frozen=True)
class EpvspStartEdit:
    """One explicitly guarded, zero-based request-row replacement."""

    row: int
    old: RequestRow
    new: RequestRow


class EpvspEditor:
    """Replace only a uniquely identified row's mReqID."""

    def __init__(self, original: EpvspFile):
        self.original = original
        self._requests = list(original.requests)
        self._edits: list[EpvspStartEdit] = []

    @property
    def summary(self) -> tuple[EpvspStartEdit, ...]:
        return tuple(self._edits)

    def replace_start_request(self, row: int, *, expected: RequestRow, new_request: int) -> None:
        if type(row) is not int or not 0 <= row < len(self._requests):
            raise EditorError("EPVSP row out of range")
        if self._requests[row] != expected or self._requests.count(expected) != 1:
            raise EditorError("EPVSP request row guard failed or is ambiguous")
        if type(new_request) is not int or not 1 <= new_request <= 0x7FFF:
            raise EditorError("EPVSP start request must be a positive signed-16 WWEV request")
        if any(new_request in r[1:3] for r in self._requests):
            raise EditorError("EPVSP replacement request already in use")
        new = (expected[0], new_request, *expected[2:])
        self._requests[row] = new
        self._edits.append(EpvspStartEdit(row, expected, new))

    def validate(self) -> EpvspFile:
        expected = list(self.original.requests)
        for edit in self._edits:
            if expected[edit.row] != edit.old or edit.old[0:1] + edit.old[2:] != edit.new[0:1] + edit.new[2:]:
                raise EditorError("EPVSP contains an undeclared change")
            expected[edit.row] = edit.new
        candidate = EpvspFile(self.original.header, tuple(self._requests))
        rebuilt = EpvspFile.from_bytes(candidate.to_bytes())
        if rebuilt.header != self.original.header or rebuilt.requests != tuple(expected):
            raise EditorError("EPVSP read-back differs from declared edits")
        return rebuilt
