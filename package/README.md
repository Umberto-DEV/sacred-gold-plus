# Editable player package

`contents/` holds the complete extracted player download, including its real
language folders, guides, patches, optional updaters and historical developer
inputs. It is local and ignored by Git. This README and the composition tool
are public; ROMs, saves and private build inputs never belong in this folder.

## Current 1.3.3 game delivery

Prepare a new 1.3.3 game package with the explicit
[release contract and packager](../source/distribution/README.md#133-single-download).
It selects five final targets, 40 recognized inputs, 200 optional direct updater
routes, five primary patches and 18 PDFs in one `Sacred-Gold-Plus-1.3.3.zip`.
The source inputs, generated documents and output directory are explicit private
CLI arguments. Preserve the current installed language, ROM filename/path and
raw save when using an updater.

The existing seeded `contents/Sacred Gold Plus 1.3.2/` tree and lock retain the
historical document-only workflow below. That lock preserves its exact patches,
cheats and builder inputs; it is not changed by the new versioned delivery.

## Historical 1.3.2: prepare the editable tree once

From the repository root, use the verified corrected package you already have:

```sh
PYTHONPATH=source:source/distribution .venv/bin/python \
  source/distribution/package_workspace.py seed \
  --seed local/releases/1.3.2-corrected/Sacred-Gold-Plus-1.3.2.zip \
  --workspace package
```

The command authenticates the complete ZIP against the frozen
[`package-baseline-1.3.2.json`](../source/distribution/package-baseline-1.3.2.json),
checks safe archive paths and available disk space, then extracts into
`package/contents/`. It records every original member's size and SHA-256 in
`package/.workspace-lock.json`. Keep this private, read-only lock beside the
tree. Existing contents and locks are preserved and refused.

The default seed pin stays fixed to the historical 1.3.2 baseline. Initialize
a different, empty historical workspace only from that exact pinned 1.3.2 ZIP.
The current delivery pointer selects 1.3.3; use the versioned packager above
for that game delivery. An existing 1.3.2 editable tree needs no new seed or
original ZIP for its document-only builds.

## Edit documents and compose

Open `contents/Sacred Gold Plus 1.3.2/`. Each language folder contains its
installation and news PDFs; `Originals/` contains the shared English gameplay
guides. Copy reviewed generated PDFs into these exact locations. The explicit
additional document paths are `Originals/Move-Changes-1.3.2-EN.pdf` and
`Originals/ABOUT-THESE-GUIDES.txt`.

Compose the whole tree with one command:

```sh
PYTHONPATH=source:source/distribution .venv/bin/python \
  source/distribution/package_workspace.py build \
  --workspace package \
  --output local/releases/1.3.2-guides
```

Choose a new output directory for each candidate. The command refuses an
existing output directory. It verifies that every patch, cheat, historical
developer input, instruction and nested optional-updater file still matches
the seeded payload. Only the named guide PDFs and explanatory index may
change; unknown additions and missing original documents are errors. Source
authoring remains under [`source/distribution/`](../source/distribution/).

The command regenerates the root `CONTENTS.json` and `SHA256SUMS`, writes a
deterministic `Sacred-Gold-Plus-1.3.2.zip`, and independently reopens and hashes
every output member. The new output directory also contains `verification.json`
and the complete ZIP checksum. All patch and nested updater bytes are reused;
the 175 routes do not need re-encoding for document edits.

Keep the previous verified ZIP as the fallback until the new candidate passes
document review and package checks. This command prepares local files; release
publication and changes to game behavior use their separate validation process.

## Limits and tests

The tool accepts at most 2 GiB of expanded files and 2,048 archive entries, and
preserves at least 10 GiB of free disk space. Symlinks, special files, traversal,
portable filename aliases and duplicate ZIP entries are refused. Failed outputs
are removed while the editable input tree and previous builds are preserved.

```sh
PYTHONPATH=source:source/distribution .venv/bin/python \
  -m unittest source/distribution/test_package_workspace.py
```

The ROM-free tests cover archive boundaries, payload tampering, missing and
unexpected documents, deterministic rebuilds and preservation of existing files.
