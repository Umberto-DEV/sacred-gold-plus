# Corrected 1.3.2 package verification

The single player download is `Sacred-Gold-Plus-1.3.2.zip`, with release title
**Sacred Gold Plus 1.3.2** and tag **1.3.2**. Its schema-3 source contract is
[release-1.3.2-r4.json](../../distribution/release-1.3.2-r4.json); the internal
revision distinguishes corrected targets without changing historical contracts.

File reconstruction passed for the five exact corrected targets in
[the game identity contract](../../distribution/game-1.3.2-r4.json). The archive
is **1,186,672,021 bytes**, SHA-256:

```text
037a35d4d48118ef5fbca273de3caf97cfdfff2e58ea4328e0e5ac78095fd78e
```

## Verified package contents

The archive has **254 members** under `Sacred Gold Plus 1.3.2/`:

- Five language folders retain one same-language clean-ROM patch each, ten
  localized installation/news PDFs, fifteen localized cheat files and complete
  credits/licenses.
- `Originals/` contains the seven current English gameplay guides, shared once.
- `Optional-Updaters/` contains all **175 direct routes**: each of **35 recognized
  source identities** can produce every current language. The registry includes
  the five original 1.3.2 outputs alongside the thirty previous sources.
- `Developer-Inputs/` preserves the two base-1.1 xdelta files and two historical
  reference ZIPs byte for byte. Source stays on GitHub; no source archive, ROM,
  raw save, BIOS or extracted ROM tree is packaged.
- Complete inventories and internal checksums cover the included files.

Every route was freshly encoded with xdelta3 and independently decoded with
both xdelta3 and pinned Rom Patcher JS commit
`3183884086825c3a57c72026234debcef1e2240c`. Both reconstructions matched the
complete intended target size and SHA-256. The five primary patches reuse their
verified clean-source routes. The finished ZIP was reopened, its exact member
map compared and every inventoried member independently hashed. Temporary
decoded ROMs were removed by the production builder.

## Documents, cheats and developer delivery

The ten localized PDFs and fifteen cheat files were regenerated against the
exact corrected targets and pinned in the release contract. The five illustrated
installation PDFs have seven pages each and retain both real patcher screenshots,
official links, source/output fingerprints and the copied-save update procedure.
All **54 localized PDF pages** were inspected in contact sheets, with additional
full-size German entry and French patcher-page inspection; no clipping, overlap,
missing images or layout defects were observed. The seven freshly derived
English gameplay PDFs exactly match the previously reviewed package bytes.
This is a layout/data check, without a new independent native-speaker editorial
review or a new emulator execution of every cheat.

[build-inputs.json](../../distribution/build-inputs.json) preserves the four
immutable source-input hashes and sizes.
[build-input-delivery.json](../../distribution/build-input-delivery.json) pins
the complete release ZIP and exact member paths independently. That delivery pin
is excluded from the ZIP, so the container has no recursive self-hash. The actual
finished container was authenticated and all four builder files extracted and
verified through [download_inputs.py](../../distribution/download_inputs.py).
The two stage-zero deltas also retain their original game/input/output pins.

The delivery tests cover complete-container and member authentication,
truncation/oversize refusal, duplicate/traversal/symlink refusal, preservation of
existing different files, verified-file reuse, explicit HTTP mirror overrides
while retaining the tracked HTTPS pin, and the deadline after data/EOF reads.
Historical direct-download and r2/r3 package behavior remain supported. The complete ROM-free distribution suite passed **98 tests**; the stage-zero/downloader suite passed **62 tests**. All ten historical r3 player PDFs were also freshly reproduced byte for byte after the combined-layout changes.

## Acceptance boundary

These results establish file reconstruction, layout and authenticated builder
input preservation. They do not themselves establish game execution, raw-save
compatibility or physical installation. The exact corrected-game acceptance and
its coverage limits are recorded separately in
[the Guide-opening validation report](guide-opening-1.3.2.md). A source test or
successful package build must not substitute for those checks.
