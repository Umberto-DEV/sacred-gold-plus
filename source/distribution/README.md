# Reproduce the 1.2.4 player downloads

The two player ZIPs each contain all 19 recognized input routes, including both
retail HeartGold languages and every previously supported Plus image through
1.2.3. The ZIP language selects the output language. The historical 1.03 Fix
variants remain excluded: no verified input is available. Recognition uses the
whole-file SHA-256; personal modifications and trimmed ROMs are not accepted.

`release.json` is the public input/target/reference contract. `pack.py` builds
and decodes one patch at a time, compares both decoders' output with the pinned
target, deletes temporary decoded ROMs, then writes deterministic ZIPs and
reads every member back. No ROM, save, BIOS or emulator is packaged. Original
PDFs and the trainer reference are checked against independent historical
fingerprints. Cheat codes are inherited unchanged from the pinned 1.2.3 ZIPs;
only their version labels change. `CONTENTS.json` records each member's hash.

## Inputs

- The two 1.2.4 target ROMs, built with `sgp12.costruisci` from your own games.
- The 19 source files you own, matching `release.json`.
- The two unmodified [1.2.3 reference ZIPs](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2.3), with the hashes in `release.json`.
- xdelta3 and Node.js, plus [RomPatcher.js](https://github.com/marcrobledo/RomPatcher.js) checked out at the commit in `release.json`.
- To render the current two-page PDF guides: reportlab 4.4.9. It is only a release-tool dependency, not needed to build the game or run core tests. `guide.py` uses standard PDF fonts and invariant metadata.

Create a private JSON mapping each source ID in `release.json` to its local
path, plus `target-EN` and `target-IT`. Do not commit this mapping or the ROMs.

```sh
python source/distribution/guide.py /path/to/new-guides
python source/distribution/pack.py \
  --inputs /path/to/private-inputs.json \
  --references /path/to/reference-zips \
  --guides /path/to/new-guides \
  --rompatcher /path/to/RomPatcher.js \
  --output /path/to/new-dist
```

The output directory must not exist. On a failure, no release is ready:
inspect the error and use a fresh directory after correcting it. Successful
output includes two named ZIPs, `SHA256SUMS` and `verification.json`. GitHub's
automatic Source code archives are developer source packages; players should
download the named IT or US ZIP.

The original manuals, Game Guide and illustrated 1.2 guides remain historical
references. Current installation instructions, release notes and the 1.2.4
PDF guide are generated from `documents/`. Never translate or rewrite the
original manuals while updating the release's own instructions.

## Checks and scope

```sh
python -m unittest discover -s source/distribution -p test_pack.py
```

File reconstruction is not a runtime test or a save-compatibility campaign.
See [1.2.4 validation](../docs/release-1.2.4.md). No new emulator or device
installation is part of this publishing workflow. The native idle behavior
is covered by the maintenance tests and the limited player report recorded
there; a complete new playthrough has not been performed.
