"""Lossless MHW WWEV v19 parsing and append-only guarded record cloning.

Notes:
    Public names are re-exported by tools.soundbank_editor. Record indices
    are one-based and offsets are absolute file byte positions. See README.md
    for API examples and soundbank-workflow for structure and route analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import struct

from ._binary import (
    check_positive_i16,
    check_unsigned,
    read_cstring,
    require_range,
    write_atomic as _write_atomic,
)
from .errors import WwevError


SUPPORTED_WWEV_VERSION = 19
WWEV_HEADER = struct.Struct("<4sIII")
WWEV_RECORD_FIXED = struct.Struct("<hhII116s")


def _check_u32(value: int, label: str) -> int:
    return check_unsigned(value, 32, label, WwevError)


def _check_i16(value: int, label: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not -0x8000 <= value <= 0x7FFF
    ):
        raise WwevError(f"{label} must be a signed 16-bit integer: {value!r}")
    return value


def _normalize_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise WwevError(f"{label} must be a 64-character SHA-256 digest")
    try:
        bytes.fromhex(value)
    except ValueError as error:
        raise WwevError(f"{label} must be a hexadecimal SHA-256 digest") from error
    return value.casefold()


@dataclass(frozen=True)
class WwevRecord:
    """Immutable complete variable-length WWEV request record.

    Attributes:
        index: 1-based serialized record position.
        offset: Absolute byte offset of the record in the WWEV.
        request_no: Stored signed-16 request number; not necessarily unique.
        mode: Stored signed-16 mode.
        event_id: Unsigned 32-bit Event ID.
        command_hash: Unsigned 32-bit command hash.
        unknown: Retained 116-byte unmodeled region.
        wwpc: Decoded UTF-8 WWPC string, excluding its terminator.
        raw: Complete serialized record, including the NUL string terminator.
    """

    index: int
    offset: int
    request_no: int
    mode: int
    event_id: int
    command_hash: int
    unknown: bytes
    wwpc: str
    raw: bytes = field(repr=False)

    @property
    def size(self) -> int:
        """Return the complete raw record length in bytes, including its terminator."""

        return len(self.raw)

    @property
    def sha256(self) -> str:
        """Return the lowercase SHA-256 hex digest of the complete raw record.

        Notes:
            Covers ReqNo, mode, Event ID, command hash, unknown bytes, WWPC, and
            terminator; neither file header/dependencies nor index/offset is included.
        """

        return hashlib.sha256(self.raw).hexdigest()


@dataclass(frozen=True)
class WwevFile:
    """Immutable WWEV v19 event list; use from_file() or from_bytes() to parse.

    Attributes:
        version: Accepted WWEV version, 19.
        unknown: Preserved unsigned header word.
        dependencies: Four decoded UTF-8 dependency strings, in input order.
        records: Complete request records in serialized order, including repeats.
        source_path: Resolved input filename for from_file(), otherwise None.

    Notes:
        The original payload is retained byte-for-byte. Direct dataclass
        construction bypasses parser validation.
    """

    version: int
    unknown: int
    dependencies: tuple[str, str, str, str]
    records: tuple[WwevRecord, ...]
    _payload: bytes = field(repr=False)
    source_path: Path | None = None

    @classmethod
    def from_file(cls, path: Path | str) -> WwevFile:
        """Read and parse a file, retaining its resolved path for output protection.

        Args:
            path: Path or string filename of the input artifact.

        Returns:
            Parsed WwevFile.

        Raises:
            WwevError: The path is not a file or format parsing fails.
            OSError: Reading the file or resolving its path fails.

        Notes:
            Does not modify the input. Editors reject writing to this resolved
            source_path even when output overwrite is enabled.
        """

        source = Path(path)
        if not source.is_file():
            raise WwevError(f"WWEV does not exist: {source}")
        parsed = cls.from_bytes(source.read_bytes())
        return cls(
            parsed.version,
            parsed.unknown,
            parsed.dependencies,
            parsed.records,
            parsed._payload,
            source.resolve(),
        )

    @classmethod
    def from_bytes(cls, payload: bytes) -> WwevFile:
        """Parse immutable input bytes without recording a source filename.

        Args:
            payload: Complete file as bytes; bytearray/memoryview are not accepted
                by the underlying parsed-file factory.

        Returns:
            Parsed WwevFile; source_path is None.

        Raises:
            WwevError: The input is not bytes or parsing checks fail.

        Notes:
            Checks WWEV v19 header, four UTF-8 dependencies, complete records, and absence of trailing data.
            No file I/O occurs; source-path overwrite protection is unavailable.
        """

        if not isinstance(payload, bytes):
            raise WwevError("WWEV input must be bytes")
        require_range(payload, 0, WWEV_HEADER.size, "WWEV header", WwevError)
        magic, version, record_count, unknown = WWEV_HEADER.unpack_from(payload)
        if magic != b"WWEV":
            raise WwevError(f"invalid WWEV magic: {magic!r}")
        if version != SUPPORTED_WWEV_VERSION:
            raise WwevError(
                f"unsupported WWEV version: {version}; "
                f"expected {SUPPORTED_WWEV_VERSION}"
            )

        cursor = WWEV_HEADER.size
        dependencies: list[str] = []
        for index in range(4):
            dependency, cursor = read_cstring(
                payload,
                cursor,
                f"WWEV dependency string #{index + 1}",
                WwevError,
            )
            dependencies.append(dependency)

        records: list[WwevRecord] = []
        for index in range(record_count):
            record_offset = cursor
            require_range(
                payload,
                cursor,
                WWEV_RECORD_FIXED.size,
                f"WWEV record #{index + 1}",
                WwevError,
            )
            request_no, mode, event_id, command_hash, unknown_record = (
                WWEV_RECORD_FIXED.unpack_from(payload, cursor)
            )
            cursor += WWEV_RECORD_FIXED.size
            wwpc, cursor = read_cstring(
                payload, cursor, f"WWEV WWPC #{index + 1}", WwevError
            )
            records.append(
                WwevRecord(
                    index=index + 1,
                    offset=record_offset,
                    request_no=request_no,
                    mode=mode,
                    event_id=event_id,
                    command_hash=command_hash,
                    unknown=unknown_record,
                    wwpc=wwpc,
                    raw=payload[record_offset:cursor],
                )
            )

        if cursor != len(payload):
            raise WwevError(
                f"WWEV has {len(payload) - cursor} unexpected trailing bytes "
                f"at 0x{cursor:X}"
            )
        return cls(
            version,
            unknown,
            tuple(dependencies),
            tuple(records),
            payload,
        )

    def to_bytes(self) -> bytes:
        """Return the complete original WWEV bytes without rebuilding, validation, or I/O."""

        return self._payload

    def records_for_request(self, request_no: int) -> tuple[WwevRecord, ...]:
        """Select every matching request from the original records.

        Args:
            request_no: Request number compared for equality; lookup adds no
                positive signed-16 range restriction.

        Returns:
            Immutable record tuple in serialization order; empty if absent.
            Repeated matches are retained rather than treated as an error.
        """

        return tuple(
            record for record in self.records if record.request_no == request_no
        )

    def record(self, request_no: int) -> WwevRecord:
        """Require a single original record for a request number.

        Args:
            request_no: Request number to look up, as for records_for_request().

        Returns:
            The matching immutable WwevRecord.

        Raises:
            WwevError: There are zero matches or multiple matches.
        """

        matches = self.records_for_request(request_no)
        if len(matches) != 1:
            raise WwevError(
                f"expected exactly one WWEV request {request_no}, found {len(matches)}"
            )
        return matches[0]


@dataclass(frozen=True)
class WwevRecordEdit:
    """Immutable bookkeeping for one donor-to-appended-record operation.

    Attributes:
        donor_record_index: 1-based donor position in the working WWEV.
        donor_request: Donor's request number.
        donor_event_id: Donor's Event ID.
        added_record_index: 1-based position of the appended record.
        new_request: Appended record's positive signed-16 request number.
        new_event_id: Appended record's unsigned-32 Event ID.
        appended_size: Complete appended byte length, including WWPC terminator.
    """

    donor_record_index: int
    donor_request: int
    donor_event_id: int
    added_record_index: int
    new_request: int
    new_event_id: int
    appended_size: int


@dataclass(frozen=True)
class WwevEditSummary:
    """Immutable append-only WWEV change report.

    Attributes:
        record_count_before: Original record count.
        record_count_after: Working count including pending clones.
        appended_size: Total serialized bytes appended, excluding header changes.
        edits: WwevRecordEdit records in append order.
    """

    record_count_before: int
    record_count_after: int
    appended_size: int
    edits: tuple[WwevRecordEdit, ...]


class WwevEditor:
    """In-memory, append-only editor for one parsed WWEV v19 file.

    Attributes:
        original: Immutable WwevFile retained for preservation/source-path checks.

    Notes:
        Existing records and dependencies are not editable through this API.
        Pending clones participate in subsequent lookups and collision checks.
    """

    def __init__(self, wwev: WwevFile):
        """Initialize working record and append lists without modifying the parsed file.

        Args:
            wwev: Parsed original WwevFile, retaining its source_path for write protection.
        """

        self.original = wwev
        self._appended: list[bytes] = []
        self._records: list[WwevRecord] = list(wwev.records)
        self._edits: list[WwevRecordEdit] = []

    @classmethod
    def from_file(cls, path: Path | str) -> WwevEditor:
        """Read and parse a file, retaining its resolved path for output protection.

        Args:
            path: Path or string filename of the input artifact.

        Returns:
            New WwevEditor containing a parsed original and independent working state.

        Raises:
            WwevError: The path is not a file or format parsing fails.
            OSError: Reading the file or resolving its path fails.

        Notes:
            Does not modify the input. Editors reject writing to this resolved
            source_path even when output overwrite is enabled.
        """

        return cls(WwevFile.from_file(path))

    @classmethod
    def from_bytes(cls, payload: bytes) -> WwevEditor:
        """Parse immutable input bytes without recording a source filename.

        Args:
            payload: Complete file as bytes; bytearray/memoryview are not accepted
                by the underlying parsed-file factory.

        Returns:
            New WwevEditor containing a parsed original and independent working state; source_path is None.

        Raises:
            WwevError: The input is not bytes or parsing checks fail.

        Notes:
            Checks WWEV v19 header, four UTF-8 dependencies, complete records, and absence of trailing data.
            No file I/O occurs; source-path overwrite protection is unavailable.
        """

        return cls(WwevFile.from_bytes(payload))

    def records_for_request(self, request_no: int) -> tuple[WwevRecord, ...]:
        """Select every matching request from the current records, including pending clones.

        Args:
            request_no: Request number compared for equality; lookup adds no
                positive signed-16 range restriction.

        Returns:
            Immutable record tuple in serialization order; empty if absent.
            Repeated matches are retained rather than treated as an error.
        """

        return tuple(
            record for record in self._records if record.request_no == request_no
        )

    def append_cloned_record(
        self,
        *,
        donor_request: int,
        expected_donor_event_id: int,
        expected_donor_mode: int,
        expected_donor_sha256: str,
        new_request: int,
        new_event_id: int,
    ) -> WwevRecord:
        """Append a complete donor clone with guarded ReqNo and Event substitutions.

        Args:
            donor_request: Positive signed-16 ReqNo (1..32767) resolving to exactly
                one working record; previously appended records may be donors.
            expected_donor_event_id: Exact unsigned-32 donor Event ID.
            expected_donor_mode: Exact signed-16 donor mode.
            expected_donor_sha256: 64-character hexadecimal digest of the full donor
                raw record; digest comparison normalizes case.
            new_request: Positive signed-16 ReqNo unused by all working records.
            new_event_id: Unsigned-32 Event ID unused by all working records.

        Returns:
            Appended WwevRecord with its new 1-based index and absolute offset.

        Raises:
            WwevError: Ranges/hash/guards fail, the donor is missing or ambiguous,
                a new identity collides, or candidate parsing/preservation checks fail.

        Notes:
            Candidate checks precede committing this operation. Copies every donor
            byte except ReqNo and Event ID, updates the header count, and retains all
            prior bytes outside that count. Collision scope is this editor only;
            no NBNK Event existence or LMT trigger validation is performed.
        """

        donor_request = check_positive_i16(
            donor_request, "donor request", WwevError
        )
        new_request = check_positive_i16(new_request, "new request", WwevError)
        expected_donor_event_id = _check_u32(
            expected_donor_event_id, "expected donor Event ID"
        )
        new_event_id = _check_u32(new_event_id, "new Event ID")
        expected_donor_mode = _check_i16(expected_donor_mode, "expected donor mode")
        expected_donor_sha256 = _normalize_sha256(
            expected_donor_sha256, "expected donor record SHA-256"
        )

        donors = self.records_for_request(donor_request)
        if len(donors) != 1:
            raise WwevError(
                f"expected one donor request {donor_request}, found {len(donors)}"
            )
        donor = donors[0]
        if donor.event_id != expected_donor_event_id:
            raise WwevError(
                f"donor request {donor_request} expected Event "
                f"{expected_donor_event_id} but found {donor.event_id}"
            )
        if donor.mode != expected_donor_mode:
            raise WwevError(
                f"donor request {donor_request} expected mode "
                f"{expected_donor_mode} but found {donor.mode}"
            )
        if donor.sha256 != expected_donor_sha256:
            raise WwevError(
                f"donor request {donor_request} expected record SHA-256 "
                f"{expected_donor_sha256} but found {donor.sha256}"
            )
        if self.records_for_request(new_request):
            raise WwevError(f"new request already exists: {new_request}")
        if any(record.event_id == new_event_id for record in self._records):
            raise WwevError(f"new Event ID already exists: {new_event_id}")

        raw_record = bytearray(donor.raw)
        if len(raw_record) < WWEV_RECORD_FIXED.size + 1:
            raise WwevError("donor WWEV record is truncated")
        struct.pack_into("<h", raw_record, 0, new_request)
        struct.pack_into("<I", raw_record, 4, new_event_id)

        candidate_appended = (*self._appended, bytes(raw_record))
        candidate = WwevFile.from_bytes(self._build(candidate_appended))
        if candidate.records[: len(self._records)] != tuple(self._records):
            raise WwevError(
                "appending the WWEV record unexpectedly changed existing records"
            )
        appended = candidate.records[-1]
        if (
            appended.request_no != new_request
            or appended.event_id != new_event_id
            or appended.mode != donor.mode
            or appended.command_hash != donor.command_hash
            or appended.unknown != donor.unknown
            or appended.wwpc != donor.wwpc
        ):
            raise WwevError("appended WWEV record failed read-back verification")

        edit = WwevRecordEdit(
            donor_record_index=donor.index,
            donor_request=donor.request_no,
            donor_event_id=donor.event_id,
            added_record_index=appended.index,
            new_request=new_request,
            new_event_id=new_event_id,
            appended_size=appended.size,
        )
        self._appended.append(bytes(raw_record))
        self._records.append(appended)
        self._edits.append(edit)
        return appended

    def _build(self, appended: tuple[bytes, ...] | list[bytes]) -> bytes:
        output = bytearray(self.original.to_bytes())
        struct.pack_into(
            "<I", output, 8, len(self.original.records) + len(appended)
        )
        for record in appended:
            output += record
        return bytes(output)

    def build(self) -> bytes:
        """Return current WWEV bytes with the updated record count and appended clones.

        Notes:
            Does not reparse, run a full validation pass, or write files.
        """

        return self._build(self._appended)

    def validate(self) -> WwevFile:
        """Build, reparse, and verify append-only preservation.

        Returns:
            Parsed working WwevFile with no source_path.

        Raises:
            WwevError: Parsing fails, header metadata/dependencies/records drift,
                or original bytes outside the record count differ.

        Notes:
            Does not mutate the editor, write files, or validate target NBNK Events.
        """

        payload = self.build()
        rebuilt = WwevFile.from_bytes(payload)
        if (
            rebuilt.version != self.original.version
            or rebuilt.unknown != self.original.unknown
            or rebuilt.dependencies != self.original.dependencies
        ):
            raise WwevError("read-back verification changed WWEV header metadata")
        if rebuilt.records != tuple(self._records):
            raise WwevError("read-back verification changed WWEV records")
        original = self.original.to_bytes()
        if payload[:8] != original[:8] or payload[12 : len(original)] != original[12:]:
            raise WwevError(
                "read-back verification changed bytes outside the record count and append"
            )
        return rebuilt

    @property
    def summary(self) -> WwevEditSummary:
        """Return an immutable WwevEditSummary of counts, append sizes, and edit records.

        Notes:
            No validation, serialization, or disk I/O occurs.
        """

        return WwevEditSummary(
            record_count_before=len(self.original.records),
            record_count_after=len(self._records),
            appended_size=sum(len(record) for record in self._appended),
            edits=tuple(self._edits),
        )

    def write_atomic(self, output: Path | str, *, overwrite: bool = False) -> Path:
        """Validate and write one artifact using a temporary file beside the output.

        Args:
            output: Path or string filename; missing parent directories are created.
            overwrite: Permit replacing an existing output when True. Never permits
                replacing the original's recorded resolved source_path.

        Returns:
            Path of the written output, retaining the caller's relative/absolute form.

        Raises:
            WwevError: Validation fails, output resolves to the recorded input, or
                output already exists and overwrite is False.
            OSError: Directory creation, staging, fsync, or replacement fails.

        Notes:
            Calls build() and validate(), stages/fsyncs bytes, then uses os.replace().
            Cleans up the staged file and leaves editor state unchanged. from_bytes()
            has no source path to protect. The preflight existence check is not
            concurrency-safe exclusive creation; this is not a multi-file transaction
            or an on-disk read-back verification pass.
        """

        payload = self.build()
        self.validate()
        return _write_atomic(
            output,
            payload,
            source_path=self.original.source_path,
            overwrite=overwrite,
            kind="WWEV",
            error_type=WwevError,
        )
