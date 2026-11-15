# Full-Bag gifts and pickups

This module remains part of the **1.3.1** build chain. Free gifts and ground
pickups can finish when an item stack is already full: the amount that fits is
added normally, any excess is discarded, and the script shows the dedicated
notice. Shops, paid rewards, trades and sites outside the audited census keep
the original behavior.

Stack limits are 999, or 99 for TMs/HMs. Mail and Key Items always retain native
behavior. The historical table was generated for 110 permissive sites: 106 unchanged
keys and four regenerated after the REWARD-01 reversal. In exact r4 EN/IT,
later script repairs leave 102 matching keys and eight obsolete keys. See the
[current attribution case](../../docs/validation/gift-source-rom-1.3.2.md)
for the source replay, fallback coverage and remaining policy decision; the
table has not been changed.

The public composed API is `source/sgp12/blocchi/borsa.py`:

```python
finale, rapporto = borsa.applica(rom, build_dir, lingua, manifest_path=None)
verdetto = borsa.rileggi(rom, finale, build_dir, lingua)
```

Its four stages are `premi`, `testo199`, `appendici` and `arm9`. Independent
readback reports each stage and returns `esito_finale: ROSSO` if any condition
fails or the result differs by even one byte from the expected reconstruction.
Individual tools remain available for diagnosis; the builder uses the composed API.

Set `SGP_PRET_SOURCE` to `pret/pokeheartgold` revision
`0985e8718df4f25e64d6507d89c0c97c0d288981`. The module reads `charmap.txt` and
tracked `tools/py_scripts/scrcmd.json`; it needs neither a 1.03 ROM nor `local/` files.

Newer PRET sources can supply additional names and explanations without replacing
these production inputs. The [reference comparison method](../../docs/test-bench.md#using-newer-pret-references)
records the moved, byte-identical charmap and three recovered script-command names.
Compare your own metadata with the standard-library-only reader:

```sh
python3 -I -S -B source/features/borsa/tools/confronta_metadata_pret.py \
  --before /path/to/old/tools/py_scripts/scrcmd.json \
  --after /path/to/new/tools/py_scripts/scrcmd.json
python3 -I -S -B -m unittest discover -s source/features/borsa/test -p test_pret_metadata.py
```

Exit 0 means identical parsed metadata or changes confined to command names;
1 means other metadata differs; 2 means an input error. The JSON reports hashes
and all renames by numeric ID. This is reference triage, not production admission
or proof that the corresponding ROM functions execute identically.

```sh
python3 source/features/borsa/tools/compila_borsa.py --uscita DIR
python3 source/features/native-core/tools/compila_tutti.py --uscita DIR --solo borsa
SGP_ROM_DIR=/path/to/roms SGP_PRET_SOURCE=/path/to/pokeheartgold \
python3 -m unittest discover -s source/features/borsa/test -v
SGP_ROM_DIR=/path/to/roms \
python3 source/features/borsa/tools/mutanti.py --uscita DIR/mutanti.json
```

Class B uses private `base-1.1-{EN,IT}.nds` inputs in `SGP_ROM_DIR` and rebuilds
all public stages through Rare Candy. The Unicorn bench executes 27 ARM cases
and rejects 12 one-bit mutants. Static/container checks cover both languages,
110 keys, four readbacks, idempotence, unchanged length and every byte outside
the declared regions.

The historical EN/IT Route 29 runtime fixture shows 999 Potions remaining at
999, the ground Ball disappearing, and a two-page notice naming the discarded
item. At 998, the count reaches 999 without that notice. On the same fixtures,
the previous code blocks the pickup at 999 and leaves its flag unchanged.
This exercises the shared ground-Ball flow, rather than every one of the 110
sites or every NPC gift, trade or purchase. Those other paths have census,
readback and ARM coverage. Historical evidence does not by itself accept a
newer ROM; see [current validation](../../docs/ui-1.3.1-validation.md).


## Current source-to-ROM verification

`tools/attribuisci.py --help` checks the current compilation, complete owner,
historical table generation, later script drift and installed command paths.
The bench's explicit `installed=True` mode preserves ROM code and table;
the default remains the historical synthetic unit fixture. Both modes require
an actual return before the instruction budget. The current case is bounded
host evidence, not fresh acceptance of every gift, script lifetime or save.
