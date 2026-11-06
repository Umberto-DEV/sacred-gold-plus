# Full-Bag gifts and pickups

This module remains part of the **1.3.1** build chain. Free gifts and ground
pickups can finish when an item stack is already full: the amount that fits is
added normally, any excess is discarded, and the script shows the dedicated
notice. Shops, paid rewards, trades and sites outside the audited census keep
the original behavior.

Stack limits are 999, or 99 for TMs/HMs. Mail and Key Items always retain native
behavior. The table identifies 110 permissive sites from the final script bytes;
106 keys remain unchanged and four are regenerated after the REWARD-01 reversal.

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
