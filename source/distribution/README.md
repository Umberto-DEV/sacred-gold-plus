# Reproduce the 1.2.5 player downloads

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
fingerprints. Cheat codes are inherited unchanged from the pinned 1.2.3 ZIPs;
only their version labels change. `Patch/CONTENTS.json` records each member's hash.

## Inputs

- The two 1.2.5 target ROMs, built with `sgp12.costruisci` from your own games.
- The 21 source files you own, matching `release.json`.
- The two unmodified [1.2.3 reference ZIPs](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2.3), with the hashes in `release.json`.
- xdelta3 and Node.js, plus [RomPatcher.js](https://github.com/marcrobledo/RomPatcher.js) checked out at the commit in `release.json`.
- To render the four current illustrated player PDFs: reportlab 4.4.9. It is only a release-tool dependency, not needed to build the game or run core tests. `guide.py` renders the installation and current-feature texts in each language, including all source and target fingerprints in the installation PDFs. It uses standard PDF fonts, invariant metadata and the real website captures in `images/install-*.jpg`. No screenshot contains a loaded ROM.

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

## Source archives

GitHub automatically adds Source code ZIP/tar.gz links to every release; they
cannot be removed as uploaded assets. Direct player-download links are placed
at the beginning of the release description and in the README. `.gitattributes`
excludes `AGENTS.md` and `CLAUDE.md` from newly generated archives of revisions
containing that rule, while keeping the instructions in the Git checkout.
The archive-mode public-file check accounts for exactly those omissions.
The existing `v1.2.5` tag is not moved: its source archives still reflect its
original tree. A push to main cannot change those old archives.

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
