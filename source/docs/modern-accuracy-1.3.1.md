# Modern accuracy in 1.3.1: Will-O-Wisp and Keen Eye

These two bounded changes are included in the 1.3.1 composition. They add no
move/ability IDs, PP changes or save format. The component evidence below is
host/ARM execution with explicit synthetic boundaries; it is not an Android
playtest. Exact current ROM identities and integrated acceptance are in the
[current validation report](ui-1.3.1-validation.md).

## Will-O-Wisp: accuracy 75 → 85

- Archive `a/0/1/1` (V4 file 140, 471 contiguous 16-byte members), member 261,
  byte 5. Member preimage: `a70002000a4b0f000000001611010000` (effect 167, status,
  Fire type, 15 PP).
- `sgp131.modern_moves` changes exactly one ROM byte in place without rebuilding
  the NARC. It rejects a foreign/truncated archive, wrong count, altered member 261
  or accuracy already 85. Readback reparses both archives and compares every
  member, all other NitroFS files, ARM9/ARM7/overlays/banner and full-ROM deltas.
- Native EN/IT V4 consumers are verified: ARM9 `LoadMoveTbl` at `0x02073300`
  reads 468×16 contiguous bytes from NARC 11 member 0; overlay 12 initialization
  at `0x0224868E` copies it into `ctx + 0x3DE`, indexed by accuracy calculation.
  Summary/`GetMoveAttr` read member 261 through FAT. Both paths obtain 85.
- Unicorn executes native `BattleSystem_CheckMoveHit` from its entry with the
  archive-built cache. All 100 `Random() % 100` residues produce **75 hits before,
  85 after**, differing only at 75–84, with one RNG call each. Evasion stages −6..+6
  scale 85 using the native table.
- Burn, Fire immunity, Safeguard/Substitute/Protect and animation use effect 167
  and battle scripts, not the accuracy byte. Readback proves effect/type/other
  fields/files unchanged; this component campaign did not replay those effects
  in gameplay.
- PP 15 and maxima 15/18/21/24 for PP-Up 0..3 retain native `GetMoveMaxPP`
  (`0x0207332C`). Stored Pokémon are neither read nor migrated.

## Keen Eye: ignore all target evasion changes

The single seam in overlay 12 `BattleSystem_CheckMoveHit` (base `0x022378C0`)
is `0x0224BD5C BL GetBattlerAbility(ctx, attacker)`, followed by `CMP r0, #109`.
Native Unaware sets `r4` (target evasion delta) to 0. The patch replaces only
those six bytes with a BL to the compiled predicate and `CMP r0, #1`; the next
branch and remaining formula stay intact.

`features/modern-accuracy/native.c` calls native getter `0x022527CC` exactly
once, returning 1 for effective ability 51 or 109. The getter applies Gastro Acid
(except Multitype) and other suppression, so suppressed Keen Eye/Unaware retain
original behavior. The separate stat-change command preventing accuracy loss
is untouched.

The position-independent payload is 28 bytes within a 128-byte compile budget,
SHA-256 `9370a52456cd303a935e69a033224d00f8a18d03c6d70a4032839efa2ef43cdd`.
Its only literal is the getter address; it uses 4-byte alignment, an 8-byte stack
frame (`push {r7, lr}`), and preserves AAPCS r4–r11. Apple Clang 21.0.0
(`clang-2100.3.34.2`) is pinned by version and executable hash.

Reserve owner `modern-accuracy.code` receives 32 bytes at `0x023D5AA0` in the
retired old-Guide compartment, conditional on UI retirement.
`compile_native(work_dir, owned_address)` compiles for its supplied address.
Stages require a granted slot and verify its current-content hash, writing only
28 payload bytes and preserving/checking the final four bytes.

`apply_code(data, lingua, work_dir, *, slot)` installs payload/seam in place
without appending files or changing `a/0/2/7`; independent
`verify_code(before, after, receipt)` reads it back. This path follows the UI,
whose description is a member 722 delta through `text.patch_bank`.
`apply(..., slot, charmap)` also appends the description archive and accepts
only exact V4 inputs.

