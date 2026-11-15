# Optional Summary controls legend

The published configuration installs this payload with its 32-byte state record
zeroed. It draws no legend on the tested cold OFF path. `destroy` deliberately
ignores the flag and can release a matching owned window, so OFF alone is not
a universal guarantee of no effects.

[Exact final-ROM attribution](../../docs/validation/summary-controls-source-rom-1.3.2.md)
connects `runtime.c`, `abi.h`, the authenticated compiler/recipe, 484 installed
bytes and three native call sites. It includes an ownership counterexample and
isolated forwarding checks without activating the legend in a game image.

Production compilation/insertion/readback belongs to `source/sgp131/controls.py`.
The final-image reader is `tools/attribuisci.py`; it reuses that compiler and the
existing Unicorn bench with `payload=None`, preserving the executed ROM bytes.
The remaining 28 bytes of the 512-byte slot are checked separately.

Historical V4 install/active-geometry tests remain under `test/`. They are
separate from final r4 attribution and are not a new approval of geometry,
natural Summary behavior or legend activation.
