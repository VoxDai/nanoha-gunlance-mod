# Custom Voice Sound Standard

Read this reference whenever a design adds custom character voice to an NBNK.
It fixes the default audible route and media contract established by the
`sharpen_voice_mix_probe` candidate 07.

## Canonical Sound

- Source donor: `original/nbnk/wp_cmn_epvsp.nbnk`, Wwise v120, Bank ID
  `1149256632`, Sound `890667980`, Media `838569492`.
- Original 46-byte donor body SHA-256:
  `b2b6d8e026d1e0aad1e4f308bbd7fdf01e516b1e02c9db6f834199b23cd9412e`.
- Canonical changes: set `DirectParentID=209038110` and set body `+0x20`
  `PositioningParams.uByVector=0xC1`. Substitute only the new Sound ID and
  Media ID for each route.
- The canonical donor-ID body SHA-256 after those two changes is
  `54433bb432a51b7912e85edbae003f4d2cb2445ce34242b0a1713fc680a74a64`.
- The external parent is locked by
  `original/nbnk/pl_act_vo_event.nbnk`: Bank ID `3755575407`, Actor-Mixer
  `209038110` body SHA-256
  `3f95ef076e1c9119c81973022288e86d273d5dd4de8501fc0aad26c218584a80`.
  Treat this Bank as a reference input; do not add it to the Mod package.

Use this 46-byte Sound directly by default. Do not clone a weapon Sound or
Container merely to obtain its output, positioning, parent, Aux, or mixing
properties. A Container hierarchy that changes the Sound's direct parent is a
separate design choice and requires explicit probe evidence.

## Media Contract

- Repository source: ordinary character voice is a 48 kHz, stereo, 24-bit PCM WAV that passes the LUFS-I and filename
  validation in the [design contract](design-contract.md).
- Runtime media: 48 kHz, 16-bit, mono Wwise PCM WEM using channel config
  `000001410000`.
- Downmix without gain. Do not add pre-gain, loudness normalization,
  loudness correction, or content-specific volume processing during build.
- Preserve the final WAV's existing amplitude during the build. If loudness needs adjustment, first report the failed
  validation and obtain explicit user confirmation, then re-export the WAV with constant gain as a separately reviewed
  audio task. Do not encode the correction in the design or builder.

## Paired Spatial Paths

When one audible action has left/right or other paired spatial Events, do not
append the same C1 custom voice to more than one path. Select one Event for the
voice and require the paired Event, its original Action list, and original
audio to remain byte-exact. Only an explicit behavioral requirement backed by
an in-game probe may authorize duplicate playback.

Record the selected Event, untouched paired Event, exact Action lists, standard
Sound IDs, mono runtime channel count, structural body guards, and expected
HIRC summary in the design.
