# release/1.2 — the downloadable package

This folder **is** the 1.2 download, laid out as files. `IT/` and `EN/` hold
exactly what a player gets, one folder per language; `build_zip.py` packs each
of them into a ZIP.

```sh
python3 -B release/1.2/build_zip.py
# -> release/1.2/dist/Sacred-Gold-Plus-1.2-IT.zip
# -> release/1.2/dist/Sacred-Gold-Plus-1.2-US.zip
```

`dist/` is not tracked: the ZIPs are rebuilt from the files next to them, so
anyone can repack this folder and compare the result, byte for byte, with the
published download. The archives are deterministic — fixed timestamps, fixed
permissions, sorted members — so two runs give the same bytes.

## What is inside each language folder

| Path | What it is |
| --- | --- |
| `LEGGIMI.txt` / `README.txt` | What the download is, what it is not, credits |
| `COME-INSTALLARE.txt` / `HOW-TO-INSTALL.txt` | Applying the patch, step by step |
| `NOVITA-1.2.txt` / `WHATS-NEW-1.2.txt` | What 1.2 changes, written for players |
| `LICENZA.txt` / `LICENSE.txt` | GPL-3.0-or-later, this project's own tools |
| `Patch/` | Five xdelta patches towards this language's 1.2, plus `manifest.json` |
| `Cheats/` | The optional melonDS codes for 1.2, both formats, plus a note |
| `Manual/` | The original Sacred Gold / Storm Silver guides and the game guide |

The download carries **no game file**. A patch is the difference between a
recognized game and the 1.2 one; `Patch/manifest.json` names every accepted
starting version by whole-file SHA-256, and the install guide explains the
three programs that can apply it.

## Where the files come from

`contenuto.json` records the size and SHA-256 of every file in both folders.
`build_zip.py` refuses to pack anything that does not match it, and the public
check (`.github/check_public.py`) verifies the same record plus each patch
manifest on every run.

The folders themselves are written by the laboratory, from the reviewed 1.2
package and the verified deltas:

```sh
python3 -B local/publishing/build_zip_1_2.py --esporta release/1.2
```

Older downloads are not here: only 1.2. Previous versions keep their own
release pages.
