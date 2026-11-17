# Five-language build

The published Sacred Gold Plus 1.3.2 release and the 1.3.3 development
candidate support English (USA), Italian, French, Spanish (Spain) and German. The public README and technical documentation are English. Player
manuals, authored dialogue and interface copy belong to their own locale.

## 1.3.3 candidate validation

The [final five target identities](../distribution/game-1.3.3.json) combine
unchanged EN/IT/ES onboarding successors with the exact DE/FR Training
successors below. The [correction report](validation/fixes-1.3.3.md) separates
scoped readback, historical seven-cycle onboarding evidence and later exact
DE/FR menu/SAVE/cold checks. Native Options and Guide screens received bounded
host review. This is not native-speaker certification, universal compatibility
or physical-device acceptance. Historical receipts and captures are preserved.

## Source ownership

### German Training menu correction

The Training stat menu uses font 4 and seven 96×32 px windows in overlay 27;
the two Mart service menus use six windows of the same size. Ordinary field
dialogue's 216 px limit does not apply. Stat values `0,1,2,4,5,3,255`, service
values `0..5`, order, native code, font and touch rectangles are preserved.

Four German catalogue aliases exceeded these windows:

| Alias | Original label | Original advance | Replacement | New advance | Margin |
| --- | --- | ---: | --- | ---: | ---: |
| `m:385:64` | Spezial-Verteidigung | 129 px | Sp.-Vert. | 61 px | 35 px |
| `m:385:24` | Kronkorken kaufen | 116 px | Kronk. kaufen | 87 px | 9 px |
| `m:385:25` | Kronkorken abholen | 122 px | Kronk. abholen | 93 px | 3 px |
| `m:385:27` | So funktioniert’s | 109 px | So geht’s | 60 px | 36 px |

The [portable checker](../localization/TRAINING-FIT.md) has two finite profiles:
`stat7` checks the three message banks and three stat menus per script;
`service6` checks the two actual Mart callers. Each authenticates the native
chain, overlay layouts, font, script mapping and aliases. Installed text and
an optional catalogue proposal have separate results: a corrected proposal
cannot conceal an old installed overflow. Nineteen owned synthetic tests and
the 77-test localization suite pass; no retail font table or bitmap is embedded.

The current separate German successor is 162932492 bytes, SHA-256
`26d2a09913a52fc1728dbf682dc94ec49ac6fb8d2817cde4debde7159e42ae2a`.
Independent readback finds twelve word streams changed across banks 385, 557
and 630, all in message archive/FAT 156. The other 512 logical file payloads,
core, font, scripts, IDs and unowned bytes are preserved; derived header/GRC
metadata and padding are checked. Both installed profiles pass.

On this exact successor, a normal Continue route showed both menus, all their
cursor positions and Back/Leave. A native SAVE/process-exit/cold Continue cycle
on a genuine prepared German copy preserved five party Pokémon, 113 boxed
Pokémon, three expanded Bag slots, money, Plus settings and Training policy/
reward ledger. No purchase, claim or IV/EV application was selected. Preparing
that copy had explicitly enabled Legacy and queued historical rewards; that
setup delta is separate from preservation across the subsequent update.

The earlier stat-only successor `44d398bb…8ce0` remains historical: only three
word streams changed there, and two bounded raw-save cycles covered an early
German save without Plus data and the prepared advanced copy. Those two cycles
are not relabelled as tests of the current successor. Its natural stat-menu
review led to discovery of the three additional service-label overflows above.

These measurements are advances. The 95/96 px Spezial-Angriff control and the
93/96 px claim label appeared complete in the observed images; analytical ink
bounds and native-speaker certification remain unqualified. Host cases do not
establish universal save compatibility or physical-device acceptance. No
installation or release was performed; the existing
five-image contract still retained the onboarding identities at that checkpoint.
The [final contract](../distribution/game-1.3.3.json) now selects the exact
German and French successors, preserving those earlier receipts separately.

