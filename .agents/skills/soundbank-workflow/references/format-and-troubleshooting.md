# NBNK, LMT, and WWEV Format and Troubleshooting

## WEM

- A `.wem` is Wwise media; renaming a WAV does not create a valid
  replacement.
- The verified project PCM WEM layout uses RIFF/WAVE, format tag `0xFFFE`,
  48 kHz, 16-bit stereo audio, a six-byte Wwise channel extension, and a
  four-byte `JUNK` chunk.
- A normal PCM WAV commonly uses format tag `0x0001` and must be converted
  with the project tool before embedding.
- Original media often uses Wwise Custom Vorbis. The verified PCM wrapper is
  larger but avoids depending on an unavailable matching Wwise encoder.

## NBNK

- `BKHD` stores the Bank header and ID.
- `DIDX` stores one little-endian `(Media ID, DATA offset, size)` record per
  embedded WEM.
- `DATA` stores WEM payloads. Rebuilt media starts are aligned to 16 bytes.
- `HIRC` stores Events, Actions, Sounds, Containers, properties, and Media ID
  references.

DIDX order is independent of Media ID order. Community labels such as “WEM
#22” usually mean the 22nd DIDX entry, so always inspect both values.

For a media-only rebuild:

1. preserve DIDX order and every Media ID;
2. replace only the selected payload;
3. rebuild DATA with 16-byte alignment;
4. update DIDX offsets and sizes;
5. preserve BKHD, HIRC, and unknown chunks byte-for-byte.

`SoundBankEditor.append_media()` adds one explicit Media ID at the end while
preserving existing records. `replace_media()` requires the 1-based index and
expected Media ID. HIRC changes must identify objects by type and ID, guard
every old value, and preserve undeclared fields. Absolute Bank offsets are not
stable after DATA or HIRC rebuilding.

Known working MHW replacement Banks retain original HIRC Source and memory-size
fields when embedding the verified PCM WEM. Do not generalize this observation
to other games or Wwise versions.

## LMT v95 and TIML

An LMT action entry may reference embedded TIML data. The supported reader
retains every action header and exposes EventGroup00–10 transforms, ReqNo A–H
assignments, keyframes, and the low eight bits of `mTrigger`.

`LmtEditor.replace_request()` changes only one guarded four-byte request value
and requires:

- one Motion and one unshared TIML;
- one EventGroup and typed slot transform;
- one matching assignment keyframe;
- the exact old/new positive signed-16 ReqNo values;
- the exact trigger-frame set.

It rejects shared TIML, multiple matches, invalid keyframes, range errors, and
overlapping edits. A successful write remains the same length and may differ
only in declared request fields.

When a request does not trigger:

1. confirm the Motion identity in game rather than inferring from length;
2. inspect the assignment frame separately from the trigger frame;
3. verify the slot bit in the trigger mask;
4. check whether TIML is shared by another Motion;
5. resolve all matching WWEV records rather than assuming one Event.

## WWEV v19

WWEV stores a versioned header, four dependency strings, and variable-length
request records. Each complete `WwevRecord.sha256` covers ReqNo, mode, Event
ID, command data, the 116-byte unknown region, WWPC, and terminators.

`WwevEditor.append_cloned_record()` preserves dependencies and all original
records, increments the count, clones the full guarded donor, and changes only
the new ReqNo and Event ID. It rejects ambiguous donors, wrong mode/Event/hash,
ReqNo or Event collisions, invalid ranges, bad strings, and trailing data.

When a request resolves incorrectly:

1. expand every record for the ReqNo and inspect mode and Event ID;
2. guard the complete donor hash, not a fixed prefix;
3. confirm the new ReqNo is unused in the relevant collision scope;
4. reparse the output and require unchanged dependencies and original records;
5. resolve the rebuilt LMT route through the rebuilt WWEV.

## Silence and Route Troubleshooting

1. Confirm the installed filename and nativePC path match the original game
   artifact.
2. For NBNK, inspect the 1-based DIDX index and Media ID, then re-extract and
   decode the rebuilt entry with `tools/utils/pyvgmstream.py`.
3. Parse the rebuilt Bank with
   `tools/wwiser/wwiser.py -d none`.
4. For added Wwise v120 HIRC graphs, inspect serialized object positions as
   well as references. Child Sounds/Containers must precede their parent
   Containers, and Actions must precede their Event; a layered route commonly
   follows `Sound → Random → Switch → Action → Event`. A Bank can parse in
   wwiser yet be rejected by MHW when a new parent Switch precedes its child
   Random. This exact ordering fault was isolated by moving only the Switch
   record after its child, which restored both the original and added sounds in
   game.
5. Trace every Event → Action → Container → Sound → Media path. Inspect
   inherited volume, pitch, positioning, Aux, parents, and paired channels.
6. For appended audio, confirm original media remains byte-exact and the new
   Media ID has exactly the intended route.
7. For animation-driven Events, verify the complete LMT → ReqNo → WWEV Event
   chain and require the intended route count.
8. Check Stop behavior, action interruption, duration, and playback limits.
9. Remove conflicting Mods that provide any of the same NBNK, LMT, or WWEV
   files.
10. Restore originals to verify the game environment, then compare with a
   known-working test artifact.

## Validation Boundaries

- pyvgmstream verifies media decoding, not Event references or Wwise mixing.
- wwiser verifies Bank/HIRC parsing, not MHW runtime acceptance.
- LMT/WWEV reparsing and hashes prove structural preservation, not that the
  chosen Motion or Event matches the intended action.
- Byte comparisons prove preservation, not loudness or subjective quality.
- In-game trigger, timing, mix, positioning, interruption, and Mod-conflict
  testing remain final acceptance.
