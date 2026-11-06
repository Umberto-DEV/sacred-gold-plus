# Base-stage validation for the current build

The current 1.3.1 composer depends on authenticated historical base stages.
This document retains their original validation identities and limitations for
reproducibility. It is not an installation guide for an obsolete release, and
these results do not accept a newer ROM. Use the [current composition guide](../sgp131/README.md)
for the complete build and [current validation](ui-1.3.1-validation.md) for
candidate-specific evidence.

## Historical maintenance-stage validation — 24 October 2026

The release includes the battle-copy animation barrier, the field Waterfall
search guard and the updated title. Public ROMs contain no private stat edits.
The event script and legacy flags of the Vermilion Latios/Latias totem remain
unchanged. A player caught Latios using the maintenance candidate and reported
that the previous slowdowns were no longer present; this does not isolate the
old freeze's cause or validate every animation/city scenario.

### File validation

- The published 1.2.3 EN/IT images were checked against their exact SHA-256s.
- The maintenance stage checked all preimages, compiled source/blob hashes,
  core hash, compressed overlays with two BLZ decoders, branch destinations,
  unchanged regions, and the full streamed outputs.
- 19 recognized source ROMs, including original HeartGold US/IT, generate both
  final languages: 38 routes. Each route was decoded with xdelta3 and pinned
  RomPatcher.js, compared with the target SHA-256, and discarded after checking.
- Both player ZIPs contain 40 members, including 19 patches, manifests, the
  original five PDF guides, trainer reference, Game Guide, historical illustrated
  guides, current two-page PDF guide, instructions, license and cheat files.
- Original reference documents retain their independently pinned bytes.
- Both final ROMs passed all 11 ARM9 reserve checks (22 total).
- Focused maintenance tests: 28 passed. Library tests: 42 executed, 31 skipped
  because the full-build fixtures were not enabled. Distribution tests: 4 passed.

Historical input/target pins,member inventory and patch hashes are retained in their immutable published archives and SHA256SUMS. Current packaging uses `source/distribution/release-1.3.1.json`; its inputs/targets are different and must not be substituted for this historical evidence.

### Construction and limits

The existing construction stages and their intermediate option-title blobs
remain unchanged. Their stable reserve-map header fields are unchanged too.
The builder and verifier append maintenance to the exact, hash-pinned 1.2.3
intermediate; `build/manutenzione/versione.json` specifies the final 1.2.4 title.
A mismatch refuses construction rather than silently accepting another baseline.

A fresh full build and full runtime campaign were intentionally not repeated
locally for this release. The lightweight incremental checks and patch round
trips establish the distributed file contents; they are not a claim that the
entire public builder was rerun from retail in this release session. CI runs
the ROM-free suites, including the new maintenance and distribution checks.
No game/emulator installation or save rewrite was performed for publication.

The brief Android presentation measurement after the player's report was
regular (median 16.763 ms, p95 16.767 ms, no interval over 25 ms). It is not a
measurement of DS logic FPS/input latency or a controlled before/after trial.
Raw logs and personal installation receipts are not distributed.

### Independent review

The read-only review found no confirmed blocking defect. It separately checked
both archive inventories and original-document hashes. Remaining coverage limits:
the final-stage reader shares its patch plan with the writer (the BLZ decoding
and output pins provide separate checks); seven totem tests need private ROM
metadata and are explicitly skipped in CI. Their classification in the runner
can be refined separately. No regression from concurrent native y-offset writes
was demonstrated, but all native animation overlaps have not been exercised.

## Historical final base-stage identity

Release date: **24 October 2026**. The two player packages each support 21
input images, including both 1.2.4 languages. Published 1.2.4 files are unchanged.

