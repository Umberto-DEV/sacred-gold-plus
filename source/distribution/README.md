# Reproduce player downloads

## Current corrected 1.3.2 package

The current schema-3 contract is `release-1.3.2-r4.json`; its internal revision
identifies the corrected game targets and leaves the frozen r2/r3 contracts
unchanged. The public title is **Sacred Gold Plus 1.3.2**, tag **1.3.2**, with
one attached file: **Sacred-Gold-Plus-1.3.2.zip**. Source is available in GitHub;
no source archive is attached.

```text
Sacred-Gold-Plus-1.3.2.zip
  Sacred Gold Plus 1.3.2/
    START-HERE.txt
    <five language folders>/
      Installation-1.3.2-<locale>.pdf
      Whats-New-1.3.2-<locale>.pdf
      Patch/<one matching clean-ROM patch>
      Cheats/<three localized files>
      Credits-and-Licenses/{ABOUT.txt,LICENSE.txt}
    Originals/<seven shared English gameplay PDFs>
    Optional-Updaters/
      <five language folders>/
        README-Updater.txt
        Patch/<35 exact-source patches>
        manifest.json
        Credits-and-Licenses/{ABOUT.txt,LICENSE.txt}
      README.txt
      manifest.json
      CONTENTS.json
      SHA256SUMS
    Developer-Inputs/<four immutable historical builder files, README.txt>
    CONTENTS.json
    SHA256SUMS
```

The five primary patches require the matching unmodified retail language. The
optional folder holds all **175** direct routes from **35** recognized sources
to the five current targets, including the five original 1.3.2 outputs. These
are starting identities, not additional installed versions. Every route is
freshly encoded and decoded with both xdelta3 and pinned Rom Patcher JS, then
compared with the full target hash. The five primary patches reuse their exact
verified clean-source routes. Preserve the current language, installed filename
and path, raw save, progress and Plus settings when updating.

Generate the ten localized installation/news PDFs with
`render_player_documents`, the seven shared EN PDFs with `render_shared_guides`,
and all fifteen cheat files with `localization.cheats.generate`, using the exact
new targets and clean retail baselines. The `p:unified:*` text is selected only
for the combined package; historical `d:*` and `p:r2:*` copy and renderer bytes
are preserved. The five installation PDFs retain the real patcher screenshots,
links, full input/output fingerprints and copied-save update procedure.

The package also preserves two `base-1.1-<locale>.xdelta` files and two
`SGP-Source-References-<locale>.zip` files byte for byte. `build-inputs.json`
records their immutable identities. `build-input-delivery.json` independently
pins the complete final ZIP and exact member paths; it is tracked in source
and deliberately excluded from the ZIP, avoiding a recursive container hash.
Only pinned regular members are copied, with bounded transfer, complete ZIP
hash authentication, per-member size/hash checks and atomic publication.
Existing different files and links are preserved and refused.

Use a private existing destination and reuse the downloaded ZIP:

```sh
PYTHONPATH=source python source/distribution/download_inputs.py \
  --destination /path/to/private-inputs --container /path/to/Sacred-Gold-Plus-1.3.2.zip
cd source && ../.venv/bin/python -m sgp12.scarica_base \
  --destinazione "$SGP_ROM_DIR" --container /path/to/Sacred-Gold-Plus-1.3.2.zip
```

Without `--container`, either downloader obtains the pinned single ZIP on demand
and removes the temporary container after extraction. Exact files already in
place are reused without another large transfer. The first command copies all
four builder inputs; `--file <basename>` selects particular files. The second
copies only the requested EN/IT stage-zero deltas. The current build still reads
your own retail ROM; no ROM or save is downloaded.

Rebuild the player ZIP with the common `pack.py` command below, selecting
`--contract source/distribution/release-1.3.2-r4.json`, a private mapping of all
35 sources plus five targets, and `--references` pointing to the directory of
those four builder files. Schema 3 authenticates the documents and builder
inputs before creating output. Package reconstruction is separate from
[game and raw-save acceptance](../docs/validation/guide-opening-1.3.2.md).

## Historical 1.3.2 package revision r3

Use **schema 3**, `release-1.3.2-r3.json`. It preserves the five accepted 1.3.2
target ROMs and the same 30 recognized source identities. The two downloads are:

