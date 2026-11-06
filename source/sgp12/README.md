# sgp12 — base stages used by 1.3.1

This package is a required dependency of the current **1.3.1** build. It
reconstructs the exact 1.2.5 predecessor from your own unmodified US or Italian
HeartGold ROM. Stage 0 applies the pinned public `base-1.1` delta; feature stages
reconstruct 1.2.3, `manutenzione` adds the battle-copy barrier/Waterfall search
guard and 1.2.4 title, and the final version stage produces 1.2.5. Intermediate
title strings are intentional; later stages replace them.

For the player-ready version, follow the
[1.3.1 composition guide](../sgp131/README.md), which explains the authenticated
V4 bootstrap and the complete successor chain. These commands reproduce only
its base dependency, using the pinned environment from the
[developer guide](../README.md):

```sh
cd source
../.venv/bin/python3 -m sgp12.costruisci --base /path/to/HeartGold.nds --uscita /private/path/sgp-1.2.5.nds
../.venv/bin/python3 -m sgp12.verifica /private/path/sgp-1.2.5.nds --base /path/to/HeartGold.nds
```

Set `SGP_ROM_DIR` for the stage 0 delta and `SGP_PRET_SOURCE` for reference
metadata. `verifica` independently rebuilds, checks every stage and runs reserve
gates; a missing check produces `PARZIALE`, not complete acceptance. Detailed
[base-stage instructions](../docs/base-stage-build.md) and
[bounded base-stage validation](../docs/base-stage-validation.md) retain the
exact predecessor identities and test limits. They do not accept a newer ROM.

The standalone `sgp12.manutenzione` command remains available for guarded
component diagnosis on an exact 1.2.3 input. It streams one new output, rejects
unknown hashes/existing output and independently rereads it. It reads/writes no
save data. Current 1.3.1 package routes are specified separately by
[release-1.3.1.json](../distribution/release-1.3.1.json); default `release.json`
is a historical build contract, not the current download version.
