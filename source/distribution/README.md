# Reproduce the 1.3.1 player downloads

Use `release-1.3.1.json` with `--contract` for the current release. It includes
25 authenticated input routes per output language and omits unverified legacy
cheat codes. Build the target images with the [1.3.1 source workflow](../README.md),
then render the four illustrated PDFs and run the packager:

```sh
python source/distribution/guide.py /path/to/new-guides --contract source/distribution/release-1.3.1.json
python source/distribution/pack.py --contract source/distribution/release-1.3.1.json \
  --inputs /path/to/private-inputs.json --references /path/to/reference-zips \
  --guides /path/to/new-guides --rompatcher /path/to/RomPatcher.js \
  --output /path/to/new-dist
```

The two `SGP-Source-References-EN.zip` / `SGP-Source-References-IT.zip` archives
are developer inputs linked and authenticated by both contracts. They preserve
the original manuals, license and legacy cheat reference bytes, without an old
player patch or ROM. The 1.3.1 package omits those legacy cheats; their retained
reference bytes allow the historical 1.2.5 contract to remain reproducible after
older player downloads are retired. Do not install the reference archives as games.

## Historical 1.2.5 contract

The sections below describe `release.json` and its 21 routes. Its reference
container URLs now point to the frozen source-reference archives; the consumed
manual/license/cheat member bytes are unchanged.


The two player ZIPs each contain all 21 recognized input routes, including both
retail HeartGold languages and every previously supported Plus image through
1.2.4. The ZIP language selects the output language. The historical 1.03 Fix
variants remain excluded: no verified input is available. Recognition uses the
whole-file SHA-256; personal modifications and trimmed ROMs are not accepted.

`release.json` is the public input/target/reference contract. `pack.py` builds
and decodes one patch at a time, compares both decoders' output with the pinned
target, deletes temporary decoded ROMs, then writes deterministic ZIPs and
reads every member back. No ROM, save, BIOS or emulator is packaged. Original
PDFs and the trainer reference are checked against independent historical
fingerprints. For the historical 1.2.5 contract, cheat codes are inherited unchanged from the frozen reference archives;
only their version labels change. `Patch/CONTENTS.json` records each member's hash.
Each reference ZIP is opened without following its final symlink, snapshotted
once with a 256 MiB container limit, and hashed before those exact snapshot
bytes are parsed. The packager never authenticates one open file and consumes
a later pathname. Selected reference members now have an 8 MiB individual
and 32 MiB aggregate decompression limit. Only STORED/DEFLATED members are
accepted, because those Python backends honor the bounded read. Unused patch
members and omitted cheats are not decompressed. Names are checked before
insertion and after version relabeling: traversal, Windows aliases and
case/Unicode/file-directory collisions fail before an output ZIP is opened.
An exact inherited name may be replaced only by an explicit project-authored
document overlay, preserving the current cheat notice.

## Inputs

