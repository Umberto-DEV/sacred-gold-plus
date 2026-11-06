# Battle Party cache

This **1.3.1** dependency reuses the move table already loaded by the battle
when optional battle animations are enabled. Historical EN/IT first/second
openings reduced the idle-task pause from **33 to 20 frames** (about **0.55 to
0.33 seconds** at 60 Hz). A visible load remains. The [anim 2](../anim2/README.md)
0.375× breathing rate is unchanged; v5d adjusts only the separate B pose.

The animations byte at `0x023D8716` in the Plus save chunk is **off by default**.
`record()` in [squadra_cache.c](sorgenti/squadra_cache.c) requires it and a valid
options chunk. OFF always selects native getters; the 33→20 improvement applies
only with animations enabled.

## Native cause and contract

`ov08_0221D184` prepares six Pokémon. Each occupied move invokes `GetMoveMaxPP`
and four `GetMoveAttr` calls (type/category/accuracy/power). Native calls reread
the move's NARC member; each load performs seven FS reads for headers/index/data.
GDB profiling confirmed those reads during the pause, and a five-getter probe
measured the improvement before permanent installation.

`BattleContext_New` already loads 468 sixteen-byte records using `LoadMoveTbl`.
The correct offset is **`ctx + 0x3DE`**, verified from the loader literal at
`ov012:0x022486A8`. Later `itemData` is separately aligned; subtracting the
move-table length from it would introduce a two-byte error.

The helper intercepts only five Party-scan BLs: `0x0221D3DE`, `0x0221D3E8`,
`0x0221D3F2`, `0x0221D3FC`, `0x0221D406`. It gets the menu context from the
caller's `[sp]` while preserving registers and stack alignment. Guards require
valid options, animations ON, nonnull pointers and moveID 0–467; the attribute
getter accepts only the four intended attributes. All other cases use the native
getter. There are no new allocations, persistent caches or move-data writes.

PP retains the native formula, three-PP-Up clamp and 8-bit result. Division by
five uses an integer identity valid over 0–765, checked for all 256 PP values and
six PP-Up values including clamp cases. The **256-byte** block at `0x023DBE00`
contains 200 code bytes, 40 zero-padding bytes and a 16-byte canary.
[Compiler](tools/compila.py), [installer](../../sgp12/blocchi/squadra_lotta.py)
and [independent readback](tools/rileggi.py) check provenance, fingerprints,
reserve, preimages, targets and whole-image confinement. The overlay remains
compressed in the same slot, with unchanged FAT and tail.

Reference: `pret/pokeheartgold` revision
`0985e8718df4f25e64d6507d89c0c97c0d288981`, `asm/overlay_08.s`, `src/move.c`,
`include/move.h`, `src/battle/battle_controller_player.c`.

## Historical validation: 15 September 2026

The fixture was level 49 Typhlosion versus level 19 Kakuna in National Park with
six party members. Each replay cold-boots a copied save; animations are selected
explicitly in RAM without changing Pokémon or moves.

| Check | Recorded result |
| --- | --- |
| EN/IT ON, two openings | Task plateau 33→20 frames; menus/returns complete. |
| EN/IT OFF, two openings | Native 32-VBlank-frame plateau. The ON baseline's 33 task frames are a different counter. |
| ARM ABI, 10 tests | Five contracts on shipped/recompiled blobs: values, PP, bounds, options, pointers, stack/registers/Thumb. |
| Native ARM equivalence, one/language | All 468 moves, four attributes, six PP-Up values match original getters. Only NARC transport is intercepted; native division executes. |
| EN live data | All 7488 RAM table bytes match 468 NARC members. |
| Offset regression | Native comparison rejects mutant `0x3E0`: move 1 power becomes 100 instead of 40. |
| EN/IT switch/end | Two cold runs: Typhlosion→Togetic, move, KO, field return by frame 9262; screens/PP inspected. |
| EN/IT full builds | Byte-identical reconstruction from 1.1 bases, 16 readbacks without skips, reserveT1–T5 passing. |
| Bundle, 7 tests | Provenance, both maps' fingerprints, symbols, checksums, overlaps. |
| Readback, 6 tests/language | Valid image accepted; code/padding/canary/metadata/header/FAT-tail mutants rejected. |

One emulated fixture does not establish all modes, Safari, doubles or hardware.
Species/EXP reads, graphics loads and return pauses remain. The consolidated
[animation notes](../anim2/README.md#historical-validation) preserve wider
historical regressions; [current validation](../../docs/ui-1.3.1-validation.md)
keeps acceptance tied to each exact ROM.

## Reproduce

```sh
python3 source/features/squadra-lotta/tools/compila.py \
  --uscita source/sgp12/build/squadra_lotta
python3 -m unittest discover -s source/features/squadra-lotta/test -p test_build.py
python3 -m unittest discover -s source/features/squadra-lotta/test -p test_blob.py
SGP_ROM_SQUADRA_PRIMA=/path/to/pre-party-EN.nds \
SGP_ROM_SQUADRA_DOPO=/path/to/post-party-EN.nds \
  python3 -m unittest discover -s source/features/squadra-lotta/test -p test_rilettore.py
SGP_ROM_SQUADRA_DOPO=/path/to/post-party-EN.nds \
  python3 -m unittest discover -s source/features/squadra-lotta/test -p test_native_data.py
python3 source/features/squadra-lotta/tools/copione.py /tmp/party.script
```

Repeat ROM checks with IT. The script requires the fixture documented by
`anim2/tools/copioni.py`; `--off` repeats with animations disabled. Unicorn
requires executable JIT memory. Keep ROMs, saves, states, captures and dumps
private. Use `sgp12.verifica` and the
[base-stage guide](../../docs/base-stage-build.md) for complete reconstruction.