[Issue #6](https://github.com/Umberto-DEV/sacred-gold-plus/issues/6) reported that
1.2.3's version could not be found. The initial Plus configuration prompt is
skipped once the save contains valid Plus settings, and the ordinary Plus menu
had no version number. On the local melonDS bench, the initial prompt already
rendered correctly in 1.2.3. The original WaterMelonDS/Android rendering issue
has not been reproduced or tested on the reported emulator.

The release shows **V.1.2.5** on the upper title screen with the logo and
flying Ho-Oh, aligned with **Developed by A FAN**. The missing descender in
**by** is restored. It also shows **Sacred Gold Plus 1.2.5** in **Options → SELECT → Plus**,
including after saving and restarting. Players need not erase settings or
start a new game to identify their version.

### Exact scope and save compatibility

`sgp12.versione` is stage 19, after the unchanged 1.2.4 maintenance stage. It
accepts only the exact published EN/IT 1.2.4 hashes. It points the Plus-menu
heading at the existing initial-prompt title and changes the final version
glyph. Each ROM changes by exactly **118 bytes**: three in the project-owned
menu text bank and 115 in the title graphics and tilemap. The label uses unused
NCGR tiles and the existing warm-white/black palette. The credit's shared tile
is copied into an unused tile before adding three pixels for the missing y
descender, so its other use remains unchanged. Both texts share baseline y=187.
There is no new allocation and no executable patch.

Independent readers check both menu-title entries, the expected label pixels,
tilemap placement, the y correction, and every unchanged byte outside those
regions. ROM size, game identity, ARM9/overlay code, FAT, palettes, logos,
animations and all save code are identical to 1.2.4. Save identifiers, offsets,
checksums and format versions are unchanged. The builder never reads or writes
`.sav` files.

Forward compatibility is required: older valid raw saves must retain their
progress and contents when updated. This correction performs no migration,
reset or setting conversion. It retains the existing handling of a save without
Plus settings (the one-time configuration) and does not make that prompt repeat
for configured saves. Invalid or already-damaged save extensions are still
subject to the existing recovery rules; this title fix does not repair them.

### Validation

- Class A: **452 tests executed and passed, 50 explicitly skipped**, of 502
  collected. Includes ten new tests for both titles, wrong inputs, corruption,
  unchanged ROM bytes, alignment, the corrected letter, and final-stage integration. Private-input skips are not
  counted as passing coverage.
- Both language candidates rebuild byte-for-byte from their pinned 1.1 bases.
  All 19 stage readers and the final T1–T5 reserve checks return **VERDE**.
  Stage 0 from retail was not rerun in this campaign.
- Native ARM Bag tests: **15 passed per language**, including the final slot,
  copying, mirrored records, all 452 interrupted-write positions, read failures,
  foreign sectors, sanitization and restart/retry behavior.
- Real font measurement: the title is **120 px** in both languages, within the
  menu's 166 px text allowance. Both menus, the initial prompt and the final aligned title screen were visually
  inspected on the physical Mac using the headless melonDS interpreter and
  software renderer; no emulator savestate was used for the update tests.

Runtime save coverage uses disposable copies. The unique fixtures are an older
raw save without Plus data, a normally saved 1.2.3 save, an advanced 1.2.2 save,
and a prepared 1.2.4 fixture with non-default settings and item 252 ×7 in the
252nd main-pocket slot. The prepared fixture was created in a separate 1.2.4
session and committed through the game's own save routine; it is a synthetic
storage test, not a claim of ordinary gameplay progression.

The no-Plus, 1.2.3 and prepared 1.2.4 fixtures are exercised in EN and IT; the
advanced 1.2.2 fixture in IT. Each is loaded with Continue, saved in-game and
cold-booted from the exported `.sav`. Reload exports equal the saved SRAM byte
for byte. The entire expanded inventory, registered items and Plus settings survive in both languages.
Opening and closing the version menu does not change SRAM. The 1.04-named local
fixture was also exercised, but is byte-identical to the older no-Plus fixture
and is not counted as independent coverage.

For three same-script comparisons (1.2.3 EN, prepared 1.2.4 EN and advanced
1.2.2 IT), the 1.2.4 control and the 1.2.5 release produce byte-identical
post-save files. Original fixture files remain untouched. These are bounded
regression tests, not an exhaustive campaign on every historical save or emulator.
WaterMelonDS on the reported Android handheld remains untested for this fix.

### Upgrading

Save normally in-game, close the emulator and retain a backup of the old `.sav`.
Apply the patch to the ROM, then associate the existing save with the new ROM
(using matching filenames or the emulator's import-save command). Start the ROM
fresh and choose **Continue**. Do not load an emulator quick save/savestate made
with the previous ROM. No new game or save conversion is required.

This is forward compatibility. Returning to an older ROM that lacks expanded
Bag support has separate limitations described in the [save contract](contracts.md#expanded-bag-121).

### Output fingerprints

| Language | SHA-256 |
| --- | --- |
| EN | `a821961fc1a90e4adaa118c4a09fce5445d25d567130d0c9edb20dfb0520050e` |
| IT | `bdf50a4f327f8ea0d8a2ef312e1491d78460d34e978d9b15d160eaf140b313d4` |

ROMs, saves, memory dumps, emulator states and private test captures are not
part of the source change. No published release asset has been replaced.

### Distribution checks

Both language ZIPs contain 21 input routes, for 42 in total. The packaging tool
verifies every route with xdelta3 and the pinned RomPatcher.js, checks all input
and target hashes again afterward, and reads back each ZIP member. Original
manuals and trainer reference retain their historical fingerprints. The two
updated PDF guides are visually checked. No ROM, BIOS or save is distributed.
