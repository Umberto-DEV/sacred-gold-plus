# 1.3 development build

This package builds a private successor from an exact EN or IT **1.2.5** image.
The published `sgp12` builder and release files remain unchanged. This is a
development build, not a published release; runtime acceptance is separate from
successful compilation. The current candidate displays **V1.3** on the title
and Plus settings; the DS library banner reads **Pokémon Sacred Gold Plus** and
retains the original icon and palette. See the [current candidate and physical
device report](../docs/device-1.3-validation.md).

## Build

Build 1.2.5 from your own cartridge dump using [the existing instructions](../README.md).
Use the same Python environment, Apple clang toolchain and pinned external
`pokeheartgold/charmap.txt`. Keep `tools/py_scripts/scrcmd.json` in that same
reference checkout at revision `0985e8718df4f25e64d6507d89c0c97c0d288981`:
the Mew stage verifies its complete hash before decoding scripts. From the
repository root:

```sh
PYTHONPATH=source .venv/bin/python -m sgp13.build \
  --base /private/path/sgp-1.2.5-EN.nds \
  --out /private/path/sgp-1.3-dev-EN.nds \
  --charmap /private/path/pokeheartgold/charmap.txt \
  --work-dir /private/path/sgp13-build \
  --report /private/path/sgp-1.3-dev-EN.json
```

For Italian, supply the Italian 1.2.5 image. Language is identified from its
complete SHA-256; other inputs are refused. Choose new output and report names.
The builder never replaces either file. Intermediate ROMs, objects and extracted
resources stay in the private work directory. Do not add them to Git.

Stages expand the reserve, install training, update the project-owned title
label, correct Mew's movement lifetime and recoverable save feedback, extend the
caught indicator, install strategic trainer changes, guarded learnset additions
and species balancing, extend the Plus interface, install native shiny generation
and search, then generate/install the field guide. The report records each stage's
hash, compilation details, source hashes, external charmap/script-metadata hashes and composition
checks. A source change during the build prevents output publication.

The final ROM is published with a same-directory, no-overwrite hard link after
its bytes are complete. The optional JSON report is published separately; if
report publication fails, the already published ROM remains valid. Inspect the
reported failure and choose a new report path rather than replacing the ROM.

## Player-facing changes

- A recoverable SAVE refusal now displays a localized failure message and
  returns to the field after deliberate A/B/touch acknowledgment. The player
  can reopen SAVE; a continuing refusal remains a failure. Previously, the
  touch-save caller displayed success despite the native FALSE result.
  The original success path and save format stay intact. The
  [investigation](../docs/deep-debug-2026-10-28.md) records EN/IT rendered tests,
  resource disposal and nine historical raw-save cycles, including active courses.
  La successiva [campagna Android del 29 ottobre](../docs/android-1.3-dev-validation.md)
  conclude 49 checkpoint, con i limiti e i pin correnti.
- The three Mew relocations wait for the incoming movement before ending the
  event script. Previously, its movement worker could access the destroyed
  script task and crash. The fix preserves event flags and existing saves;
  the [investigation](../docs/deep-debug-2026-10-28.md) records runtime coverage
  and distinguishes this defect from the separate Latios report.
- The empty field-menu slot opens **Guide / Guida**. Four categories cover
  evolutions, items and TMs, special events, and training. The 429 entries include
  229 evolution entries generated from the input ROM, 156 item entries, 38 event
  groups and six training topics. Native names and font metrics come from the
  input. Details use pages and item links, with touch and button navigation.
  Long lists support five-entry L/R jumps and touch arrows; short paragraphs
  remain together on a page.
- IV consultants are inside the Violet and Blackthorn PokéMarts. A Silver Cap
  changes one IV to 31, or an exact chosen value from 0 to 31; a Gold Cap changes
  all six to 31. These are real IVs and can affect breeding and Hidden Power.
- The Route 34 Day Care consultant offers quick EV training and courses for
  deposited Pokémon. Classic uses 252 per stat and 510 total. Unlimited permits
  252 in every stat, after an explicit balance warning. A stricter mode cannot
  erase excess existing values; the compatibility setting retains original
  rules while the player reduces them. Added quick-training EVs cost 100 each;
  reductions and resets are free.
- Free courses give one level per two hours, optionally 32 EVs per hour toward
  a chosen stat target. Real time is the default; active playtime is selectable.
  Breeding remains step-based. Course progress preserves moves and is applied
  on withdrawal. The Day Care Pokégear contact reports projected progress.
- Silver Caps cost 10,000 after the first Badge; Gold Caps cost 50,000 after the
  League. Consultants also distribute milestone rewards. Johto Gyms give two
  Silver each, Kanto three; the eighth and sixteenth Badges add one Gold each.
  The first League clear gives four Silver and two Gold; subsequent clears give
  four Silver and one Gold. First Red victory gives three Gold. Existing saves
  receive historical one-time rewards once, without retroactively paying old
  League rematches. Full-Bag rewards remain pending for later collection.
- Plus retains its settings and controls, with native selection colors and
  contextual descriptions. Its preview handles an unfinished native Text Speed
  demonstration before drawing, and restores the original preview on close.
- The existing Plus difficulty enables nine purposeful move changes across
  seven trainers. [The rationale](../docs/trainer-strategy-1.3.md) lists every
  change and its limits. Normal difficulty retains the original parties.
