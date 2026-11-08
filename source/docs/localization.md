# Five-language build

Sacred Gold Plus 1.3.2 supports English (USA), Italian, French, Spanish (Spain)
and German. The public README and technical documentation are English. Player
manuals, authored dialogue and interface copy belong to their own locale.

## Source ownership

`source/localization/languages.json` pins the exact original HeartGold revision-0
inputs, including full SHA-256, size and header code. Filenames do not establish
identity. Keep owned ROMs and all generated game files outside Git.

| Location | Responsibility |
| --- | --- |
| `localization/locales/EN`, `IT` | Existing guarded core recipes and translated player-document/cheat copy |
| `localization/locales/FR`, `ES`, `DE` | Separate `messages.json`, `ui.json`, `guide.json`, `evolution.json`, `native.json`, `summary.json` and guarded `recipe.json` |
| `localization/messages.py` | Official donor text for unchanged/case-only retail content; explicit translations for Sacred Gold/Plus edits |
| `localization/geometry.py` | Native field-window ownership, glyph advances, variable bounds and bounded line/scroll layout |
| `localization/guide.py`, `catalogue.py` | Localized names and actual evolution rules, Guide pages and UI resources |
| `localization/build.py`, `verify.py` | Append-only composition and independent cartridge readback |
| `localization/badges.py`, `keyboard.py`, `native_text.py`, `summary_labels.py` | Bounded Fairy labels, accent keys, native onboarding/EV/IV help and German FP/DV labels |
| `distribution/reference_docs.py`, `pack.py` | Candidate-derived manuals and the five-language package |

EN/IT keep their existing bilingual source data in `sgp131/data/`, selected by
the explicit locale recipe. Shared gameplay code is not duplicated by language.
The new locale folders contain only authored presentation, metadata and hashes;
retail names, dialogue and graphics are read from the matching owned cartridge.

## Composition

First reproduce the EN/IT current player cores through `sgp131.workbench`, using
the [documented source chain](../README.md). Keep controls/rematches inert and
portable storage active. Activation requires a fresh measured proof tied to the
exact inert core; a diagnostic derivative must be independently reproduced by
the guarded builder before acceptance.

Then compose each regional presentation from the exact English player core:

```sh
PYTHONPATH=source .venv/bin/python -m localization.build \
  --language FR --core /private/player-core-EN.nds \
  --reference /private/retail-US.nds --donor /private/retail-FR.nds \
  --charmap /private/pokeheartgold/charmap.txt \
  --output /private/SGP-1.3.2-FR.nds --receipt /private/SGP-1.3.2-FR.json
```

Use ES or DE and its matching donor for the other outputs. Input hashes and
native preimages must match the checked-in recipe; a different core is a new
candidate requiring reviewed pins. The historical V4 admission guards remain
unchanged. The codec requires the pinned CRLF charmap, SHA-256
`58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded`.

The shared executable and internal English game/save identity stay intact.
Regional executables, scripts, save structures and whole mixed-content archives
are not transplanted. The US Pokédex search-unit graphics and dynamic height
formatter remain together. Regional static trainer-height/weight comparisons
are complete localized literals. Plus title/Fairy palettes stay protected;
FÉE/HADA/FEE pixels are authored within their original image boundaries.

Missing authored translations, changed control arguments, unknown glyphs,
resource-budget overflow, graphics preimage mismatches and unowned cartridge
changes fail the build. The receipt identifies complete input/output hashes,
source files, member substitutions, native resource sizes and readback results.
A static receipt does not imply gameplay or save acceptance.

Ordinary field dialogue uses the common engine's 216px, two-row window and
native scroll/wait controls. Ownership comes from actual map headers and the
explicit shared-bank messages; Bag, battle, phone and unknown or positioned
layouts are not treated as ordinary field dialogue. Existing page boundaries,
words, colours and command arguments stay intact.

UI copy uses actual native glyph advances. Footer width includes 13px per
button cap and 9px after each non-key run except the last, within 232px.
Exit/Apply bars check all labels together, starting at x4 with native 16px
advances between actions and the 240px right bound. Python admission and the
generated C descriptors must agree with the real C planner. Readback recompiles
and compares the shared dynamic UI so new locale copy cannot use an older
descriptor. Keep the generated header and production pins aligned with copy.

## Validation and release

Run ROM-free localization checks with:

```sh
PYTHONPATH=source .venv/bin/python -m unittest discover -s source/localization -t source
```

The [1.3.2 validation report](validation/localization-1.3.2.md) records exact
candidates, first boot/Mom, localized UI and native SAVE/cold-restart coverage
and limits. Bounded host results do not imply physical-handheld testing.
All game captures and saves remain private. Technical checks and authored
translation review do not constitute independent native-speaker certification.

The 1.3.2 package has five language folders, nine translated PDFs and localized
cheat material per folder. It contains five current targets, with all 30
recognized original/historical sources supported for each language: 150 explicit
routes. No older playable target is included. Historical contracts, tags and
recorded identities retain their original scope.

Manuals read names and numerical facts from each exact candidate and matching
retail baseline. Encounter records keep verified native IDs/weights; unmapped
floor descriptions remain explicit limits. Optional project cheats require
the full target SHA-256 and native static preimages. Revision checks do not
certify every runtime effect; the unverified money pointer and historical
third-party database are omitted. Regenerate target-bound PDF/cheat material
when a target changes. See [packaging](../distribution/README.md) and the
[1.3.2 contract](../distribution/release-1.3.2.json) for exact routes and hashes.
