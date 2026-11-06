# Extended levels — model only, not installed

**The current ROM still has a level cap of 100.** This directory contains a
ROM-free, tested contract for the requested level-150 feature. It deliberately
does not install hooks, rewrite a ROM, or touch a save.

The current policy starts locked at 100. Observing a non-egg Pokémon only after
its permanent record has been committed to Party, Box or Day Care latches the
feature when that Pokémon is level 100 or higher. The latch and highest owned
level never decrease. The effective cap is derived from that one latch: 100
while locked and 150 after unlocking. Temporary battle copies are not inputs.
A complete scan after loading a save is required as the recovery path for
records committed through a route a future hook did not observe.

`level_policy.c` models normalization and observation without knowing the game
layout. It uses the existing `over100` and `peak` meanings but is not wired to
the save runtime. The earlier local design that selected a cap at New Game and
used level 101 as the trigger is historical and is superseded by this contract.

`growth_tables.py` reads the eight `a/0/0/3` members from an explicitly supplied
candidate, requires their exact pinned 0–100 identity, and emits separate
0–150 members plus a small manifest. It preserves the first 404 bytes of every
member. For levels 101–150 it uses integer arithmetic:

```text
T(level) = floor(T(100) * level^3 / 1,000,000)
```

The product needs a 64-bit intermediate in a native implementation. The tool
never writes a ROM and refuses a nonempty output directory.

Before ROM activation, the remaining consumers must be mapped and tested in
both languages: EXP-to-level conversion and awards, battle synchronization,
Rare Candy, Day Care, Party/Box/trade paths, load-time recovery, learnsets at
the 127/128 boundary, stat saturation at 999, enemy scaling under Plus, UI,
raw-save Continue/SAVE/cold restart, and cap-100 negative controls. A partial
installation is unsafe because Party, Box and EXP-derived levels could disagree.
