# Rebuilding Sacred Gold Plus 1.2.1

Two commands build a 1.2.1 ROM from your own 1.1 ROM and verify the result.

(The file keeps its `rebuilding-1.2.md` name: three other pages link to it, and the
procedure is the same one, extended by one block.) This page is the
step-by-step version: what you need, in what order, and what to do when a step refuses.

No ROM is distributed here. You supply the base.

---

## 1. Start from your own 1.1 ROM

You need a Sacred Gold Plus **1.1** ROM, English or Italian. That file is your base; 1.2.1 is
built by patching it.

Put it in a private folder **outside this repository** and pass its path with `--base`. Nothing
in the build writes to the base, but keeping game files out of the working tree is a rule here,
not a preference: ROMs, saves, BIOS images and dumps never enter this repository and are never
opened as text.

The appliers verify the base by content at every step, so an unexpected or already-patched base
is refused rather than silently mangled.

## 2. Install the Python dependencies

```sh
python3 -m venv .venv
.venv/bin/pip install -r source/requirements.txt
```

Four pinned packages: `ndspy` (ROM and NARC containers, used by several appliers), `unicorn`
(ARM946E-S emulation, used by the blob tests), `capstone` (disassembly in the readers and the
blob tests) and `Pillow` (frame comparison in the image checks).

## 3. Obtain `charmap.txt`

The text block encodes its corrections with the game's character map, which comes from the
`pret/pokeheartgold` decompilation at commit
`0985e8718df4f25e64d6507d89c0c97c0d288981`. That file is not redistributed here.

Check out that commit somewhere outside this repository and point the builder at it:

```sh
export SGP_PRET_SOURCE=/path/to/pokeheartgold
```

Alternatively, place the checkout (or just its `charmap.txt`) at
`source/sgp12/build/testi/pret-source/`, which is where the builder looks when the environment
variable is not set.

## 4. Build

`sgp12` is a package inside `source/`, so `python -m sgp12...` needs `source/` as the working
directory — one level below where step 2 creates `.venv`. Every command below is written
`cd source &&`, then the venv interpreter as `../.venv/bin/python3`, the same convention
`source/README.md` uses, so each line can be copied and run from the repository root on its own:

```sh
cd source && ../.venv/bin/python3 -m sgp12.costruisci --base <base-1.1-EN.nds> --uscita <out/sgp-1.2.1-EN.nds> --lingua EN
cd source && ../.venv/bin/python3 -m sgp12.costruisci --base <base-1.1-IT.nds> --uscita <out/sgp-1.2.1-IT.nds> --lingua IT
```

`--build` selects the folder holding the validated per-block blobs and the ARM9 reserve manifest
(default `sgp12/build/`). `--log-dir` additionally writes a JSON record and an intermediate ROM
after each block, which is what the step-by-step readers consume.

### The block order

The builder applies fourteen blocks, always in this order:

1. **reserve** — carves and records the ARM9 reserve the native blocks allocate from
2. **camera** — the camera behaviour change
3. **Plus + chunk** — the Plus difficulty blob and the save-chunk load/save path
4. **texts** — the text corrections inside the message archive
5. **NPC** — NPC movement smoothing
6. **animation** — the procedural idle animation, hooked in the battle overlay
7. **options** — the in-game options page
8. **Wi-Fi** — the connection-slot logic
9. **title** — the title screen tilemap
10. **credit** — the credit tiles in the same archive
11. **guide** — turns the automatic EV/IV guide label off
12. **rare candy** — the Rare Candy stays in the party menu after use
13. **capped gifts** — restores the old reward paths, adds the named-item warning and its script calls, then builds the permissive site table and installs the ARM9 hooks
14. **continuous battle motion** — updates the battle hooks for both sides and pauses motion during moves

The order matters: later blocks read the reserve map the first block wrote, and blocks that
patch the same overlay run in a declared sequence, the second applier working on the ROM the
first one produced. The gift block computes site keys after the script changes. The final
motion block updates the original animation hooks; its reserved bytes must still be zero.

### The build is deterministic

The same base, the same block folder and the same language produce a **byte-identical** ROM.
There is no timestamp, no build id and no randomness in the output. Determinism is not a nicety
here: it is what makes the verification below meaningful.

## 5. Verify

```sh
cd source && ../.venv/bin/python3 -m sgp12.verifica <out/sgp-1.2.1-EN.nds> --base <base-1.1-EN.nds> --lingua EN
```