- The two 1.2.5 target ROMs, built with `sgp12.costruisci` from your own games.
- The 21 source files you own, matching `release.json`.
- The two frozen [source-reference ZIPs](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.3.1), with the hashes in `release.json`.
- xdelta3 and Node.js, plus [RomPatcher.js](https://github.com/marcrobledo/RomPatcher.js) checked out at the commit in `release.json`.
- To render the four current illustrated player PDFs: reportlab 4.4.9. It is only a release-tool dependency, not needed to build the game or run core tests. `guide.py` renders the installation and current-feature texts in each language, including all source and target fingerprints in the installation PDFs. It uses standard PDF fonts, invariant metadata and the real website captures in `images/install-*.jpg`. No screenshot contains a loaded ROM.

`--rompatcher` must name the checkout root, not a symlink or a directory nested
inside another repository. The packager verifies the literal commit object,
recursively verifies every tree/blob object by its Git SHA-1, rejects links and
unsupported entries, and materializes those committed bytes in a new private
temporary directory. Every Node decoder uses that one snapshot. Modified,
ignored, index-hidden and untracked working-tree files are therefore never
executed; they need not be deleted to obtain the pinned result. Lazy object
fetching is disabled, so a partial clone with missing objects fails closed
instead of invoking a checkout-configured remote helper. The
`verify-rompatcher.cjs` script is an internal helper and is not a standalone
authenticator for arbitrary checkout paths.

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

Every ZIP has one explicit `Sacred Gold Plus 1.2.5/` root on both Windows and
macOS. Start with `How-to-install-1.2.5-EN.pdf` or `Come-installare-1.2.5-IT.pdf`.
The matching `Whats-New-1.2.5-EN.pdf` / `Novita-1.2.5-IT.pdf` sits beside it.
No root README or installation TXT competes with those entry points.
Credits are included in the PDFs. The root texts under `documents/` are
authoring sources only, not ZIP members. Old installation and feature-overview
PDFs are omitted from the new packages; original gameplay manuals remain
unchanged under `Manual/`.

Patch paths are grouped as `Patch/From Clean ROM/{US,IT}/` or
`Patch/From Plus <version>/{US,IT}/`, with additional variant folders for
1.04 and 1.2.2. Legacy 1.01-1.03 only have a verified US input. Folder languages
identify the **source**, while the ZIP edition identifies the **target**.
Manifest and inventory paths are relative to the versioned root, not to the
folder containing their JSON file. `install_text()` refuses packaging if a
source, target fingerprint or patch path is missing from the current guide.

The four 1.2.5 PDFs are generated from `documents/`. Never translate or rewrite the
original manuals while updating the release's own instructions.

## Checks and scope

```sh
python -m unittest discover -s source/distribution -p test_pack.py
```

File reconstruction is distinct from game and save validation. See the
[1.2.5 validation](../docs/version-1.2.5.md) for the final build, title-screen,
menu and older-save tests. Every package route is decoded using two independent
decoders. Existing original manuals and their fingerprints remain unchanged.

## Player-facing release pages

Use [RELEASE-NOTES-TEMPLATE.md](RELEASE-NOTES-TEMPLATE.md) for every release.
The page introduces the current game with its features, screenshots, downloads
and credits. Keep maintenance notes to **Some bugs fixed.**; retain the detailed
technical record in `CHANGELOG.md` and the release validation document. Update the
feature overview when the game gains or changes a feature.

Replace `{{VERSION}}` with the published version and `{{IMAGE_BASE_URL}}` with the
image directory URL at a full, published commit SHA. Review the screenshots and
their captions against `images/captures.json`, and check every link before
publishing. Refresh any screenshot that displays an older version number.
Only update the release description when refreshing its presentation;
published ZIPs, checksums and tags remain immutable.

## Preparing the 1.3.1 package

`release-1.3.1.json` is an explicit, separate contract for the current EN/IT
manual-test candidates. The default `release.json` and default commands still
select published 1.2.5. The new contract keeps all 21 old sources and adds the
two 1.2.5 and two device-V1.3 inputs: 25 routes per ZIP. Whole-file hashes select
inputs; labels and filenames alone do not. Targets are pinned to the manual
candidate identities in [validation](../docs/ui-1.3.1-validation.md).

This is **offline preparation, not release acceptance**. The contract currently
targets EN `02cccfbf…bf0af` (152,786,376 bytes) and IT `35d459e3…088f4`
(159,029,292 bytes), with portable storage as the only newly active owner.
These successors include the `legendary-scene-version` repair. The bounded local
Box and IT Android SAVE/cold receipts for EN `5c561184…2f15` / IT
`c5a45d16…77f97` remain historical evidence for those predecessors; they do not
accept the new target identities. Neither current target has completed the
physical-device update gate. The package remains **not publishable until the
exact IT successor is validated on the maintainer's physical device**. The older Italian
`171b53b6…9d64a0` installed on the maintainer's device is only the rollback
predecessor and must not be used as the release target.

Under the maintainer's 5 November instruction, the player ZIPs, PDFs,
manifests and checksums may be rebuilt now as a private offline draft against
the current contract. This does not accept the package for release: the exact
IT successor must still pass the conservative physical-device update before
publication. Candidate-bound screenshots must be refreshed or requalified.
The verified private draft is US `99f3e7d3…d23e` (331,419,164 bytes) and IT
`fbe6109c…204d` (354,446,308 bytes), 39 members and 25 routes per ZIP. Its
exact receipts are in [package validation](../docs/package-1.3.1-validation.md).
Preserve published 1.2.5 assets and tags. Do not publish without the
maintainer's explicit approval, and do not publish the outgoing local history
until its private intermediate files have been reconciled without changing
published history.

```sh
python source/distribution/guide.py /path/to/new-guides \
  --contract source/distribution/release-1.3.1.json
python source/distribution/pack.py \
  --contract source/distribution/release-1.3.1.json \
  --inputs /path/to/private-inputs.json \
  --references /path/to/reference-zips --guides /path/to/new-guides \
  --rompatcher /path/to/RomPatcher.js --output /path/to/new-dist
python -m unittest discover -s source/distribution -p 'test*.py'
```

Use the same mapping format as above, with every source ID and `target-EN` /
`target-IT`. No ROM build or new emulator test is part of packaging. Each route
is decoded by xdelta3 and pinned RomPatcher.js, compared with its exact target,
and the temporary decoded ROM is deleted immediately. ZIPs have one
`Sacred Gold Plus 1.3.1/` root, two current PDFs, verified original manuals,
license, patches, manifest and inventory. `documents/1.3.1/` contains authoring
sources; original gameplay PDFs remain unchanged and credited.

Legacy cheat codes are deliberately **omitted**, because their effect has not
been checked on these exact images. `Cheats/` contains language-specific
instructions, without relabelled catalogues. Native game tools require no cheat.
The [bug list](../../BUG-FIXES-1.3.1.md) stays in the repository, not a third PDF.
The release template presents all current game features; its only maintenance
line remains **Some bugs fixed.** Existing 1.3.1 images are development
captures from earlier candidate identities and must not be represented as
current-candidate evidence without refresh or requalification. Replace the
image placeholder with a full source commit only after that commit is published;
links to a prepared but unpublished commit remain a publication gate.

## Source archives

GitHub automatically adds Source code ZIP/tar.gz links to every release; they
cannot be removed as uploaded assets. Direct player-download links are placed
at the beginning of the release description and in the README. Local assistant
instructions, skills and internal plans are ignored and removed from the
tracked index; the public-file check rejects accidental reintroduction.
Previously published Git history and the `v1.2.5` tag are not rewritten.

## Installation references

Checked on 27 October 2026:

- [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) and its
  [source](https://github.com/marcrobledo/RomPatcher.js): browser field names,
  xdelta support and local processing. SHA-1 shown there is not SHA-256.
- [SHA256 File Checksum](https://emn178.github.io/online-tools/sha256_checksum.html):
  File/Hex mode with HMAC off, calculated locally in the browser.
- [Microsoft Get-FileHash](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash):
  SHA256 and LiteralPath for filenames containing wildcard characters.
- [xdelta](https://github.com/jmacd/xdelta): optional command-line alternative.
- [Dumping your game cartridge](https://3ds.hacks.guide/dumping-titles-and-game-cartridges.html#dumping-a-game-cartridge):
  NDS cartridge copying on a console already configured for GodMode9.
- [GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases):
  automatic source archive links belong to the release tag.

### Reproducing the private trial identity

[reproduction-1.3.1.json](reproduction-1.3.1.json) records the exact V1.3 input,
UI calibration, per-language inert owner configuration, inert hash and six
manual activation fields. It contains data and hashes only, no game bytes or
personal paths. It describes a **manual test trial**, not an alternate route to
production acceptance.

That recipe preserves an earlier trial identity. It does not reproduce the
current `release-1.3.1.json` targets or provide evidence for their physical-device gate.

Generate private `ui.json` and `mechanics-EN.json` / `mechanics-IT.json` from
its `ui_config` and `languages.<language>.mechanics_config` objects. Rebuild the
V1.3 base using the [successor builder](../sgp13/README.md), checking its entire
hash against the recipe. Initialize `sgp131.workbench` with the two exact V1.3
inputs, then build each language through `identity` using those private JSON
files and the pinned external charmap. All archive deltas and native owners are
derived by the builder. An output that differs from `inert_sha256` is not this
candidate and must not be activated under this recipe.

For the named manual test only, the following transformation is fully pinned.
`language` is `EN` or `IT`, and `inert_path` / `output_path` are private paths.
It creates no production proof or acceptance receipt. Production activation
continues to require candidate-bound measured evidence.

```python
import hashlib, json
from pathlib import Path
recipe = json.loads(Path('source/distribution/reproduction-1.3.1.json').read_text())
row = recipe['languages'][language]
raw = inert_path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == row['inert_sha256']
trial = bytearray(raw)
for field in row['manual_activation_fields']:
    at, size = field['rom_offset'], field['bytes']
    assert raw[at:at+size] == bytes(size)
    trial[at:at+size] = (1).to_bytes(size, 'little')
assert hashlib.sha256(trial).hexdigest() == row['target']['sha256']
with output_path.open('xb') as stream:
    stream.write(trial)
```

No new full source-to-ROM rebuild was run while preparing these packages. The
recorded candidate readbacks and earlier code checks remain scoped to the
[validation report](../docs/ui-1.3.1-validation.md); this recipe makes the build
inputs and manual delta reviewable rather than claiming a new runtime result.
