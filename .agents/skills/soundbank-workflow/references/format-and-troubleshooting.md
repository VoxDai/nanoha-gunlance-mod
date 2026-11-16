# NBNK, LMT, and WWEV Format and Troubleshooting

This reference describes binary structure and analysis. Concrete calls are in
the [Library README](../../../../tools/soundbank_editor/README.md); exact
contracts are in the public API docstrings.

## WEM Encoding

A `.wem` is Wwise media; renaming a WAV does not create a valid replacement.
The verified project PCM wrapper uses RIFF/WAVE, format tag `0xFFFE`, 48 kHz,
16-bit stereo audio, a six-byte Wwise channel extension, and a four-byte `JUNK`
chunk. Ordinary PCM WAV commonly uses format tag `0x0001` and needs conversion.
Original media often uses Wwise Custom Vorbis. PCM is larger but avoids
depending on an unavailable matching Wwise encoder.

The Library's WEM check is a limited RIFF/fmt check, not a complete decoder or
proof of this exact PCM layout. Inspect and decode the embedded result with
pyvgmstream; use the conversion commands in the skill when preparing media.

## NBNK Structure and Preservation

NBNK consists of tagged chunks with an eight-byte header: four-byte tag and
little-endian unsigned payload length. Preserve unknown chunks and ordering.

| Chunk | Contents |
|---|---|
| BKHD | Wwise version and Bank ID at the start of the Bank header |
| DIDX | Twelve-byte records: unsigned Media ID, DATA-relative offset, and size |
| DATA | Embedded WEM payloads; rebuilt media starts use 16-byte alignment |
| HIRC | Typed object records for playback routes and node settings |

DIDX order is independent of Media ID order. Community labels such as “WEM
#22” usually mean the 22nd DIDX entry. Always verify both identifiers. DATA
offsets and whole-file offsets move after rebuilding and are not stable guards.

