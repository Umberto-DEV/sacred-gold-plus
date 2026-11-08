# Multilingual 1.3.2 acceptance — 8 November 2026

This report covers the original 1.3.2 candidate set. The later
[Guide opening correction](guide-opening-1.3.2.md) records five successor
identities and their separate game/save/device checks.

This report identifies the final five-language candidate set and the bounded
acceptance requested for this release. Historical diagnostic reports retain
their original hashes and limitations. Commercial ROMs, raw saves, gameplay
captures and machine-specific receipts are private; public source contains the
reproducers, authored translations, ownership recipes and package fingerprints.

## Candidate identity

| Language | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 152786800 | `65d6d42a59543a499858ce43c5c4652ab5323fe290124daddfaf842ead1034f3` |
| IT | 159029716 | `e884761c8141042bc64eff62564c3e2a0c707379851eb0790e70f09bd4f4019e` |
| FR | 162560728 | `0366cc3d7909cc0e5996a78486a547dced3d7809a2243627828f74877ccaefa9` |
| ES | 162490072 | `ae593192321095f936b10e0ad444e238b2fcc12d471ee7b0f05896fde8e0745f` |
| DE | 162932492 | `225f21a9752a2e2388980f98186de6aa89aabcd68c0ef8c76d3fd99f4539fa25` |

The English/Italian cores are independently built from their authenticated V4
inputs with the existing workbench. Controls/rematches remain inert; portable
storage activation has fresh exact-candidate Party → R → native PC evidence
(phase 1→3, opens 1, failures 0). The formal guarded builds reproduced the four-word measured diagnostic
derivatives byte for byte. FR/ES/DE compose presentation
around that exact English engine; their internal game/save identity stays stable.
No published 1.3.1 target is relabelled as a new build.

## Translation and preservation

Each regional cartridge passed independent readback of all 829 ordinary message
banks: 49,441 retail/case-style positions match the matching original donor,
1,746 authored positions use explicit translated keys and preserved command
arguments, and the US height formatter is retained with its matching graphics.
There is no missing-key English fallback. The 1,391 unique authored keys are
not treated as a substitute for checking every aliased occurrence.

Each new locale also contains 144 UI strings, 633 Guide strings, localized
onboarding and all 24 native Summary help rows. The live Guide has 467 entries,
uses localized native names and actual current evolution rules. Accent keyboard
rows, embedded labels and authored FÉE/HADA/FEE graphics have exact preimage and
bounds checks. German native Summary labels use FP/DV. Graphics recipes admit
individual members and identical dependencies; title/Plus palettes and protected
US unit formatting are retained.

The final regional readback verifies 479 unchanged files and all unowned bytes
outside explicit append-only resources, keyboard/presentation spans and resource
descriptors. Scripts, game mechanics and save structures are not transplanted
from the regional originals. Shared save layout/identifiers remain unchanged.

Ordinary field layout is measured against the actual 27-tile/216-pixel native
window, pinned font and all 540 MapHeaders. All 1,200 admitted authored field
occurrences per locale pass content, command, clear-page, two-row/scroll and
width invariants; 546 mixed/app/menu/positioned occurrences remain unchanged
with explicit scope exclusions. FR/ES/DE reflow counts are 226/143/147.
Training copies in banks 385, 557 and 630 use their actual installed message
bases, not only the first catalogue alias. Variable widths reserve native name
bounds and proven training integer/stat semantics. This does not certify every
native application layout or arbitrary external variable substitution.

All 30 native Settings footers fit their 232-pixel area (maximum 231); French
root is 222 pixels. Action bars also fit. 300 real C render plans cover all
seven views across five locales and representative states. A French refusal
was reproduced before shortening its oversized footer and then corrected;
the final French cartridge opened and reopened Options successfully. All three
new locales also opened the localized Guide body.
The resident UI payload is 65,156/65,536 bytes; independent composition readback
also matches it against the current pinned compiler/catalogue, preventing stale
native descriptors from being combined with new text.

## Short runtime and raw-save checks

All five exact targets cold-booted New Game, completed the Mom conversation and
returned to visible player movement using normal input only. Runs used the
project's bounded headless melonDS core, revision
`906e9ebb27da8c6a715cd7abab4abfe8a8d29427`, ARM interpreter, software rendering,
FreeBIOS, generated firmware and fixed initial RTC 2026-09-05 12:00:00.
Runtime SHA-256:
`81e58a86e3d055696d7a661eca9e91e9e23f7a06a1dcd862badd78d4c58877e1`.
No cheats, savestates, RAM writes or warps were used. EN/IT/FR/ES/DE runs covered
21,526/15,626/19,914/23,186/23,186 frames with no sampled VBlank reset after
frame 1,000. Final cleared-dialogue/movement captures were inspected.

