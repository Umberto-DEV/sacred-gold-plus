# Editable player package

`contents/` holds the complete extracted player download, including its real
language folders, guides, patches, optional updaters and historical developer
inputs. It is local and ignored by Git. This README and the composition tool
are public; ROMs, saves and private build inputs never belong in this folder.

## Prepare the editable tree once

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

The default pin deliberately stays fixed when a newer documentation package
changes the download hash. To initialize a *different, empty workspace* from
the current published package, supply
`--delivery source/distribution/build-input-delivery.json` and its matching ZIP.
An existing editable tree needs no new seed or original ZIP for normal builds.

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
