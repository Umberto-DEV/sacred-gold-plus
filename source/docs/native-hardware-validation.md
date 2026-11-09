# Native-hardware candidate validation

Use this procedure with the existing [candidate validation report format](validation/README.md).
It describes how to qualify an exact ROM on an identified Nintendo configuration;
it does not establish new hardware support or transfer an emulator result to a
physical console. Current game identities are in the
[game contract](../distribution/game-1.3.2-r4.json); the
[Guide correction report](validation/guide-opening-1.3.2.md) retains its own
bounded host/save and Android evidence.

## Identify the test cell before launch

Record predecessor and candidate SHA-256, size, language, variant, source commit,
composition/readback result and any diagnostic instrumentation. An instrumented
ROM is a separate candidate; record how its observations relate to the
uninstrumented ROM. Record the raw-save input hash and fixture category, actual
model, launch chain, component versions/builds and release channels, storage
medium/filesystem, execution mode, effective CPU clock and per-game settings.
Mark unknown values unverified rather than inferring them from the model or a
launcher icon. Keep diagnostic overhead and capture resolution explicit.

| Configuration | Prerequisite and scope |
| --- | --- |
| DS Lite / NTR | Identify an actual compatible path for launching the exact modified ROM and reading/writing its raw save. A stock console alone does not establish that path. NTR resource/timing claims need their own measured cell. |
| Stock DSi | Establish a suitable existing launch path before testing. Keep its loader, mode, clock and storage cell separate from DS Lite and New 3DS. |
| New 3DS / TWiLight Menu | Verify the actual [TWiLight Menu](https://github.com/DS-Homebrew/TWiLightMenu) and [nds-bootstrap](https://github.com/DS-Homebrew/nds-bootstrap) builds/channel used by this game, resolved mode/clock and all per-game overrides. Their presence does not by itself verify launch, save routing or compatibility. |

This procedure begins after a suitable launch path exists; it does not prescribe
console modification, purchases, installations or launcher updates. A result
qualifies only its recorded configuration. Changing loader, clock, storage,
settings or ROM creates a different comparison cell.

## Preserve saves and rollback

1. With the game closed and writes finished, identify the **actual active raw-save
   path** from current loader settings and files. Record the ROM/save mapping,
   including redirects or copy-back behavior; do not assume the save is beside
   the ROM. Keep personal paths, device identifiers and backup receipts private.
2. Make fresh backups of the active installed ROM and raw save. Verify each
   backup's complete size/hash against its source and retain rollback references.
   Preserve original fixtures. Check available space before creating outputs;
   retain canonical copies rather than duplicating whole ROM/evidence trees.
3. Test on an isolated raw-save copy with an explicitly verified destination.
   Confirm the loader will neither read nor copy results back to the personal
   save. Use fresh copies of the same fixture for predecessor/candidate trials;
   never replace the personal save with test output or an older backup. If save
   isolation cannot be established, stop that cell before launch.
4. For an authorized ROM-only installation after the exact successor passes,
   preserve language, variant, installed ROM filename/path, emulator or launcher
   association and current personal save. Take a fresh verified backup at that
   time, recheck the active mapping and verify the personal save hash is unchanged
   by ROM replacement, before gameplay. Keep the previous verified ROM available
   for rollback. Preparing a candidate is separate from installing it.

## Functional and raw-save sequence

For each cell, record ordered inputs and visible outcomes, repeat count, failed
assertions, skips and limits in its candidate report. Keep large captures/raw
saves private and publish only redacted findings and hashes.

1. Cold-launch normally and select Continue from the copied raw save. Check the
   expected progress, Pokémon, inventory, expanded Bag slots and existing Plus
   settings. No savestate, memory write, reset save or new game substitutes for
   this route.
2. Exercise the changed scenario and a nearby unaffected control using normal
   inputs, including close/reopen where relevant. For battle UI changes, cover
   animations ON/OFF, first opening/reopening, switch, fainting, capture, battle
   exit, object reuse and repeated allocation/retirement. Check task/sprite
   ownership and input handling throughout; a bounded repetition result is not
   proof of universal lifetime safety.
3. Complete the native in-game SAVE and wait for all game/loader save writes to
   finish. Fully power off, then cold-launch and Continue again. Recheck the
   scenario/control and protected data. Capture and hash the resulting raw save
   after writes finish, retaining before/after copies and sequence evidence.
4. Compare protected data with independent readers: story/event progress,
   party/boxed Pokémon, inventory/registered items, expanded Bag slots and Plus
   settings, plus applicable Pokédex, Day Care and other persisted state. Explain
   expected native bookkeeping changes explicitly; complete-file hash differences
   alone neither prove loss nor establish preservation. Unexpected changes fail
   the cell pending investigation.

The core save matrix includes **EN and IT**, each with a legacy save lacking
Plus data and a populated save with existing Plus settings and Bag extensions.
A five-language claim also requires explicitly identified FR/ES/DE regional
fixtures and localized UI checks. State which populated/legacy categories each
regional fixture actually covers, omissions and the limits of shared-core
inference. The existing [successor report](validation/guide-opening-1.3.2.md)
distinguishes populated EN/IT coverage from more limited regional fixtures;
those results do not accept a new candidate or Nintendo configuration.

## Measure response without changing game cadence

The current battle Bag is a concrete measurement case: separate its first entry
from reopening in the same battle, with optional animations ON and OFF. Keep the
same scene, raw-save start, inventory, input sequence, loader and storage. Use
comparable native game pages as controls for entry and subsequent navigation.
Do not carry historical Bag timings forward as measurements of the current ROM.

Separate CPU execution time, storage read counts/bytes and waits, task ticks,
VBlank waits and visible presentations. The pinned
[HGSS main loop](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/main.c#L99)
separates task execution and VBlank synchronization; a task tick is not
necessarily one displayed frame. Emulator traces can locate calls and verify
behavior, but do not establish physical CPU or storage timing. The
[BlocksDS profiling guidance](https://blocksds.skylyrac.net/docs/guides/optimization_guide/)
also requires hardware for CPU measurements in its homebrew context; it is not
a benchmark of this retail-derived runtime.

Measure three interaction intervals with a declared observation method:

- initiating button press to first visible response;
- initiating button press to a usable page;
- subsequent navigation input to visible cursor response.

First use a separately reported preliminary run to estimate variability,
measurement resolution and capture/instrumentation uncertainty. Before final
A/B trials, record exact identities, balanced paired order, controls, sample
budget, stopping rule based on precision of the paired difference, and acceptance
criteria derived from that uncertainty and native-page response. Keep start
conditions and first/reopen categories fixed; report order effects and outliers
rather than silently dropping them. A short sample supports its observed median,
maximum and raw observations, not a reliable population-tail guarantee.

A performance claim requires a repeatable reduction beyond uncertainty that is
relevant to the native controls, with causal work counters where available,
without lost input, functional regressions or an unexplained worse tail.
Explain tradeoffs when only one phase improves. For a Bag data-reuse change,
prove redundant reads and valid data ownership/lifetime in the OFF context
before changing the animation gate; an absent context or dominant non-I/O cost
invalidates that hypothesis. This is a condition for evaluating such a change,
not an instruction to implement it. Preserve the existing renderer, native
logic cadence, synchronization and animation readability; do not infer a need
for an FPS unlock from a loading pause.

Report memory separately from timing: resident payload capacity/ownership for
the **exact composition**, runtime heap peaks and allocation lifetimes per scene,
and VRAM use/transfers. The historical
[reservation register](arm9-reserve-reservations.md) does not measure global
runtime free RAM; consult the current [composition policy](../sgp131/reserve.py)
and [map](../sgp131/data/reserve-map.json) without counting conditional regions
on top of their live owners. No heap or VRAM budget follows from spare resident
bytes alone.

## Report the evidence class

Use the existing report to distinguish prepared, measured, failed and untested
cells, exact identities/settings, save comparisons, controls, uncertainty and
remaining falsifiers. Source tests, emulator/component runs, physical function,
physical timing and publication/installation are separate outcomes. The runner's
JSON checkpoints describe suite execution only. No numerical speed guarantee,
full-playthrough claim or support for an untested model follows from this method.
