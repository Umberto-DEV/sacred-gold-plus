# sgp12 — Sacred Gold Plus 1.2.4

The public builder starts from the contributor's unmodified HeartGold US or
Italian ROM. Stage 0 applies the pinned public base-1.1 delta. The existing
feature stages reconstruct the published 1.2.3 intermediate; the final
`manutenzione` stage applies the battle-copy barrier, Waterfall search guard
and the 1.2.4 title. Intermediate options text still names 1.2.3 by design;
`build/manutenzione/versione.json` specifies the final title transition.

From the repository root, with the pinned dependencies already installed:

```sh
cd source
../.venv/bin/python3 -m sgp12.costruisci --base /path/to/HeartGold.nds --uscita /path/to/sgp-1.2.4.nds
../.venv/bin/python3 -m sgp12.verifica /path/to/sgp-1.2.4.nds --base /path/to/HeartGold.nds
```

Set `SGP_ROM_DIR` for the pinned stage-0 delta and `SGP_PRET_SOURCE` for the
reference metadata, as described in [the developer guide](../README.md).
The current release pins are in [distribution/release.json](../distribution/release.json).

`verifica` rebuilds the result, checks each stage and runs the reserve gates.
A missing check produces `PARZIALE`, not a complete passing verdict. Its
full rebuild can be expensive; this release used incremental file validation
and two-decoder patch round trips, without repeating a local full build or
runtime campaign. See [release validation](../docs/release-1.2.4.md).

For a lightweight update from an exact official 1.2.3 image:

```sh
../.venv/bin/python3 -m sgp12.manutenzione --base /path/to/sgp-1.2.3.nds --uscita /path/to/sgp-1.2.4.nds
```

This streams one output, rejects unknown input hashes and existing output
files, and reads the output back. No save data is read or written.
