# Build and contribute

This folder is for developers. To play, use the [download and install instructions](../README.md#download).

Everything here rebuilds and checks the game from **your own** game file. No game file is distributed, and none is needed to run the tests that CI runs. How changes get in is at the end of this page.

## What is here

| Folder | What it is |
| --- | --- |
| `sgp12/` | The library. One command builds 1.2 from a 1.1 base, one command checks the result. `blocchi/` has one module per feature, each with an `applica()` and a read-back written independently of it. `build/` holds the validated payloads each block writes — code we compiled from the C sources in `native-*/` and `features/*/sorgenti*/`. |
| `features/<name>/` | One self-contained folder per feature: `sorgenti/` (our C), `tools/` (the applier, the read-back, the compiler, the mutants) and `test/`. The folders are deliberately self-contained, including their copy of the shared ARM9 helper: an applier and its read-back must not be able to share a wrong constant. |
| `verifiche/` | The ARM9 reserve checks T1–T5 and the automatic runtime gates (`rileva_crash.py`, `collauda_repellente.py`, `riserva_arm9.py`). |
| `native-guide/`, `native-eviv/` | The in-game EV/IV guide and reader, from 1.1. |
| `translation/`, `quality-audit/` | Message codec, release recipe loader, container helpers and pixel-width measurement against the game font. |
| `features/debug/` | Field instrumentation for the headless bench: a minimal GDB RSP client for the melonDS gdbstub, a scriptable warp that makes the game run its own map-change routine, the map and camera campaigns and their independent gate read-back. Development aids only: no block, no test, and they need a `hg_runtime-gdb` you build yourself. |
| `runtime/` | The headless melonDS harness used for runtime proofs: sources, the core patch script and build instructions. No binary; you build it. See [docs/test-bench.md](docs/test-bench.md). |
| `scripts/` | The 1.04 variant builders, kept for that older route, plus the ROM-free instruction probe the runtime build compiles. The 1.04 route itself does not run from this repository: `translation/build_release.py` needs release recipes, interface manifests and message banks that are not distributed. |
| `run_tests.py` | The Class A suites — exactly what CI runs. |

## Prepare

Python 3.9 or newer. Install the pinned dependencies into an isolated environment:

```sh
python3 -m venv .venv
.venv/bin/pip install -r source/requirements.txt
```

Two inputs stay outside this repository.

**Your game file.** A Sacred Gold Plus 1.1 ROM, English or Italian, in a private folder. Point `SGP_ROM_DIR` at that folder; the tools expect `base-1.1-EN.nds` and `base-1.1-IT.nds` there. Never copy a ROM, save, BIOS or dump into this checkout.

**The character mapping.** `charmap.txt` from the reference disassembly, at the pinned revision:

```sh
git clone https://github.com/pret/pokeheartgold.git ../pokeheartgold
git -C ../pokeheartgold checkout --detach 0985e8718df4f25e64d6507d89c0c97c0d288981
export SGP_PRET_SOURCE=$PWD/../pokeheartgold
```

It is not redistributed here: its licensing was not established to our satisfaction, so it is an external input like the game file.

## Build and check the game

From this folder:

```sh
python3 -m sgp12.costruisci --base "$SGP_ROM_DIR/base-1.1-EN.nds" \
        --uscita /tmp/sgp-1.2-EN.nds --lingua EN
python3 -m sgp12.verifica /tmp/sgp-1.2-EN.nds \
        --base "$SGP_ROM_DIR/base-1.1-EN.nds" --lingua EN
```

The build is deterministic: the same base gives the same bytes. `verifica` rebuilds the ROM internally from the same base, compares it with the one you give it (`costruzione_identica`), runs every block read-back and then T1–T5. Use `IT` and the Italian base for the other language. Step-by-step instructions, including what to do when an applier refuses: [docs/rebuilding-1.2.md](docs/rebuilding-1.2.md).

The blocks are applied in this order: reserve, camera, Plus difficulty + save chunk, texts, NPC cap, battle animation, options page, Wi-Fi slot, title, credit, guide label.

## Run the tests

Class A — no game file, the same set CI runs:

```sh
.venv/bin/python source/run_tests.py         # from the repository root
```

Class B — with your own game file:

```sh
cd source
SGP_ROM_DIR=/path/to/private/roms python3 -m unittest sgp12.test_lib -v
SGP_ROM_DIR=/path/to/private/roms python3 -m unittest discover -s features/overlay/test -v
SGP_RISERVA_ROM=/tmp/sgp-1.2-EN.nds python3 -m unittest verifiche.test_riserva -v
```

The battle-animation suite (`features/anim/test/`) also needs the overlay modules extracted from your ROM; its tools do that, and the suite skips without them. The runtime runs on the headless emulator are described in [docs/test-bench.md](docs/test-bench.md).

## Make a change

Change one issue at a time. Preserve message controls, argument counts and expected input data. **A preimage mismatch is a reason to stop and investigate, not to remove the check.** For a new translation, start with a small agreed set of screens and test it in context.

If the change needs space in the ARM9 reserve, claim it in [docs/arm9-reserve-reservations.md](docs/arm9-reserve-reservations.md) and add its entry to `source/docs/arm9-reserve-map.json` in the same change; [docs/arm9-reserve-map.md](docs/arm9-reserve-map.md) explains the rules, in particular that anything with a public address anchors to the high end of the reserve. The interfaces between features — the save chunk, patching an overlay in place, the Wi-Fi slot fallback, the guide — are in [docs/contracts.md](docs/contracts.md).

## What must never be committed

Game files, saves, save states, BIOS, firmware and memory dumps. Game text, game code, extracted tables, archives and graphics. Anything with a personal path or name in it. `.github/check_public.py` refuses a tracked `.nds`, `.sav`, `.bin` dump or `.dump`, any tracked file over 2 MB that is not declared, and any binary outside the screenshot gallery and our own small compiled blobs.

Where a tool needs game data, it reads it from your file at build time. The text corrections are the clearest case: `sgp12/build/testi/REGOLE.json` records, for each correction, the message it belongs to, the SHA-256 the current text must have and the minimal edits — no sentence of the game. `features/texts/genera_correzioni.py` rebuilds the table the applier consumes from your own ROM, and the builder does it automatically when the table is absent.

## How changes get in

`main` is the development trunk and stays green. Work on a `feature/…` or `fix/…` branch (from a fork or from this repository) and open a pull request against `main`; it needs the CI run to pass and a review, and the history stays linear.

CI runs the Class A tests above on every push to any branch and on every pull request, so your branch gets the same checks as `main`. A first run from a fork waits for the maintainer's approval. Class B needs your own game file and never runs on GitHub: run it locally and write what you ran, and what it said, on the pull request's "Class B tests run locally" line. "Not run" is acceptable; a claim that was not checked is not.

Finished versions are tags `vX.Y` with a GitHub release carrying the player ZIPs, built on the maintainer's machine from the verified ROM. Previews are tagged `vX.Y-rcN` and marked pre-release. Released bytes are never overwritten: a correction is a new release. There is no nightly build, because building the game needs a game file.