```text
Sacred-Gold-Plus-1.3.2-r3-Multilingual.zip
  Sacred Gold Plus 1.3.2/
    START-HERE.txt
    EN-English/                  # also IT-Italiano, FR-Francais, ES-Espanol, DE-Deutsch
      Installation-1.3.2-EN.pdf
      Whats-New-1.3.2-EN.pdf
      Patch/Sacred-Gold-Plus-1.3.2-EN.xdelta
      Cheats/<three localized files>
      Credits-and-Licenses/{ABOUT.txt,LICENSE.txt}
    Originals/<seven current English gameplay PDFs, one Game Guide>
Sacred-Gold-Plus-1.3.2-r3-Optional-Updaters.zip
  Sacred Gold Plus 1.3.2 Optional Updaters/
    README.txt
    <language folder>/
      README-Updater.txt          # localized source hashes, sizes and patch names
      Patch/<30 patches naming target 1.3.2, language and source ID>
      Credits-and-Licenses/{ABOUT.txt,LICENSE.txt}
      manifest.json
    manifest.json
    CONTENTS.json
    SHA256SUMS
```

The main ZIP has exactly five same-language clean-ROM patches and no `Documents`
folders, JSON inventories or internal checksums. All 150 historical-source
updaters remain in the optional ZIP. Its readable localized tables make JSON
parsing unnecessary. Older version labels identify inputs, never old outputs.

Schema 3 retains the source/target/route/decoder identities and cheat pins from
schema 2, adds `package_revision: "r3"`, two `documents` pins per locale,
seven EN `shared_documents` pins and a canonical `license` pin. It omits
`references` and `original_documents`: historical ZIPs are not imported. Every
language gets the unchanged complete English GPLv3 plus localized explanations.

Use `reference_docs.render_player_documents(...)` for each locale and
`render_shared_guides(...)` for EN, with the exact candidate, matching clean retail
baseline and character map. The latter updates the obsolete packaging notice;
gameplay text and page counts stay unchanged. Current `p:r2:*` authoring keys
overlay the historical `d:*` catalogue only through these explicit APIs. The
default renderer and historical contracts retain their behavior. Pin complete
PDF/cheat hashes and sizes in the new contract. Put two PDFs and `Cheats/` under
`--guides/<locale>/`, with the seven shared guides beside the two EN PDFs.
The current installation walkthrough restores the authentic Rom Patcher JS
screenshots in `images/install-rom-patcher.jpg` and
`images/install-patcher-settings.jpg`, with their original capture date. It
explains extraction, file selection, full SHA-256 checks, patcher settings,
copied-save validation and installation separately for Windows and macOS.

```sh
PYTHONPATH=source python source/distribution/pack.py \
  --contract source/distribution/release-1.3.2-r3.json \
  --inputs /path/to/private-inputs.json --references /path/to/unused-references \
  --guides /path/to/current-documents --rompatcher /path/to/RomPatcher.js \
  --output /path/to/new-dist
```

`--references` remains required by the common CLI but is unused by schema 3.
The private mapping supplies the same 30 source IDs and five `target-<locale>`
paths as schema 2. Wrong identities or stale/missing files fail admission.
Each route is generated once and decoded with xdelta3 and pinned Rom Patcher JS,
checking the complete target hash; the primary patches reuse five verified
patches. Both ZIPs are reopened and compared with complete member maps and must
be below 2 GiB each. External checksums and verification metadata cover both.
See [package validation](../docs/validation/package-1.3.2-r3.md); existing
[game acceptance](../docs/validation/localization-1.3.2.md) remains unchanged.
For the release-page template, use `VERSION=1.3.2`, `PACKAGE_VERSION=1.3.2-r3`
and `RELEASE_TAG=v1.3.2-r3`; the package revision does not change the game label.

```sh
cd source/distribution
PYTHONPATH=.. ../../.venv/bin/python -B -m unittest discover -p 'test*.py'
```

Schema 3 also retains support for the frozen r2 contract. The `p:r2:*` locale
namespace names the shared layout; the installation asset basename is formatted
from the selected package revision. Revision r3 preserves all game/patch bytes.

