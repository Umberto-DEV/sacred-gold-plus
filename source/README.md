# Build and contribute

New contributors can start with the [contribution guide](../CONTRIBUTING.md)
and [repository map](docs/architecture/README.md),
[feature ownership index](features/README.md) and
[documentation index](docs/README.md) to find the relevant source and checks.

This tree contains the five-language **1.3.2** sources, native payloads,
build tools, tests and technical documentation. Published 1.3.1 identities remain
historical contracts; reproduce them from their published source revision.
Start with the [localization guide](docs/localization.md) and
[shared composition guide](sgp131/README.md). The `sgp12` commands below rebuild
the **1.2.5** predecessor from your own retail HeartGold.

The [1.3 builder guide](sgp13/README.md) describes the earlier feature line.
The 1.3.1 composer accepts only the two historical V1.3 V4 inputs. The current
`sgp13.build` uses the newer HF02 implementation. The
[authenticated V4 bootstrap](distribution/bootstrap_13.py) reconstructs the
required older HF01 inputs from 208 pinned sources in the already-published
ancestor, without changing current game code or Git refs. Fresh EN/IT builds
reproduce both exact V4 hashes. The 1.3.1 guide gives the complete commands;
HF01 is a build intermediate upgraded to HF02 before player use.

The [change register](docs/whats-new-1.3.1.md),
[bug list](../BUG-FIXES-1.3.1.md) and
[published validation report](docs/ui-1.3.1-validation.md) distinguish source
repairs, exact ROM identities, played scenarios and open coverage.
The [1.3.2 source correction](../BUG-FIXES-1.3.2.md) and its
[measured New Game regression](docs/validation/new-game-reset-1.3.2.md) retain the original diagnosis and probe identities. Current acceptance is in
[the five-language 1.3.2 report](docs/validation/localization-1.3.2.md).
The [base-stage evidence](docs/base-stage-validation.md),
[Android campaign of 29 October](docs/android-validation.md),
[earlier device campaign](docs/device-validation.md),
[systematic playtest](docs/gameplay-validation.md) and
[earlier UI campaign](docs/interface-validation.md) retain their original
candidate scope. Their results do not automatically accept the 1.3.1 successor.
The [stability investigation](docs/stability-investigation-1.3.1.md) and
[test-bench guide](docs/test-bench.md) document the older defects and runtime method.