For media replacement, preserve entry order and IDs, change only selected
payloads, rebuild DATA and DIDX offsets/sizes, and preserve BKHD, HIRC, and
unknown chunks. For addition, append explicit media identities and verify their
new HIRC users while retaining original payloads. See the
[media APIs](../../../../tools/soundbank_editor/README.md#nbnk-and-media).

HIRC changes are anchored by object type and ID. Preserve undeclared bytes and
guard inspected old fields or whole donor bodies. The
[HIRC reference](hirc-routing-and-settings.md) explains graph topology and
serialization order. Known working MHW replacement Banks retain original
Source and memory-size fields with the verified PCM WEM; this observation is
not a guarantee for other games or Wwise versions.

## LMT v95 and Embedded TIML

The LMT header contains magic, version, and entry count, followed by a table of
64-bit Motion-header offsets. Zero offsets represent empty entries; a Motion ID
is its zero-based table position, not its rank among populated entries. Each
supported Motion header is 96 bytes, with animation metadata and an embedded
TIML pointer. Multiple Motions can point to the same TIML.

Embedded TIML links timeline types to transforms and typed keyframes. The
reader follows absolute offsets within the LMT; this is inspection metadata,
not a license to patch file offsets. EventGroup00–10 identify audio timeline
groups. Each group's ReqNo transforms assign slots A–H, while the low eight
bits of `mTrigger` activate those slots at a trigger frame. A slot uses the
latest assignment at or before that frame. Assignment time and playback
trigger time are separate facts.

Querying must preserve the complete Motion context and all WWEV expansions.
Shared TIML means a timeline change can affect more than the selected Motion.
The supported modification therefore requires an unshared timeline, one typed
request transform and assignment, and the reviewed trigger-frame set. It
changes one four-byte assignment, preserves file length and metadata, and uses
positive signed-16 ReqNo values compatible with WWEV. It does not add/remove
Motions, timelines, or keyframes. See the
[LMT APIs](../../../../tools/soundbank_editor/README.md#lmt-and-wwev).

When a request does not trigger:

1. Confirm the Motion identity in game rather than inferring it from length.
2. Inspect assignment and trigger frames separately.
3. Verify the slot bit in the trigger mask and the assignment active at that time.
4. Check all Motions sharing the TIML pointer.
5. Resolve every matching WWEV record instead of assuming one Event.

## WWEV v19 Structure and Preservation

The 16-byte header stores `WWEV` magic, version, record count, and an unknown
word. Four NUL-terminated UTF-8 dependency strings follow. Each variable-length
record has signed-16 ReqNo and mode, unsigned-32 Event ID and command hash,
116 unknown bytes, and a NUL-terminated UTF-8 WWPC string. The supported parser
requires complete records with no trailing data.

ReqNo is not necessarily unique: a query can resolve several records with
different modes or Events. Retain each expansion and its original record
position. The unknown bytes and string terminator are part of the record, not
padding to discard.

For supported additions, select one unambiguous donor and record the hash of
its complete serialized record, including ReqNo, mode, Event ID, command data,
unknown bytes, WWPC, and terminator. Clone the full record, changing only its
new ReqNo and Event ID. Keep dependencies and original records byte-exact;
only the header count and appended bytes change. Original-record mutation and
deletion are not provided. See the
[WWEV APIs](../../../../tools/soundbank_editor/README.md#lmt-and-wwev).

When a request resolves incorrectly:

1. Expand every record for the ReqNo and inspect mode and Event ID.
2. Verify the complete donor hash rather than a fixed prefix.
3. Check new identities in the current WWEV and the relevant project route scope.
4. Reparse and compare dependencies, original records, and the appended record.
5. Resolve the rebuilt LMT through the rebuilt WWEV and compare affected routes.

## Silence and Route Troubleshooting

1. Confirm the installed filename and nativePC path match the game artifact.
2. Verify the 1-based DIDX index and Media ID, then re-extract and decode the
   rebuilt entry with `tools/utils/pyvgmstream.py`.
3. Parse the rebuilt Bank with `tools/wwiser/wwiser.py -d none`.
4. Inspect HIRC references and serialized positions: child Sounds/Containers
   precede parent Containers, and Actions precede their Events. A layered route
   commonly serializes as `Sound → Random → Switch → Action → Event`. A Bank
   can parse in wwiser yet fail in MHW if a new parent precedes its child.
5. Trace every Event → Action → Container → Sound → Media path, including
   inherited volume, Pitch, positioning, Aux, and paired spatial paths.
6. Confirm original media remains byte-exact and added media has only the
   intended users.
7. For animation-driven Events, inspect the complete LMT → ReqNo → WWEV Event
   chain and the number of expanded routes.
8. Check Stop behavior, interruption, duration, and playback limits.
9. Remove conflicting Mods supplying any of the same NBNK, LMT, or WWEV files.
10. Restore originals to verify the environment, then compare a known-working
    test artifact in a recoverable game installation.

## What Validation Proves

- pyvgmstream verifies media decoding, not Event references or Wwise mixing.
- wwiser verifies Bank/HIRC parsing, not MHW runtime acceptance.
- LMT/WWEV reparsing and hashes establish structural preservation, not that
  the chosen Motion or Event matches the intended action.
- Byte comparisons establish preservation, not loudness or subjective quality.
- Game testing establishes trigger, timing, mix, positioning, interruption,
  and conflict behavior for the scenarios actually exercised.

## External References

- [MHW:IB Labelled Audio](https://docs.google.com/spreadsheets/d/10A_YEfm7KV0ATw7uD-3_o_ZOGSlGXtzWWMGXKs_neYM/edit)
  catalogs NBNK and NPCK uses, WEM IDs, bank indices, character voice presets,
  and audition notes. Verify uncertain and older entries against vanilla files.
- [Modding MH:W — wwiseutil Wiki](https://github.com/hpxro7/wwiseutil/wiki/Modding-MH%3AW)
  documents NBNK, NPCK, and WEM structures and replacement workflows. Use the
  project's wwiser submodule to parse sound banks.