The current release also rehosts four source inputs, byte for byte:
`base-1.1-EN.xdelta`, `base-1.1-IT.xdelta`,
`SGP-Source-References-EN.zip` and `SGP-Source-References-IT.zip`.
The base downloader uses the r3 delivery URLs. Historical contracts keep their
original provenance URLs; obtain their locally supplied reference ZIPs from the
current r3 release and compare the unchanged contract hashes. Bootstrap source
reconstruction uses a literal reachable commit and does not depend on old tags.

## Historical contracts

The sections below describe the frozen schema-1/schema-2 layouts, not the
current r3 player ZIP. The tools keep schema 1 as their backward-compatible
default; selecting the current contract explicitly is required.

This directory retains the **published 1.3.1** package contract and supports
an explicit multilingual schema-2 contract for 1.3.2. Reproduce published 1.3.1
outputs from their published source revision; do not relabel that contract or
treat a development ROM as its historical target. A successor package needs its
own versioned contract, exact accepted ROM hashes and freshly generated documents.

`release-1.3.1.json` is the current default contract for `pack.py` and `guide.py`.
It authenticates 25 input routes per output language, the two output ROMs,
original reference documents and the independent patch decoder. Unverified
legacy cheat catalogues are omitted. Build the target ROMs with the
[current source workflow](../README.md).

## Historical multilingual 1.3.2 schema-2 contract

`pack.py` also accepts an explicit **schema 2** contract for the five-language
1.3.2 successor. The default remains the immutable schema-1 1.3.1 contract.
Schema-2 packaging support does not accept a ROM, runtime result or release by
itself: the supplied versioned contract must pin the exact accepted candidates.
Do not reuse published 1.3.1 target hashes as 1.3.2 identities.

The schema-2 contract contains:

- `version: "1.3.2"`, five `targets` keyed by EN, IT, FR, ES and DE, each with
  complete `sha256` and `bytes` (an optional `name` must be a basename).
- `sources`: all 30 recognized bases: the immutable 1.3.1 contract's 25
  sources, its two published target ROMs under `plus-1.3.1-en` and
  `plus-1.3.1-it`, and `clean-fr`, `clean-es` and `clean-de` from the retail
  language registry. Every source hash and size must match this independent
  registry; unknown bases and repinned known IDs are rejected. Each row contains
  exactly `id`, `label`, `sha256` and `bytes`; local paths belong only in the
  separate private input mapping.
- `routes_by_target`: five explicit lists, each containing all 30 source IDs
  exactly once, for 150 routes. Every recognized historical base can produce
  any of the five latest language targets. The output folder and target hash
  identify the chosen language; the starting ROM's language does not constrain
  that choice. Missing historical routes, unknown IDs, duplicate IDs and extra
  target locales are rejected. The packager uses these declared lists directly
  and never silently expands them. The schema-1 25-by-two contract is unchanged.
- `locales`: one row per locale, with its exact `folder` from
  `source/localization/languages.json` and a `documents` list containing all
  nine `{name, sha256, bytes}` PDF pins, in renderer order. The names are
  `Installation`, `Whats-New`, `Special-Events`, `Pokemon-Changes`,
  `Pokemon-Locations`, `Evolutions`, `Items-TMs`, `Trainers` and `Game-Guide`,
  each followed by `-1.3.2-<locale>.pdf`. Each locale also requires a nonempty
  `cheats` list of `{name, sha256, bytes}` pins. These are portable basenames
  ending in `.txt`, `.xml`, `.mch` or `.cht`; duplicate names, path aliases, ROM
  filenames and files larger than 8 MiB are rejected. A translated notice may be
  the sole file until a revision-verified catalogue is available.
- The existing pinned EN/IT `references`, `original_documents` and
  `rompatcher_commit`. Each shared original document pin also declares its
  actual `language` (EN for the original shared Drayano manuals). The cheat
  policy is `omit-unverified` or `verified-localized`. No old cheat catalogue
  is inherited from a reference ZIP.

The private `--inputs` mapping supplies exactly the declared source IDs and all
five `target-<locale>` paths. Supply generated PDFs under `--guides/<locale>/`
and the contract-listed cheat files under `--guides/<locale>/Cheats/`. Only
listed files are packaged. Missing, stale, altered or wrong-language PDFs,
missing/changed cheat files and wrong source/target bytes fail before an output
folder is created. Every PDF's complete bytes and size must match its contract
pin; a filename or PDF signature alone is insufficient. The existing no-follow guide readers, authenticated
reference snapshots, archive-name checks and pinned decoder snapshot remain
in use. Schema 2 reads current authored package notices from the separate
locale document catalogues; there is no English fallback or dependency on
`SGP_PLAYER_DOCUMENTS_DIR` authoring text.