The New Game correction initializes the existing empty HF02 event bank before
the first family-variable access. It preserves its field IDs/layout and legacy
load migration; the normal SetVar and older-format owner regressions are reused.
See the [original diagnosis](new-game-reset-1.3.2.md) for the observed reset and
source cause. That diagnosis is not a final-candidate test by itself.

Seven Continue → native SAVE → process exit → cold Continue cases use copies
of five independent raw fixtures:

- Both EN/IT: an older save without Plus data, and an advanced older Plus save
  with five party Pokémon, 113 boxed Pokémon and three occupied expanded slots.
- FR/ES/DE: genuine matching original-retail saves, created through normal
  New Game/native SAVE and independently cold-reopened before use. FR/ES have
  one starter and five Potions; DE has an empty party/Bag. Their boxes, Day Care
  and pre-existing Plus/expanded-slot data are empty. The advanced EN/IT fixture
  supplies populated-extension/settings coverage; no advanced regional original
  fixture or active-course migration was tested.

The protected comparisons cover player identity/progress, party/boxed/daycare
Pokémon, Pokédex, native inventory/registered items, expanded Bag slots and
existing Plus settings. Native save generation advances once and the active
bank alternates; the cold export matches the saved bytes. Missing Plus data is
initialized without requiring New Game. Existing Pokémon language metadata is
preserved. Bookkeeping/playtime changes are distinguished from protected data;
no claim is made that an in-game SAVE leaves every byte unchanged. Original
fixtures and their test-input copies remain hash-identical.

These are representative format/component checks, not every possible save.
Unknown/corrupted third-party saves and every late-game feature are outside
this bounded acceptance. No physical-device installation, full campaign,
independent native-speaker certification or complete cheat-effect playthrough
is claimed.

## Universal input routing and player documents

The [versioned package contract](../../distribution/release-1.3.2.json) lists
all 30 recognized clean/historical source identities and all five latest targets:
150 explicit routes. This includes the recognized 1.03 and previous project
versions. Unknown or altered inputs fail SHA-256/size admission. “Universal”
means this complete authenticated set; a filename/version label is insufficient.
Every route must reconstruct its chosen target through both xdelta3 and the
pinned independent Rom Patcher JS decoder, compared by complete output hash.
The encoder uses a 256 MiB source-search window covering all admitted sources;
secondary compression remains off. A measured 64 MiB/default-window package
was oversized and was superseded before publication. The public packager rejects
a player ZIP at or above GitHub's 2 GiB asset limit. This changes patch encoding,
not the ROM targets, documents or raw-save evidence.
This proves reconstruction equivalence across source ROMs, not universal-save
compatibility. Applying a ROM patch does not modify a raw `.sav`.

The ZIP contains only current 1.3.2 targets, with separate EN/IT/FR/ES/DE folders.
Each contains nine translated PDFs: Installation, What's New, Special Events,
Pokémon Changes, Pokémon Locations, Evolutions, Items/TMs, Trainers and Game
Guide. Manuals are regenerated from these candidates and matching clean retail
baselines; old Plus ROMs are rejected as “original” comparison inputs. Numerical
facts and record IDs are compared across languages; representative rendered
pages are visually inspected. All 45 PDF files and 15 localized cheat files are
pinned by complete size/hash before packaging.

The six exported optional project cheats are initially disabled and statically
admitted against exact-target native instruction contexts/AR guards. The money
code and unverified historical third-party database are omitted. This is exact
revision/static validation, not runtime effect or interaction certification;
the translated notices state that limit. Original third-party manuals and
credits remain separately identified, with their actual language and unchanged
fingerprints.

## Repetition and public checks

The [update procedure](../update-workflow.md) maps each future change to its
sources, documents and minimal gates. The [localization guide](../localization.md)
and [distribution instructions](../../distribution/README.md) give reproduction
commands. ROM-free tests cover translation/control/glyph contracts, bounded
layout, resource readers, safe packaging, all 150 declared routes and rejected
stale/wrong-language/tampered documents. Local targeted localization tests:
57 passed; UI copy/resource tests: 42 passed plus two explicit private-ROM skips.
Hosted Class A coverage is recorded by the public-checks workflow for the exact
published source revision; it does not build or accept commercial ROMs.

A package verification report records the actual 150 dual-decoder outcomes,
ZIP member/checksum verification and final asset hash. Publication requires that
report and green hosted CI. Retain installation filename/path and emulator save
association; verify backups and a copy of the current personal raw save before
physical installation. Publishing a release does not install it.
