# Battle Bag cache

This **1.3.1** dependency reuses item data already resident in the battle when
the optional battle animations are enabled. In the historical EN/IT fixture,
the idle-task opening pause fell from **55 to 7 frames** (about **0.9 to 0.12
seconds** at 60 Hz). A short load remains. The stage follows `anim2` and retains
its 0.375× breathing rate; [v5d](../anim2/README.md#b-pose-accent) changes the
B pose separately.

The cache requires the animations option, which is **off by default**. The byte
at `0x023D8716` in the Plus save chunk is checked by `abilitato()` in
[borsa_cache.c](sorgenti/borsa_cache.c), together with valid options and
attribute 13. OFF always selects the native getter, so the measured 55→7
improvement does not apply to that setting.

## Native cause and implementation

The list constructor `ov08_02223BF4` scans eight pockets and calls
`GetItemAttr(item, ITEMATTR_BATTLE_POCKET, heap)` for every occupied slot. Each
call opens, reads and frees NARC data. `BattleContext_New` has already loaded
`trainerAIData.itemData` with `LoadAllItemData`; `BattleContext_Delete` frees it
after battle. The live Bag context can use native `GetItemVar` without more I/O.

The reference is `pret/pokeheartgold` revision
`0985e8718df4f25e64d6507d89c0c97c0d288981`, checked against both local images:
[battle context](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/battle/battle_controller_player.c),
[battle attribute getter](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/battle/overlay_12_0224E4FC.c),
and [item mapping/loading](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/item.c).

The helper replaces one BL at `ov008:0x02223C30`. Its shim obtains the menu
context from `r4`, keeps the stack 8-byte aligned, and preserves item, attribute,
heap and the original `r1=13` load. Guards require valid options, animations ON,
attribute 13 and all context pointers. Before native `GetItemIndexMapping`, it
checks `item <= ITEM_MAX` (536), then checks the mapped index against the actual
loaded count. `LoadAllItemData` loads `mapping(ITEM_MAX) * sizeof(ItemData)`
without `+1`: 513 records, indices 0–512. Member 513 is absent and falls back.
Missing cache, invalid index/context and OFF also use the original getter.
No additional cache or persistent state is allocated.

Independent data comparison matched the battle-pocket attribute in all 513
resident records to their NARC members. Quantity, selection and item use stay
native. The **256-byte** reserve at `0x023DBD00` contains 162 code bytes, zero
padding through `+0xF0`, then a 16-byte canary. Constructor/getter fingerprints
are checked first. The BL occupies four bytes, three of which change; overlay 8
recompression preserves its slot, FAT and all unrelated content.

[The compiler](tools/compila.py) emits compiled code, canary, source fingerprints
and `SHA256SUMS`, with only a temporary object. The
[installer](../../sgp12/blocchi/borsa_lotta.py) rejects stale bundles, preimage
mismatches and reserve overlaps. [Independent readback](tools/rileggi.py)
decodes ARM9/overlay separately and checks the entire image without the installer.

## Historical validation: 14 September 2026

The fixture was Typhlosion versus Kakuna in National Park, starting each cold
run from a copied save. Four EN/IT ON/OFF runs completed Bag→pocket→item→battle,
then opened and closed it again, through frame 5962.

| Check | Recorded result |
| --- | --- |
| EN/IT ON, both openings | Idle-task plateau 7 frames; VBlank plateau 6. Both stable-menu Y offsets took seven distinct values. |
| EN/IT OFF, both openings | 55 VBlank frames, preserving the native fallback. |
| ARM, 10 tests | Five contracts on shipped and recompiled blobs: arguments, return, stack, preserved registers, Thumb and fallback. Same-toolchain bytes must match; differing compilers execute both blobs. |
| Bundle, 6 tests | Size, fingerprints, provenance, symbols, reserve and tamper rejection. |
| Readback, 6 tests/language | Accept valid image; reject code, padding, canary, target, header and FAT-tail mutants. The 344-byte FAT tail remains intact. |
| Full EN/IT builds | Byte-identical reconstruction from 1.1 bases, all 15 readbacks without skips and reserve T1–T5 passing. |
| IT visual review | Bag, pocket, Ultra Ball and return screens retain menus, sprites and panels. |

This is one emulated fixture, not all pockets/inventories or physical hardware.
Remaining loads and Party-menu pauses are separate. No poses/images are added.
These results retain their historical candidate scope; current release coverage
is in [1.3.1 validation](../../docs/ui-1.3.1-validation.md).

## Reproduce

From the root, install `source/requirements.txt` and use an ARMv 5-capable Clang:

```sh
python3 source/features/borsa-lotta/tools/compila.py \
  --uscita source/sgp12/build/borsa_lotta
python3 -m unittest discover -s source/features/borsa-lotta/test -p test_build.py
python3 -m unittest discover -s source/features/borsa-lotta/test -p test_blob.py
SGP_ROM_BORSA_PRIMA=/path/to/pre-bag-EN.nds \
SGP_ROM_BORSA_DOPO=/path/to/post-bag-EN.nds \
  python3 -m unittest discover -s source/features/borsa-lotta/test -p test_rilettore.py
```

Repeat ROM readback with the IT pair. Unicorn requires executable JIT memory.
ROM-free suites run through `source/run_tests.py`; ROM mutants are Class B.
The [sgp12 dependency builder](../../sgp12/README.md) installs and reads back
`borsa_lotta` as stage 15. Keep ROMs, saves and captures private.