The result is one `Sacred-Gold-Plus-1.3.2-Multilingual.zip`. Its only output
games are the five 1.3.2 targets; older versions appear solely as authenticated
patch input identities. Choose the desired output language explicitly, then
follow the installation guide to retain the installed ROM filename/path and
its raw-save association. The ZIP has this layout:

```text
Sacred Gold Plus 1.3.2/
  START-HERE.txt
  manifest.json
  CONTENTS.json
  SHA256SUMS
  EN-English/                  # also IT-Italiano, FR-Francais, ES-Espanol, DE-Deutsch
    Patch/<source-id>.xdelta
    Patch/manifest.json
    Patch/CONTENTS.json
    Documents/<nine localized PDFs>
    Cheats/<contract-pinned localized files>
  Originals/<unchanged shared manuals, once each>
  Originals/EN-English/Game Guide.txt
  Originals/IT-Italiano/Game Guide.txt
  Originals/CONTENTS.json      # original language and fingerprints
  Credits-and-Licenses/<locale>/ABOUT.txt
  Credits-and-Licenses/EN-English/LICENSE.txt
  Credits-and-Licenses/IT-Italiano/LICENZA.txt
```

All 150 routes use a bounded 256 MiB xdelta3 source-search window, covering
every admitted source instead of repeatedly embedding distant unchanged data.
Secondary compression stays disabled for standard Rom Patcher JS compatibility.
The finished player ZIP must remain under GitHub's 2 GiB per-asset limit; an
oversized output is rejected before its verification receipt is produced.
Routes are decoded sequentially with xdelta3, independently
decoded with the pinned RomPatcher.js snapshot, and checked against its entire
exact target hash. Temporary reconstructed ROMs and patches are removed even
on decoder failure. Every input is rechecked before the ZIP is finalized.
The ZIP is reopened and compared with the complete member map. Root
`SHA256SUMS` covers all members except itself; `CONTENTS.json` lists all
other members except those two root inventory files, naming the exclusions
explicitly. An external checksum and verification report identify the finished
ZIP. These are file-reconstruction results; Continue/native SAVE/cold restart
acceptance remains separate.

Focused checks, including the unchanged published schema-1 behavior:

```sh
cd source/distribution
PYTHONPATH=.. ../../.venv/bin/python -B -m unittest test_multilingual_pack test_pack test_release131 test_document_sources -v
```

## Historical 1.3.1 player-document sources

The following authoring and two-ZIP instructions describe schema 1 and the
published 1.3.1 revision only. Current 1.3.2 uses the explicit schema-2 contract
above and public `localization/locales/<locale>/documents.json` sources for all
five languages; it does not use the private Italian-only authoring arrangement.

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

## Historical 1.3.1 required inputs

- The two current 1.3.1 target ROMs and 25 supported source ROMs that you own,
  matching the complete contract hashes. No ROM or personal save is committed.
- The frozen `SGP-Source-References-EN.zip` and
  `SGP-Source-References-IT.zip` from the
  [current source-input delivery](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.3.2-r3).
  They preserve original manuals, licenses and reference bytes, and are not
  player game installations.
- xdelta3, Node.js and a local
  [RomPatcher.js](https://github.com/marcrobledo/RomPatcher.js) checkout at the
  exact contract commit.
- ReportLab 4.4.9 for illustrated PDFs and distribution preflight tests.
  It is pinned in `source/requirements.txt`; game compilation does not use it.
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

## Historical 1.3.1 output and validation

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

## Historical 1.3.1 package revision 2

That release tag is `v1.3.1-r2`, while the game and player-guide version
remain 1.3.1. The revision updates public source documentation and download
locations. Native target ROM and input fingerprints are unchanged. Stage-zero
base deltas remain required current build inputs; their bytes and pins are
preserved when hosted with the latest package. The complete release checksum
list includes both deltas and is accepted by the existing pinned downloader.
