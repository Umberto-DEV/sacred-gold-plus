# Reproduce the current 1.3.1 player downloads

`release-1.3.1.json` is the current default contract for `pack.py` and `guide.py`.
It authenticates 25 input routes per output language, the two output ROMs,
original reference documents and the independent patch decoder. Unverified
legacy cheat catalogues are omitted. Build the target ROMs with the
[current source workflow](../README.md).

## Player-document sources

Public documentation and bundled authoring texts are English. Italian player
PDFs and notices remain available in the Italian download package. Their
authoring sources are maintained outside the public tree.

To regenerate both language packages, prepare a private document directory
containing `EN/` and `IT/`, using the existing English source layout as the
structure. Set `SGP_PLAYER_DOCUMENTS_DIR` to its absolute path. Each language
needs installation and current-feature text plus its `Cheats/` and `Manual/`
notices. Keep original Italian translations in this private directory; do not
add them to the Git index. The installation text must name every contract
source SHA-256/patch path and the language's exact output SHA-256. Missing
localizations fail with a clear error rather than silently substituting English.
The override changes only the authoring input location, never the public
contract or the published release identity.

```sh
export SGP_PLAYER_DOCUMENTS_DIR=/path/to/private-player-documents
python source/distribution/guide.py /path/to/new-guides
python source/distribution/pack.py \
  --inputs /path/to/private-inputs.json --references /path/to/reference-zips \
  --guides /path/to/new-guides --rompatcher /path/to/RomPatcher.js \
  --output /path/to/new-dist
```

An explicit `--contract source/distribution/release-1.3.1.json` is also accepted.
The output directory must be new. Do not overwrite published ZIPs, PDFs,
checksums or tags: corrected player assets require a new release. Existing
published 1.3.1 assets are immutable and retain the hashes recorded in their
release manifest.

## Required inputs

- The two current 1.3.1 target ROMs and 25 supported source ROMs that you own,
  matching the complete contract hashes. No ROM or personal save is committed.
- The frozen `SGP-Source-References-EN.zip` and
  `SGP-Source-References-IT.zip` from the
  [current release](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.3.1-r2).
  They preserve original manuals, licenses and reference bytes, and are not
  player game installations.
- xdelta3, Node.js and a local
  [RomPatcher.js](https://github.com/marcrobledo/RomPatcher.js) checkout at the
  exact contract commit.
- reportlab 4.4.9 to render illustrated PDFs. It is a release-tool dependency,
  separate from game compilation and core tests.
- The private authoring bundle described above. The public English documents
  remain under `documents/1.3.1/EN/`.

Create a private JSON mapping each contract source ID to its local path,
plus `target-EN` and `target-IT`. Older input versions are upgrade routes into
1.3.1; they are not additional published output packages. Preserve the original
inputs and saves. The two 1.04 camera variants and two 1.2.2 editions remain
distinct routes. Unsupported trimmed/modified ROMs and unverified 1.03 Fix
variants are rejected.

## Packaging and integrity boundaries

The packager verifies all inputs before allocating its output, creates one
patch at a time and decodes it with both xdelta3 and the pinned JavaScript
decoder. Each complete decoded output must match the target SHA-256. Temporary
ROMs are removed, deterministic ZIPs are read back, and
`Patch/manifest.json` plus `Patch/CONTENTS.json` identify every route/member.
Original gameplay manuals and licenses retain their original bytes and credits.
No ROM, save, BIOS or emulator is included in the player ZIP.

Reference ZIPs are opened without following their final symlink and read from
one authenticated snapshot. Limits are 256 MiB per container, 8 MiB per selected
member and 32 MiB aggregate decompression. Only STORED/DEFLATED input members are
accepted; unused patches and omitted cheats are never decompressed. Traversal,
Windows device aliases, case/Unicode aliases and file/directory collisions fail
before writing an output ZIP. Only explicit authored document overlays can
replace the same inherited name.

RomPatcher.js is materialized from the literal pinned Git commit. Tree/blob
identities, regular entries and checkout boundaries are checked recursively;
symlinks, nested checkout roots and unsupported entries are rejected. Lazy
object fetching is disabled. Working-tree edits, ignored/untracked files,
index-hidden changes and repository-configured filesystem helpers are not
executed. Every decoder process uses the single private committed snapshot.

Player PDF directories and individual files are opened with no-follow checks
and retained descriptors. Player authoring text and nested notices use the same
regular-file/no-symlink reader, including an explicit private document bundle.
No source-directory path is added to the release manifest.

## Current output and validation

Each language ZIP has one `Sacred Gold Plus 1.3.1/` root with its two current
PDFs and `Patch/`, `Manual/` and `Cheats/`. The ZIP selects the final language;
`US`/`IT` patch subfolders identify the starting ROM. The packager emits the
English/Italian ZIPs, `SHA256SUMS` and a verification report. File reconstruction
is separate from Continue/native SAVE/cold-restart acceptance.

```sh
cd source/distribution
../../.venv/bin/python -m unittest test_document_sources test_pack test_release131 -v
```

The tests cover current defaults, private localization inputs, source-route
identity, both PDF names, original-document retention, omitted legacy codes,
archive aliases, decompression budgets, reference snapshots, safe guide files
and pinned decoder execution. Synthetic localized fixture text is English;
Italian authoring content is not required by public CI. Actual translated
release PDFs keep their separate human/visual review requirement.

## Package revision 2

The current release tag is `v1.3.1-r2`, while the game and player-guide version
remain 1.3.1. The revision updates public source documentation and download
locations. Native target ROM and input fingerprints are unchanged. Stage-zero
base deltas remain required current build inputs; their bytes and pins are
preserved when hosted with the latest package. The complete release checksum
list includes both deltas and is accepted by the existing pinned downloader.