This folder is for developers. To play, use the [download and install instructions](../README.md#download).

Game-dependent tools read **your own** game files. No game file is distributed, and none is needed to run the ROM-free tests in CI. Exact historical intermediate hashes and toolchains are required where the composition guide states them. How changes get in is at the end of this page.

## Five-language 1.3.2

The current localization layer adds FR/ES/DE to EN/IT using exact retail donors
and one guarded gameplay core. Per-language sources, the composition command,
native presentation ownership and input hashes are documented in
[localization.md](docs/localization.md). The [1.3.2 validation report](docs/validation/localization-1.3.2.md)
separates bounded game/save acceptance from ROM-free tests. The latest-target
package revision r2 uses [the schema-3 contract](distribution/release-1.3.2-r2.json):
five clean-ROM patches in the main download and all 150 historical-source routes
in a separate optional download. Localized installation/news PDFs accompany
seven shared English gameplay guides. The game targets are unchanged; see
[package validation](docs/validation/package-1.3.2-r2.md) and
[candidate-derived player PDFs](distribution/reference_docs.py). Follow
[the repeatable update procedure](docs/update-workflow.md) for future releases.

## What is here

| Folder | What it is |
| --- | --- |
| `sgp12/` | The library. One command builds 1.2.5 from an unmodified HeartGold ROM, one command checks the result. `base11.json` pins stage 0 (the public xdelta that turns that ROM into the 1.1 base) and `scarica_base.py` fetches it. `blocchi/` has one module per feature, each with an `applica()` and a read-back written independently of it. `build/` holds the validated payloads each block writes — code we compiled from the C sources in `native-*/` and `features/*/sorgenti*/`. |
| `sgp13/` | Earlier 1.3 feature builder from exact 1.2.5. Current HF02 sources are distinct from the historical HF01 V4 input required by 1.3.1. |
| `sgp131/` | Version-composition code, independent readbacks, owner activation, workbench and regressions, including the battle type-loop fix. Development sources now select V1.3.2 identity. See its [build guide](sgp131/README.md). |
| `features/<name>/` | One self-contained folder per feature: `sorgenti/` (our C), `tools/` (the applier, the read-back, the compiler, the mutants) and `test/`. The folders are deliberately self-contained, including their copy of the shared ARM9 helper: an applier and its read-back must not be able to share a wrong constant. |
| `verifiche/` | The ARM9 reserve checks T1–T5 and the automatic runtime gates (`rileva_crash.py`, `collauda_repellente.py`, `riserva_arm9.py`). |
| `native-guide/`, `native-eviv/` | The in-game EV/IV guide and reader, from 1.1. |
| `translation/`, `quality-audit/` | Message codec, release recipe loader, container helpers and pixel-width measurement against the game font. |
| `features/debug/` | Field instrumentation for the headless bench: a minimal GDB RSP client for the melonDS gdbstub, a scriptable warp that makes the game run its own map-change routine, the map and camera campaigns and their independent gate read-back. Development aids only: no block, no test, and they need a `hg_runtime-gdb` you build yourself. |
| `runtime/` | The headless melonDS harness used for runtime proofs: sources, the core patch script and build instructions. No binary; you build it. See [docs/test-bench.md](docs/test-bench.md). |
| `scripts/` | The 1.04 variant builders, kept for that older route, plus the ROM-free instruction probe the runtime build compiles. The 1.04 route itself does not run from this repository: `translation/build_release.py` needs release recipes, interface manifests and message banks that are not distributed. |
| `run_tests.py` | The Class A suites and separately reported Class B probes run by CI; game-dependent assertions need private inputs. |

## Prepare

The legacy 1.2.5 tools and general tests support Python 3.9 or newer. The
production 1.3.1 UI compiler additionally authenticates the exact Python
3.14.7 executable, libraries and Apple clang binary described in the
[1.3.1 guide](sgp131/README.md). A generic Python environment does not satisfy
those production pins. Install the dependencies into an isolated environment:

```sh
python3 -m venv .venv
.venv/bin/pip install -r source/requirements.txt
```

The compiled-code suites need an ARM946E-S-capable C compiler. The existing
1.2.4 payloads were built with **Apple clang 21.0.0
(`clang-2100.3.34.2`, Command Line Tools 27.0)**; each build manifest records
its compiler. Other Clang releases may produce different bytes or exceed a
payload's fixed space limit even when they support the ARM target. A usable
ARM target alone does not establish release reproducibility.

CI runs the ROM-free Class A suites on the official `xcode-27` macOS runner
with `/Library/Developer/CommandLineTools` explicitly selected. The observed
image includes CLT 27.0; its Xcode 27.2 alias instead names release candidate
27B48, not the frozen production CLT compiler. The workflow records the actual
CLT package, compiler version and SHA-256, checks host/ARM compilation and
retains every existing byte-for-byte and payload-size test. The complete job
has a bounded 60-minute budget.
A payload mismatch remains a failure; CI does not regenerate validated blobs.
UI and native compiler fixtures use explicit nonproduction host contract
seams, including protected compiler ownership/ACL checks. Production builders keep
their exact toolchain pins. Ten explicitly listed legacy suites also use the
existing protected host contract through the test runner, including isolated
version/hash rejection cases. No production command uses this injection.
Public-file checks remain on Ubuntu. Runner
software is documented by
[GitHub Actions](https://github.com/actions/runner-images/blob/main/images/macos/xcode-27-arm64-Readme.md).

Check that your compiler supports the target with:

```sh
clang --version
clang --target=armv5te-none-eabi -mcpu=arm946e-s -mthumb -ffreestanding -c -x c /dev/null -o /dev/null
```

Without a usable compiler the affected tests SKIP, with their count kept in the summary and the JSON — not a silent hole, but still a skip, so a first local run can print PASS with those tests unexercised. `SGP_CI=1` (what CI sets; `--richiedi-compilatore` does the same for `run_tests.py`) turns that skip into a failure instead, which is how you reproduce CI's severity locally. A compiler that is present but cannot build the shipped sources is never a skip, there or here: that is a defect and it fails on every machine.

Two inputs stay outside this repository.

**Your game file.** An **unmodified Pokémon HeartGold ROM**, US or Italian — the retail game you dumped from your own cartridge. That is the only game file the build needs; no intermediate ROM of ours is required, and none is distributed. The two the tools recognise are:

| Language | File as commonly named | SHA-256 |
| --- | --- | --- |
| EN | `Pokemon - HeartGold Version.nds` | `65f02a56…0105` |
| IT | `Pokemon - Versione Oro HeartGold.nds` | `013d04f5…0ce1` |

Keep it in a private folder and point `SGP_ROM_DIR` at that folder. Never copy a ROM, save, BIOS or dump into this checkout. The full pin — both SHA-256s, their sizes, and what each one must produce — is `sgp12/base11.json`.

**Stage 0 and `xdelta3`.** The blocks are applied to a 1.1 base, which the builder now derives from your ROM as its first step ("stage 0") instead of asking you for it. Stage 0 applies a public **xdelta patch**: a file of *differences* only, useless without the HeartGold it belongs to, and not a ROM. Install `xdelta3` (`brew install xdelta`, or `sudo apt install xdelta3`) and fetch the two patches once:

```sh
cd source && ../.venv/bin/python3 -m sgp12.scarica_base --destinazione "$SGP_ROM_DIR"
```

That command is the only place in this repository that opens a network connection, and nothing calls it for you. It requires the destination to belong to the current user and not be group/world-writable. It downloads the patches named in `sgp12/base11.json` from the `base-1.1` release, limits the checksum listing to 64 KiB and every patch to its pinned size, and gives the complete transfer a 30-minute deadline. It checks each patch against the pinned SHA-256 and atomically publishes only verified files without following output symlinks. Anything that does not match is deleted rather than left in the folder. You can equally download the two files by hand from the release page and drop them in `$SGP_ROM_DIR` under the same names, or pass one with `--delta`.

If you already have a 1.1 ROM, `--base` still takes it: stage 0 is skipped with a warning. Any other ROM is refused by SHA-256, with the accepted ones listed.

**The reference metadata.** `charmap.txt` and `tools/py_scripts/scrcmd.json` from the reference disassembly, at the pinned revision. Both files are included in its checkout:

```sh
git clone https://github.com/pret/pokeheartgold.git ../pokeheartgold
git -C ../pokeheartgold checkout --detach 0985e8718df4f25e64d6507d89c0c97c0d288981
export SGP_PRET_SOURCE=$PWD/../pokeheartgold
```

These files are not redistributed here: their licensing was not established to our satisfaction, so they remain external inputs. The character mapping encodes text; the command metadata lets the gift tools walk and verify scripts.

## Build and check the 1.2.5 predecessor

`sgp12` is a package inside `source/`, so every command below runs `python -m sgp12....`: it needs `source/` as the working directory, which is one level below where "Prepare" creates `.venv`. Every command in this README that touches `sgp12` is written the same way — `cd source &&`, then the venv interpreter as `../.venv/bin/python3` — so it can be copied and run from the repository root without a separate `cd` step to remember:

```sh
SGP_BUILD_OUT="$(mktemp -d "${TMPDIR:-/tmp}/sgp-build.XXXXXX")"
cd source && ../.venv/bin/python3 -m sgp12.costruisci \
        --base "$SGP_ROM_DIR/Pokemon - HeartGold Version.nds" \
        --uscita "$SGP_BUILD_OUT/sgp-1.2.5-EN.nds"
cd source && ../.venv/bin/python3 -m sgp12.verifica "$SGP_BUILD_OUT/sgp-1.2.5-EN.nds" \
        --base "$SGP_ROM_DIR/Pokemon - HeartGold Version.nds"
```

`--lingua` is no longer needed: the language comes from the ROM's SHA-256, and if you pass `--lingua` it has to agree. Use the Italian HeartGold for the Italian build.
The builder never replaces an existing ROM, report or intermediate log. It
publishes new files as private `0600` entries and requires `--log-dir`, when
used, to be a private `0700` directory.

The build is deterministic: the same ROM gives the same bytes. Stage 0 checks all three fingerprints — your ROM, the patch, and the 1.1 base that comes out of it — before a single block runs, and records them in the build's JSON report under `stadio0`. `verifica` repeats the whole thing, stage 0 included, compares the result with the ROM you give it (`costruzione_identica`), runs every block read-back and then T1–T5. Step-by-step instructions, including what to do when an applier refuses: [docs/base-stage-build.md](docs/base-stage-build.md).

After stage 0 the blocks are applied in this order: reserve, camera, Plus difficulty + save chunk, texts, NPC cap, battle animation, options page, Wi-Fi slot, title, credit, guide label, Rare Candy, capped gifts, continuous battle motion, battle item cache, battle party move cache, expanded Bag capacity, maintenance and the persistent version title — nineteen in all; see `source/sgp12/costruisci.py` or the numbered list in [docs/base-stage-build.md](docs/base-stage-build.md#the-block-order) for what each one does.

## Run the tests

The 1.3/1.3.1 native stages authenticate the actual Apple CLT compiler before
executing it, including version queries. The local pin is SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
Compiler and ancestors must be root-owned, not group/world writable and have
no extended ACL. Compiler children use a restricted environment. GitHub's
Class A job checks a separately observed host compiler; its UI/native compiler
contracts are explicitly nonproduction. The production identity guard remains enforced
before execution, and a host-suite PASS does not establish release-byte
reproduction or ROM acceptance.

Class A — no game file, the same set CI runs:

```sh
.venv/bin/python source/run_tests.py         # from the repository root
```

The runner also probes Class B, reporting missing private inputs as explicit
skips. Its historical `collected` number can include separate skipped subtests;
the new `executed_methods` count distinguishes methods that actually ran from
skip events. Compare suite results and their skip reasons across environments.
Each suite prints its elapsed time; `--json /path/to/private/report.json`
records `elapsed_seconds` per suite and separates Options payload compilation
time. Use those measurements before changing CI scheduling or reducing a test.
The runner explicitly registers ROM-free successor regressions and checks that
new `sgp131/test_*.py` modules are either registered or classified as local-only.
A local-only classification means CI has **not** executed those tests: they need
private inputs, the production compiler or another named prerequisite. Class A
fails if a registered suite collects nothing or skips every collected test.
All executed assertions must pass; a larger aggregate count does not establish
broader coverage. Historical validation totals retain their original scope.

The Route 43/44 repair's land/matrix codecs ship in `sgp131/map_resources.py`
with synthetic tests. Its optional visual regression uses the public read-only
`sgp131/tools/NativeModelReadback.java` bridge. Supply the exact Java and Nds4j
inputs pinned in `sgp131/test_invisible_grass_rom.py` with `SGP_HG_F09_JAVA`
and `SGP_HG_F09_JAR`; the two historical preimage ROMs can be supplied with
`SGP_HG_F09_ROM_EN` and `SGP_HG_F09_ROM_IT`. Those optional inputs are not
required to compose the repair or run the synthetic codec tests.

Class B — with your own game file (same venv-from-root convention as above: `cd source &&`, then `../.venv/bin/python3`).

What `$SGP_ROM_DIR` has to hold depends on which Class B suites you want:

| Suite | Wants |
| --- | --- |
| `sgp12.test_lib.TestCostruisciIdentico` (the criterion-4 test: the build is byte-identical to the shipped ROM) | your HeartGold, `base-1.1-{EN,IT}.xdelta` and a `SHA256SUMS` naming `sgp-1.2.5-{EN,IT}.nds` — it runs stage 0 itself. A `base-1.1-{EN,IT}.nds` is still accepted instead and skips stage 0. |
| the rare-candy, full-bag and bag-capacity suites | the built candidate; set `SGP_CAR_ROM_NOME=sgp-1.2.5-%s.nds`, `SGP_BORSA_ROM_NOME=sgp-1.2.5-%s.nds`, or the capacity suite’s explicit `SGP_CAPACITY_ROM` and `SGP_CAPACITY_BUILD` |
| the per-block suites (overlay in place, block mutants, text width, `TestBlocchiVFinale`) | `base-1.1-{EN,IT}.nds` |

The last row is the one exception to "the only input is your HeartGold": those suites open the 1.1 base directly, to compare a block against the stage that precedes it, and they have not been rewritten to derive it. They skip with an explicit reason when it is absent — a folder holding only the HeartGold and the patches runs everything else and skips those. Writing the base out once with the same patch is enough:

```sh
xdelta3 -d -D -R -s "$SGP_ROM_DIR/Pokemon - HeartGold Version.nds" \
        "$SGP_ROM_DIR/base-1.1-EN.xdelta" "$SGP_ROM_DIR/base-1.1-EN.nds"
```

```sh
cd source && SGP_ROM_DIR=/path/to/private/roms SGP_PRET_SOURCE=/path/to/pokeheartgold \
    ../.venv/bin/python3 -m unittest sgp12.test_lib -v
cd source && SGP_ROM_DIR=/path/to/private/roms ../.venv/bin/python3 -m unittest discover -s features/overlay/test -v
cd source && SGP_ROM_DIR=/path/to/private/roms ../.venv/bin/python3 -m unittest discover -s features/caramelle/test -v
cd source && SGP_RISERVA_ROM=/tmp/sgp-1.2.5-EN.nds SGP_RISERVA_COMPLETA=1 \
    ../.venv/bin/python3 -m unittest verifiche.test_riserva -v
```

`SGP_PRET_SOURCE` is a checkout of `pret/pokeheartgold` at commit
`0985e8718df4f25e64d6507d89c0c97c0d288981`: the text block reads `charmap.txt` from it, and
that file is not redistributed here. Without it the affected tests skip and say so.

`SGP_RISERVA_COMPLETA=1` turns "no ROM, so T2–T5 skipped" into a failure. Use it whenever you
mean to run the reserve register in full: eight skipped tests and eight passing tests print
almost the same summary. `sgp12/verifica.py` sets it for you. Even in full mode, T3's
`test_cheat_pubblici_spediti_cadono_in_un_blocco_pubblico` still skips on its own if `SGP_CHEATS`
(default `release/<version>/`, the cheat files a release ZIP is built from) is not a folder that
exists: a public checkout normally does not have one, since releases are built and packaged on
the maintainer's machine. That single skip is expected and does not need `SGP_CHEATS` set; see
`source/verifiche/test_riserva.py` for what it checks when the folder is there.

The rare-candy suite (`features/caramelle/test/`) runs the shipped ARM9 under Unicorn starting from the hook site itself, set `SGP_CAR_ROM_NOME=sgp-1.2.5-%s.nds` and point `SGP_ROM_DIR` at those private files (the historical default name is 1.2.2). Without them it skips with a reason. Its mutants (`features/caramelle/tools/mutanti.py`) build their own starting ROMs by undoing the block on a copy, so they need nothing else. Every mutant tool first runs the suite **unmutated**: a mutant only counts as killed if that baseline was green and the mutated run went red *having executed tests*. A red run with no test executed is a broken harness, not a gate that worked, and it is reported as NOT EVALUABLE.

The native-code suite recompiles the shipped C sources and compares them with the blobs that go into the ROM. Those bytes are only reproducible on the toolchain that produced them, which each `build/*/manifesto.json` names; on a different compiler (vendor or major version) the byte-for-byte tests **skip with the two identities printed**, and what stays is the claim that holds anywhere: the blob compiles, fits its compartment and has no external symbols. The expanded-Bag build suite always requires byte-identical code and symbols. The current macOS CI keeps those assertions and every fixed-space limit enabled. A compiler mismatch can therefore fail the full suite; it is not permission to replace the validated payloads.

The battle-animation suite (`features/anim/test/`) also needs the overlay modules extracted from your ROM; its tools do that, and the suite skips with an explicit reason without them. The runtime runs on the headless emulator are described in [docs/test-bench.md](docs/test-bench.md).

## Make a change

The 1.3.1 successor now pins Apple clang 21 `clang-2100.4.1.1` for its
newly compiled payloads. The legacy Guide still recompiles byte-identically;
current native/pixel and installer checks are recorded in the
[UI validation report](docs/ui-1.3.1-validation.md). This does not replace the
historical 1.2.5 payloads or their reproducibility checks.

The 1.3.1 compiler tests have separate assurance levels. The ROM-free
`sgp131.test_ui` seam authenticates the observed protected host toolchain for UI
and selected native test fixtures. Source/library, golden payload, size, symbol
and Unicorn assertions remain enabled. UI test receipts are labelled
nonproduction; native fixture measurements are supporting host contracts.
Production `sgp131.ui` and `ui_verify`
retain exact interpreter/compiler and source pins; `sgp131.test_ui_rom` verifies
the canonical private inputs under those pins. Passing the host contract suite
does not certify a production ROM or a different toolchain. Current results and
remaining runtime gates are in [UI validation](docs/ui-1.3.1-validation.md).

The `sgp131.workbench` UI stage requires explicit `--ui-config` and `--charmap`
inputs. It retains one pending candidate alongside the verified candidate and
fallback, checks provenance before use, and requires runtime evidence for
promotion. A successful build is not runtime acceptance. Its first Italian
pending candidate and focused transaction tests are recorded in that report.

Change one issue at a time. Preserve message controls, argument counts and expected input data. **A preimage mismatch is a reason to stop and investigate, not to remove the check.** For a new translation, start with a small agreed set of screens and test it in context.

If the change needs space in the ARM9 reserve, claim it in [docs/arm9-reserve-reservations.md](docs/arm9-reserve-reservations.md) and add its entry to `source/docs/arm9-reserve-map.json` in the same change; [docs/arm9-reserve-map.md](docs/arm9-reserve-map.md) explains the rules, in particular that anything with a public address anchors to the high end of the reserve. The interfaces between features — the save chunk, patching an overlay in place, the Wi-Fi slot fallback, the guide — are in [docs/contracts.md](docs/contracts.md).

## What must never be committed

Game files, saves, save states, BIOS, firmware and memory dumps. Game text, game code, extracted tables, archives and graphics. Anything with a personal path or name in it. `.github/check_public.py` refuses a tracked `.nds`, `.sav`, `.bin` dump or `.dump` — the extension anywhere in the name, not only at the end — any tracked file over 2 MB that is not declared, any binary outside the screenshot gallery and our own small compiled blobs, any undeclared hidden folder, a blob that starts with a cartridge or game-container header, a personal path inside a binary, and a long unbroken base64 run inside a text file.

The stage-0 patches are not tracked either: `.xdelta` is forbidden in the
public source tree because a format header cannot prove that a delta contains
no private game bytes. Patches are release assets, downloaded on demand into
your private folder. What lives in the tree is `sgp12/base11.json`, which is a
few hundred bytes of fingerprints and URLs.

Where a tool needs game data, it reads it from your file at build time. The text corrections are the clearest case: `sgp12/build/testi/REGOLE.json` records, for each correction, the message it belongs to, the SHA-256 the current text must have and the minimal edits — no sentence of the game. `features/texts/genera_correzioni.py` rebuilds the table the applier consumes from your own ROM, and the builder does it automatically when the table is absent.

## How changes get in

`main` is the only working branch for the maintainer and their coding assistants. Make and validate changes directly on `main`; do not create a development branch or pull request for this workflow. Keep history linear and publish only reviewed changes with passing checks. Do not change repository protections without explicit maintainer authorization. Community contributions from other accounts may still use pull requests and follow the existing review requirements.

The workflow is configured for pushes to branches where Actions is enabled and pull requests to `main`, including direct maintainer updates. A contributor must enable Actions in a new fork before its own push checks run; a fork pull request may await maintainer approval under the repository's GitHub settings. On GitHub the runner probes Class B suites, but their game-dependent assertions skip without private inputs; a few synthetic assertions may still execute. Run the applicable Class B checks locally with your own game file and record the exact result in the release validation document or pull request. "Not run" is acceptable when explained; a claim that was not checked is not. Follow the [contribution guide](../CONTRIBUTING.md) for the exact fork, private-candidate and evidence steps.

Finished versions are tags `vX.Y` with a GitHub release carrying the player ZIPs, built on the maintainer's machine from the verified ROM. Previews are tagged `vX.Y-rcN` and marked pre-release. Released bytes are never overwritten: a correction is a new release. There is no nightly build, because building the game needs a game file.

## Final stages (1.2.4 maintenance and 1.2.5 title)

After the existing stages, `sgp12.manutenzione` requires the exact published
1.2.3 intermediate hash. It installs the copy-ownership barrier and Waterfall
search guard, then updates the initial prompt title to 1.2.4. The options source and
blobs retain the intermediate 1.2.3 title deliberately; the final title is
specified in `sgp12/build/manutenzione/versione.json`. The following `sgp12.versione` stage updates the menu title and the upper title-screen version label, including the corrected credit. No intermediate ROM
needs to be kept on disk. Both the builder and verifier include this stage.

The release-specific file checks, supported inputs and reproducible player
ZIP tooling are documented in [distribution/README.md](distribution/README.md)
(relative to this document's directory, use `source/distribution/README.md`
from the repository root). The published 1.2.4 release was validated incrementally against
the 1.2.3 files. The 1.2.5 release has separate [build and runtime validation](docs/base-stage-validation.md); its historical packaging contract described 21 input routes.

For 1.3.1 use the explicit [versioned contract](distribution/release-1.3.1.json)
and [distribution instructions](distribution/README.md), with 25 direct input
routes per language. The default distribution contract is `release-1.3.1.json`. Package reconstruction and game/save acceptance are separate;
[package validation](docs/package-1.3.1-validation.md) retains exact receipts
and the limitations of each checkpoint. The current ROM fingerprints and
battle-loop regression are in the [1.3.1 composition guide](sgp131/README.md).