- Ariados learns Poison Fang at 23, Chimecho Psybeam at 22 and Kricketune Bug Bite
  at 14 in both difficulties. Existing moves remain available; the patch does
  not edit owned Pokémon. The [gameplay plan](../docs/gameplay-balance-1.3-plan.md)
  records the earlier measurements and selected shiny profiles. Il
  [censimento finale](../docs/shiny-species-1.3.md) contiene 493 decisioni:
  67 specie interessate, 50 con statistiche cambiate, 51 record personal,
  29 learnset con 32 aggiunte livello/mossa e due nuovi secondi slot abilità.
  Il builder installa modalità shiny native, seconda pagina Plus e ricerca
  specie. EV e abilità posseduti restano conservati; il calcolo nativo di
  Continue aggiorna le statistiche selezionate. La
  [verifica Android corrente](../docs/android-1.3-dev-validation.md) distingue
  i campioni giocati dalle prove ARM e dai limiti residui.
- The enemy caught indicator now also appears in trainer battles when the
  native Pokédex says that species has been caught. The intermittent wild-battle
  report has not been reproduced; this is not a claim that every reported
  missing icon has been fixed.

## Compatibility and ownership

The [successor reserve map](../docs/arm9-reserve-map-1.3.json) allocates code below
the existing public addresses. Pokémon layouts, native save arrays, existing
Plus settings and expanded-Bag records keep their identifiers and locations.
Existing item IDs are retained; previously unused IDs 113 and 114 hold the Caps.

Training uses a separate, versioned, checksummed journal bound to native save
generation and main-data CRC. Its two records are stored in the selected bank's
sector 49 or 113, with a separate ownership marker. Empty sectors observed in
fixtures do not grant universal ownership: native activation and saving must
check the actual save. Foreign or future data must not be overwritten. The
training save coordinator runs after expanded-Bag writes and before the native
save commit. A failed training write must prevent that commit and permit retry.
Le operazioni mutanti 4–8 ricontrollano ora la destinazione prima di applicare
servizi o addebiti; una preview rifiutata dall’operazione 4 va ricreata. La
[campagna Android corrente](../docs/android-1.3-dev-validation.md) verifica il
rifiuto prima di EV/denaro in EN/IT e separa gli altri rami ARM.

Do not use a savestate to establish save compatibility. Validate copies of raw
older saves through Continue, native SAVE and cold restart, and compare progress,
party, boxes, inventory, settings and Day Care data. Keep original fixtures.
Active courses, payments, queued rewards and interrupted writes need separate
tests; passing an inactive old-save matrix does not cover these paths.

## Verification

`source/run_tests.py` registers the ROM-free rules, journal, transaction, content,
native UI and source-build suites. Actual-ROM suites require private inputs:

```sh
SGP13_BASE_DIR=/private/path/inputs PYTHONPATH=source \
  .venv/bin/python -m unittest sgp13.test_space sgp13.test_caught_arm sgp13.test_teams_arm -v
SGP_TRAINING_ROM=/private/path/training-EN.nds \
SGP_TRAINING_REPORT=/private/path/training-report.json \
  .venv/bin/python -m unittest discover -s source/features/training-native/test -p test_native.py -v
```

The first directory contains `sgp-1.2.5-EN.nds` and `sgp-1.2.5-IT.nds`.
Training tests require the exact candidate and its matching installer report;
run them for both languages. Unicorn needs an executable JIT environment.
Always distinguish executed cases, skipped suites and emulator observations.

The save-feedback suites are `sgp13.test_save_ui` (compiled callback contracts)
and `sgp13.test_save_ui_rom` (actual caller, composed writers and readback).
The latter needs `SGP_PRET_SOURCE` and `SGP_SAVE_UI_CANDIDATES`, a private
directory containing the pre-save-UI `mew-fixed-{EN,IT}.nds` candidates and
matching `mew-fixed-{EN,IT}-training.json` symbol reports. The suite installs
the correction on copies in memory. `SGP_SAVE_UI_ACTIVE_DUMPS` supplies the
separate active-course RAM/raw fixtures for the composed transient-refusal
and native-commit case; without them that case skips. These controlled I/O
tests do not replace emulator SAVE/cold-restart or physical-storage tests.

The guide facts and research boundaries are recorded in
[guide-content-sources.md](data/guide-content-sources.md). The implementation
checklist is [expansion-1.3-plan.md](../docs/expansion-1.3-plan.md), and the exact
initial candidate hashes, test counts and raw-save coverage are in
[validation-1.3-dev.md](../docs/validation-1.3-dev.md). La
[verifica funzionale Android del 29 ottobre](../docs/android-1.3-dev-validation.md)
è il rapporto corrente: 45 SAVE/cold e quattro rifiuti con file intero invariato,
con prove ARM, conteggi automatici e limiti distinti.

## Local storage

The builder removes its private stage workspace on success and on exceptions.
Only the requested output ROM and optional JSON report persist; existing files
in the supplied work directory are untouched. Hard termination or power loss
may still leave a workspace: check for active users before removing that orphan.
The JSON report keeps stage hashes and receipts; internal scratch paths in stage
details are diagnostic provenance, not retained files.

Keep one verified candidate and one verified fallback per language. Promote a
new candidate only after validation, then remove superseded generated copies.
Use one canonical location for each retained build, and keep reports and scripts
instead of copies of entire build trees. Preserve original inputs, saves and
unique regression fixtures. Check peak disk requirements before starting large
builds or captures and leave at least 10 GiB free, as required by `AGENTS.md`.

The [native event-flag correction](../features/event-flags/README.md) reserves
variables `415E..416F` for the full `3F00..3FFF` bank and preserves Pal Pad bytes.
It composes with Training/Bag Continue, refuses foreign reservation ownership,
and leaves save layouts and existing event IDs stable. La verifica Android EN/IT
di prima relocation e cattura finale Mew conserva l’intera Rubrica Amici; il
censimento più ampio dei flag resta una prova ARM nel
[rapporto corrente](../docs/android-1.3-dev-validation.md). Compatibility is forward
only; execution on an older ROM cannot synchronize later event changes safely.