Overlay 12 must be the writer's canonical BLZ encoding (`blz_comprimi_ottimo`
with original FAT length), with coherent FAT/y9, unchanged compression/flags,
`0xFF` slot tail, two agreeing decoders and mandatory receipt input/output hashes.
Alternative encodings of the same decompressed bytes are rejected even with a
rewritten receipt: altered footer, coherent four-byte padding, or unused flag bit.

## Localized description: bank 722, row 51

`features/modern-accuracy/text.py` replaces only row 51 of `a/0/2/7` bank 722;
123 other rows and 829 other members remain unchanged. The append path uses
`sgp13.resources.append_file`. The earlier longer draft did not fit real windows;
the installed strings are:

| Language | Literal game text | Pixels per line |
| --- | --- | --- |
| EN | `Prevents accuracy loss.` / `Ignores evasion changes.` |131, 136|
| IT | `Evita cali di precisione e` / `ignora i cambi d’elusione.` |131, 134|

Measured with native font 0 from `a/0/1/6`, 16-pixel line height, in V4 windows:
ARM9 Summary window 7 is 152×32 px at x=3; overlay 8 battle Summary is 144×32 px at x=0.
Both allow two lines. The widest of 123 other retail descriptions is 136 px, and
neither new line exceeds it. The text mentions no items/weather. ARM9 font 0
metadata at `0x020F56D8` confirms height 16/spacing 0. Private font-reconstructed
renders are not gameplay captures.

## ARM evidence

`features/modern-accuracy/test/accuracy_bench.py` executes the real function,
getter, Mold Breaker check `0x02252834`, ARM9 divisions and native table. Declared
stubs cover battle type, field abilities, items, the already-acted helper and RNG.

| Attacker ability / target / move | Before | After |
| --- | --- | --- |
|51, evasion+6, accuracy 100|33/100|100/100|
|109, evasion+6, accuracy 100|100/100|100/100|
|51, evasion−6, accuracy 75|100/100|75/100|
|109, evasion−6, accuracy 75|75/100|75/100|
|Suppressed 51, evasion+6, accuracy 100|33/100|33/100|

The complete matrix covers accuracy/evasion stages 0..12 × four attackers ×
{none, 51, 109} × suppression. Effective 51 matches native neutral-target evasion;
all other cases match the original, including RNG calls. Interactions include
target Unaware/Simple, attacker Simple/Compound Eyes, Sand Veil/Snow Cloak with
weather/Air Lock, fog, Gravity, BrightPowder, Wide/Zoom Lens, Micle Berry,
Foresight, Miracle Eye, Tangled Feet, Hustle, fixed-rate No Guard path, charge
turn, unchecked moves, Thunder in sun, tutorial, doubles and target changes.

The isolated predicate covers 256 abilities × four battlers × {none, Gastro Acid,
Gravity+Levitate, Ingrain+Levitate} at two addresses, with one getter call.
An in-memory installed V4 diagnostic executes its actual ARM9/overlay 12 without
injected payload and matches the table. Because V4 still owns that slot as
Guide code, this component diagnostic is not itself a playable composed ROM.
Independent readback confines overlay changes to the seam and ARM9 changes to
the payload, checking tail, other files and description.

After a passing baseline, mutants rejected: missing 51, missing 109, direct
ability-byte read (suppression bypass), CMP still 109, positive changes only,
unconditional zeroing and damaged SP.

## Composition and AI boundary

The accuracy seam `0x0224BD5C..61` and AI fix `0x02258938..0x02258945`
(eight logical bytes) are disjoint in overlay 12. Each stage decodes the current
overlay and checks its own function. Both orders yield identical images/ROMs
in EN/IT `test_composes_with_ai_scoring_in_either_order`.

The verified EN V4 overlay 10 AI script matches the pret reference. It neither
calls `BattleSystem_CheckMoveHit` nor duplicates its formula: it reads ACC/EVA
stages and checks ability 51 once to penalize accuracy-lowering moves against
Keen Eye, which remains correct. Boosting its own evasion against Keen Eye or
using target-evasion scoring with an AI Keen Eye user may become less useful;
that is inherited incomplete ability knowledge, not a demonstrated new defect.
No AI hook was added without a reproducible case.

This report establishes component behavior, not Android performance/persistence
or integrated gameplay acceptance. Preserve that boundary when citing it.