`source/localization/languages.json` pins the exact original HeartGold revision-0
inputs, including full SHA-256, size and header code. Filenames do not establish
identity. Keep owned ROMs and all generated game files outside Git.

### French Training menu correction and regional coverage

A subsequent regional check found three French service labels exceeding the
same native 96 px windows. The earlier German results remain valid, but did
not establish French coverage. Only these catalogue values changed:

| Alias | Original label | Original advance | Replacement | New advance | Margin |
| --- | --- | ---: | --- | ---: | ---: |
| `m:385:21` | Entraîner les IV | 104 px | Entraîner IV | 80 px | 16 px |
| `m:385:24` | Acheter des Capsules | 134 px | Acheter Caps. | 88 px | 8 px |
| `m:385:25` | Réclamer les Capsules | 137 px | Réclamer Caps. | 93 px | 3 px |

The separate French successor is 162560728 bytes, SHA-256
`df8b6aad56a3422fef5597f9d8e4123b58e9f60d62e5510b5a319009bf1069b8`.
Independent readback finds exactly nine changed word streams: the three
aliases and their counterparts in banks 557 and 630, within archive/FAT 156.
The other 512 logical payloads, core, font, scripts, menu values, save layout
and identifiers are unchanged. Both installed profiles pass; checking the
old French image still reports its installed overflow even with the corrected
catalogue proposal.

A natural route on a prepared raw-save copy exercised the service and stat
menus, every cursor position, Back and Leave, then native SAVE and cold
Continue. Five party Pokémon, 113 boxed Pokémon, three expanded Bag slots,
Plus settings and the Training ledger were preserved; generation 116→117.
This prepared copy was previously written by the German test candidate and
is a host presentation test, not a normal language-switch installation route.
A separate original French fixture without Plus data passed Continue/SAVE/
cold Continue, generation 1→2, with its one party Pokémon preserved. Neither
cycle selected a purchase, claim or IV/EV application. Original fixtures were
unchanged; neither case establishes universal compatibility.

The finite regional matrix is `stat7` and `service6` × EN, IT, FR, ES and DE.
EN/IT/ES use their unchanged exact candidate images; FR uses the successor
above. DE reuses the exact `26d2a099…ae2a` reports recorded before that test
image was pruned, rather than a new scan of the older German image. All ten
cells pass advance checks. The unchanged Spanish Buy/Claim labels measure
96/96 px and French Info 95/96; ink bounds remain unmeasured. French labels
appeared complete in the observed host images, without native-speaker or
physical-device certification. Other menu families are outside this matrix.
At that R1 checkpoint the distribution contract was unchanged and no
installation or release was performed. Final delivery now selects this exact
French successor in the versioned contract; R1 receipts remain historical.

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
  --output /private/SGP-1.3.3-FR.nds --receipt /private/SGP-1.3.3-FR.json
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

The corrected 1.3.2 package keeps five language folders in one ZIP. Each has
localized installation/news PDFs and cheat material; seven English gameplay
PDFs are shared once. The archive includes 175 explicit updater routes from 35
recognized original/historical inputs, including the original five 1.3.2 builds.
All five corrected language targets have individual native SAVE/cold-restart
and localized Guide/Options checks in the [correction report](validation/guide-opening-1.3.2.md).
EN/IT are built by the shared composer; FR/ES/DE presentation is composed and
independently read back against that exact corrected English core. Historical
contracts and reports retain their original identities and limitations.

Manuals read names and numerical facts from each exact candidate and matching
retail baseline. Encounter records keep verified native IDs/weights; unmapped
floor descriptions remain explicit limits. Optional project cheats require
the full target SHA-256 and native static preimages. Revision checks do not
certify every runtime effect; the unverified money pointer and historical
third-party database are omitted. Regenerate target-bound PDF/cheat material
when a target changes. See [packaging](../distribution/README.md) and the
[1.3.2 contract](../distribution/release-1.3.2.json) for exact routes and hashes.