`verifica` does three things:

- **`costruzione_identica`** — it rebuilds the ROM internally from `--base`, with the same
  library the builder uses, and compares the result with the file you passed. This is the check
  that matters: it says the ROM you have is exactly the one this toolchain produces. Without
  `--base` and `--lingua` the rebuild is skipped, with an explicit reason.
- **every block reader** — each block has a reader that re-derives what the block wrote, from
  scratch, instead of trusting anything the applier produced. Several of them deliberately use a
  separate family of decoders from the applier, so a shared wrong constant cannot make both
  agree. The readers are written to compare a ROM against the stage **immediately before** their
  block, not against the finished ROM, so `verifica` reconstructs the intermediate stages and
  feeds each reader the right pair.
- **T1–T5** — the independent ARM9 reserve checks in `source/verifiche/test_riserva.py`, run on
  the ROM you passed. T1 needs no ROM and always runs. One of T3's own checks skips on its own,
  even here, if `SGP_CHEATS` (default `release/<version>/`) is not a folder that exists: it reads
  the cheat files a release ZIP ships, which are not part of a plain checkout.

## 6. Regenerating the canonical build blobs

The per-block blobs under `source/sgp12/build/` are extracted from a finished 1.2.1 ROM, not
recompiled:

```sh
cd source && ../.venv/bin/python3 -m sgp12.estrai_build --rom <sgp-1.2.1-EN.nds> --lingua EN
cd source && ../.venv/bin/python3 -m sgp12.estrai_build --rom <sgp-1.2.1-IT.nds> --lingua IT
```

For every block that writes a blob at a fixed address, this reads the exact bytes out of the ROM
and — where a call target can be decoded unambiguously — the patch targets too, then writes them
into `source/sgp12/build/<block>/` with a provenance record and a checksum file. An existing
manifest in that folder is merged, not replaced.

It works this way because compiled candidates kept in a development folder are not necessarily
the same bytes that ended up in the shipped ROM: one blob differed by 152 bytes from the real
one, having been compiled with slightly different options. Extracting from the ROM is correct by
construction, and stays correct when the ROM changes — you just extract again.

Blocks with no external blob (reserve, camera, title, credit, guide) are
deterministic and need no extraction. The two options text blobs
(`build/opzioni/testi-{EN,IT}.bin` and `voci-{EN,IT}.bin`) are the one exception in the other
direction: since 1.2.1 they are **built**, not extracted, by
`features/options/tools/costruisci_testi.py` from `features/options/testi/testi.json` and the
pret charmap, then zero-padded to the size of their compartment. The unpadded form sits in
`features/options/prove/testi/`, byte for byte the same. That is how the version string shown
on Continue is changed: edit `testi.json`, re-measure with `tools/misura_v2.py` against a real
ROM font, rebuild the blobs, then rebuild the ROM. The text block is a transformation of a correction table rather than a blob at a
fixed address, and is not extractable in the same way.

## 7. If a step refuses

An applier that rejects because **the preimage does not match** is telling you that the bytes it
expected to find are not there. That almost always means the base is not the one this step was
written for: a different 1.1 build, a ROM that has already been through another tool, or a step
run twice.

**Investigate; do not remove the check.** Every patch in this project is idempotent by design —
reapplying one is a rejection, because the preimage is gone — and every patch carries content
guards precisely so that a drifting base announces itself with a refusal instead of a silence.
A guard that fires is the mechanism working. The right moves are: confirm the base's SHA-256,
confirm which steps have already run against it, and re-derive the preimage on the ROM you
actually have rather than copying it from a document. Preimages are always re-derived on the
current working ROM; a preimage copied out of an older note is how a postimage once got mistaken
for a preimage.

Two related failure modes worth naming:

- **A block refuses because a recompressed overlay stream no longer fits its slot.** Do not
  relocate the overlay to get around it — see `docs/contracts.md` for why relocation is refused
  and what to try instead.
- **A size gate fires.** Every block asserts that the ROM it produces is exactly as long as the
  one it received. If that gate fails, something moved a file; stop and find out what.

---

## See also

- `docs/contracts.md` — the save chunk, in-place overlay patching, the Wi-Fi slot rule and the
  EV/IV guide.
- `docs/arm9-reserve-map.md` — the ARM9 reserve layout the native blocks allocate from.
- `source/README.md` — repository layout, tests and how to work on the sources.
- `source/sgp12/README.md` — the library itself, block by block.
