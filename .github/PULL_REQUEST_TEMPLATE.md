Follow [CONTRIBUTING.md](https://github.com/Umberto-DEV/sacred-gold-plus/blob/main/CONTRIBUTING.md). One focused change per PR. An
issue is optional; link one if it exists. Use `N/A` with a reason for fields
that do not apply. Never attach a ROM, save, dump, raw log or release ZIP.

## Change and reproducer

- Player-visible or developer-visible change:
- Before → after, with exact steps and a negative control:
- Source area and risk (including save layout, ARM9 reserve or dependencies):
- Related issue or discussion, if any:

## Identity and evidence

| Check | Exact input / command | Result, skips and limits |
| --- | --- | --- |
| Source | Base commit and PR head commit | Changed paths; reason for new blobs/dependencies |
| Class A (ROM-free) | `.venv/bin/python source/run_tests.py` or exact equivalent | Job URL, PASS/FAIL, collected/ran/skipped and any unexpected skip reason |
| Private build / Class B | Input language and SHA-256, exact builder/readback command | Candidate SHA-256; before/after result and unrun checks; no private paths or files |
| Runtime | Emulator/version, same scenario on predecessor and candidate | Repetitions, outcome and a nearby unaffected scenario |
| Raw save compatibility | Copy of older `.sav`, language and fixture type | Continue → native SAVE → cold restart → Continue; progress, Pokémon, Bag and Plus settings; missing matrix cells |

The public CI cannot build or run a ROM. Do not call a Class A pass game or
release acceptance. The maintainer independently reconstructs any candidate
before accepting game-dependent results.

## Provenance and review

- [ ] I inspected every changed file, workflow, dependency and attachment for private information and unexpected behavior.
- [ ] I included no ROM, BIOS, save, savestate, dump, extracted game data, raw log, `.xdelta` or player release ZIP.
- [ ] I updated the ARM9 reserve register and map together if this change claims space.
- [ ] I documented reused work, its source, author and permission to include it.
- [ ] I disclosed material AI assistance and reviewed its output, if applicable.
- [ ] I left already published patch files and tags unchanged.
