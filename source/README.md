# Build and contribute

New contributors can start with the [contribution guide](../CONTRIBUTING.md)
and [repository map](docs/architecture/README.md),
[feature ownership index](features/README.md) and
[documentation index](docs/README.md) to find the relevant source and checks.

This tree contains the five-language **1.3.3 targets**, native
payloads, build tools, tests and technical documentation. Published 1.3.2 and
1.3.1 identities remain historical contracts; reproduce those releases from their
published source revisions.
Start with the [localization guide](docs/localization.md) and
[shared composition guide](sgp131/README.md). The `sgp12` commands below rebuild
the **1.2.5** predecessor from your own retail HeartGold.

**What is rebuilt:** the Plus build produces a complete ROM file by compiling
project-owned additions and composing them with authenticated retail and
inherited stages. It does not compile every original HGSS function from C.

| Task | Entry point and evidence |
| --- | --- |
| Build the complete Plus file from owned retail inputs | [Current composition recipe](sgp131/README.md) and [stage map](docs/test-bench.md#from-the-source-tree-to-the-complete-rom) |
| Connect a particular source function to installed bytes and execution | [Attribution method](docs/test-bench.md#linking-source-to-an-exact-rom) and [case catalog](docs/validation/README.md); coverage is per component |
| Rebuild the original retail game from PRET sources | [PRET scope and requirements](docs/test-bench.md#using-newer-pret-references); the inspected upstream targets are USA, and this project has not demonstrated a fresh whole-ROM PRET rebuild |

Localized Plus IT shares the USA internal core while retaining Italian
presentation. An exact Italian retail rebuild is a separate regional target.
An executable-component inventory is not a map of every function or a measure
of decompilation completeness.

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
The [1.3.3 corrections](docs/validation/fixes-1.3.3.md) have bounded source,
counterfactual and exact-target readback evidence. The report separates the
historical seven-cycle onboarding checks from subsequent DE/FR Training menu
and raw-save/cold checks. Natural battle/pivot and physical-device validation
remain pending. The [1.3.3 distribution contract](distribution/release-1.3.3.json)
selects five targets, 40 recognized sources and 200 direct updater routes,
with 18 player PDFs and the four unchanged historical builder inputs.
The [1.3.2 source correction](../BUG-FIXES-1.3.2.md) and its
[measured New Game regression](docs/validation/new-game-reset-1.3.2.md) retain
the original diagnosis and probe identities. The published 1.3.2 baseline identities and
bounded acceptance are in the [game contract](distribution/game-1.3.2-r4.json)
and [Guide correction report](docs/validation/guide-opening-1.3.2.md); the
[original five-language report](docs/validation/localization-1.3.2.md) retains
its predecessor scope.
The [base-stage evidence](docs/base-stage-validation.md),
[Android campaign of 29 October](docs/android-validation.md),
[earlier device campaign](docs/device-validation.md),
[systematic playtest](docs/gameplay-validation.md) and
[earlier UI campaign](docs/interface-validation.md) retain their original
candidate scope. Their results do not automatically accept the 1.3.1 successor.
The [stability investigation](docs/stability-investigation-1.3.1.md) and
[test-bench guide](docs/test-bench.md) document the older defects and runtime method.

The [source-to-ROM attribution method](docs/test-bench.md#linking-source-to-an-exact-rom)
explains how to connect source, compilation, installed bytes and execution using
locally supplied ROMs.
Its [complete-ROM stage map](docs/test-bench.md#from-the-source-tree-to-the-complete-rom) connects retail/bootstrap, component compilation, owner composition, localization and exact output/readback receipts.
The [newer PRET reference method](docs/test-bench.md#using-newer-pret-references)
shows how to recover source knowledge and compare command metadata with a
ROM-free JSON tool while preserving the qualified production inputs.
The [continuous native ExecuteSync example](docs/validation/native-fs-exec-sync-native-callees-source-rom-1.3.2.md)
shows how to join qualified caller/callee checks without importing their future
RAM states, while retaining an explicit remaining model and counterexamples.
The [complete native Send case](docs/validation/native-fs-send-native-callees-source-rom-1.3.2.md)
adds actual caller preparation and the original return POP, preserving captured
predecessor guard bytes and separating source consistency from exact-input identity.
The [native Translate case](docs/validation/native-fs-translate-source-rom-1.3.2.md)
adds code/data separation, a concrete Italian retail literal relocation and a
writer control whose final CPU and entire RAM are unchanged.
The [combined native Send/Translate case](docs/validation/native-fs-send-translate-native-source-rom-1.3.2.md)
joins those checks with complete frozen fields and actual whole-RAM boundary
agreement, leaving only the default handler explicitly modeled.
The [default FindPath prefix](docs/validation/native-fs-default-findpath-source-rom-1.3.2.md)
shows a zero-model native prefix with explicit deeper-stack provenance and
controls that distinguish identical final bytes from their writer.
The [nested SEEKDIR dispatch](docs/validation/native-fs-nested-seekdir-source-rom-1.3.2.md)
separates actual parent input from a declared flag projection with identical
final CPU/RAM, while checking the new table target and deeper stack provenance.
The [complete cached SeekDir case](docs/validation/native-fs-cached-seekdir-source-rom-1.3.2.md) runs the full native
callee with authenticated filesystem resources, bounded overlap checks and a
ROM-derived input mode reproducible without private captures. Its independent
PRET metadata check recovers the root-directory layout; full caller activation
and original C rebuilding remain separate.
The [complete cached pathname lookup](docs/validation/native-fs-cached-findpath-source-rom-1.3.2.md)
continues through eight native functions to a real FNT file ID. It adds a finite
independent ARM arithmetic oracle, byte/halfword neighbor checks and standard
Python verification of saved evidence without starting the CPU or compiler.
The [public report catalog](attribution_cases.py) provides standard-library-only
`list`, `show` and `check` JSON for developers and automation. Start with
`python3 -I -S -B source/attribution_cases.py show native-fs-release --json`;
its command descriptions and navigation checks are separate from game validation.
The [complete Read/Wait caller](docs/validation/native-fs-read-caller-source-rom-1.3.2.md)
and [relative Find wrapper](docs/validation/native-fs-find-source-rom-1.3.2.md)
show how full caller and isolated copied-context evidence retain different limits.
The [complete native Find caller](docs/validation/native-fs-find-caller-source-rom-1.3.2.md)
adds one-time BSS input, typed replay and matched final RAM verification.

The [complete cached Convert API](docs/validation/native-fs-cached-convert-source-rom-1.3.2.md)
connects18 native components to the real move-archive path and fileID140, with
owned-ROM reproduction, BSS provenance and finite IRQ checks. The input's archive
procedure projection and missing natural card protocol remain explicit.

The [complete cached Open API](docs/validation/native-fs-cached-open-source-rom-1.3.2.md)
continues to the real FAT140 record and live file handle, including a finite
bounds failure and temporary-stack lifetime checks. Payload I/O and natural
card protocol retain their separate limits.

The [memory-archive Read chain](docs/validation/native-fs-memory-read-source-rom-1.3.2.md)
follows Open/Read/Seek/Read/Close to exact owned NARC bytes. Original SDK code,
a compiled test caller and explicit memory-archive input projections retain
separate provenance; natural CARD protocol remains unqualified.

The [original NARC caller](docs/validation/native-fs-memory-narc-source-rom-1.3.2.md)
now traverses its own Thumb parser and all native SDK bodies without a test
caller or service models. Source/byte identity, mixed ISA, stack ownership and
the exact selected member are checked; natural CARD delivery remains open.

The [complete PP getter](docs/validation/native-pp-memory-getter-source-rom-1.3.2.md)
then reads its native stack buffer and returns the PP scalar. A separately
declared source-memory counterfactual changes the actual returned value,
checking the causal data link through the full chain without register shadows.

The [complete native MaxPP path](docs/validation/native-maxpp-memory-source-rom-1.3.2.md) now joins the PP getter to its
actual clamp, multiplication, signed division and u8 return. A recovered MSL
assembly recipe compiles to the exact 524 installed division bytes. Declared
PP-Up and source-PP inputs exercise causal native results, with source-bound
raw verification; original Thumb compilation and natural CARD remain open.

The [native Mon segment cipher](docs/validation/native-mon-cipher-source-rom-1.3.2.md) follows the original wrapper,
core and private LCG on 128 synthetic bytes. Two API seeds and neutral observer
OFF qualify native data/seed writes, stack lifetime and full ABI without player
records or global RNG access. The reusable fixture, frontend and verifier keep
C provenance, installed byte identity and finite semantics distinct from the
missing original C compiler.

The [native Mon checksum](docs/validation/native-mon-checksum-source-rom-1.3.2.md) checks the next prerequisite on owned
storage: normal/odd sizes, 16-bit overflow and zero. Exact halfword access,
per-step truncation, final flags and full ABI are verified with the existing
frontend, without new ISA kernels or an original-compiler claim.

The [native Mon substructure selector](docs/validation/native-mon-substructure-source-rom-1.3.2.md) covers all32PID rows and
four logical blocks, with exact table-byte reads, full ABI and an ignored-PID
counterfactual. Its eight-image reader finds the retail Italian table-pointer
difference. A source-only PRET adapter reuses four unchanged HGSS functions and
compares Platinum's mapping while recording its declared type differences.

The [complete encrypted Box PP-Up getter](docs/validation/native-box-ppup-source-rom-1.3.2.md) now composes decrypt,
checksum, four header-PID selectors and re-encryption on owned synthetic
records. A checksum-preserving field counterfactual changes the actual native
return while each record is restored exactly. Full transient access/stack
proofs and CPU-free raw verification keep this isolated API coverage separate
from original C compilation, natural callers and save validation.

The [complete encrypted Box PP setter](docs/validation/native-box-pp-setter-source-rom-1.3.2.md) follows the write lifecycle:
old-key decrypt, native field store, second checksum, header update and new-key
encryption. A separate Value-byte counterfactual and full transient replay
verify the field's effect. Static MaxPP/caller attribution remains distinct
from executing that caller or rebuilding the original C binary.

The [complete encrypted Box move setter](docs/validation/native-box-move-setter-source-rom-1.3.2.md) verifies halfword load/store,
post-ADDSP lifetime and both idempotent field/header writes. A move310→311
counter keeps the high byte unchanged, so the proof requires exact width2
transcripts and independent instruction kernels, alongside full state/replay.
The complete higher move caller remains a separate bounded context.

This folder is for developers. To play, use the [download and install instructions](../README.md#download).

Game-dependent tools read **your own** game files. No game file is distributed, and none is needed to run the ROM-free tests in CI. Exact historical intermediate hashes and toolchains are required where the composition guide states them. How changes get in is at the end of this page.

## Five-language 1.3.2

For current illustrated player documents, start in [`guides/`](../guides/README.md).
The [file index](../REPOSITORY.md) separates guide sources, release-page assets,
game code and the [complete editable package tree](../package/README.md).
This documentation refresh reuses the exact accepted game patches. Frozen
schema-3 contracts below retain their original document hashes; document-only
recomposition uses `distribution/package_workspace.py` and records a separate
current package identity.

The current localization layer adds FR/ES/DE to EN/IT using exact retail donors
and one guarded gameplay core. Per-language sources, the composition command,
native presentation ownership and input hashes are documented in
[localization.md](docs/localization.md). The [1.3.2 validation report](docs/validation/localization-1.3.2.md)
retains its original bounded game/save scope. The
[explicit schema-3 contract](distribution/release-1.3.2-r4.json) freezes the
corrected package baseline. One `Sacred-Gold-Plus-1.3.2.zip` contains five
clean-ROM patches, all 175 optional
updaters from 35 recognized sources, ten localized installation/news PDFs,
seven shared English gameplay guides and the four authenticated developer inputs
in that frozen baseline. The current illustrated documentation refresh adds the
eighth, complete Move Changes guide through the package workspace; its
[documentation contract](distribution/documentation-1.3.2.json) identifies the
current archive separately from that frozen baseline.
The [Guide correction report](docs/validation/guide-opening-1.3.2.md) records all
five successor identities and their separate tests. See [package validation](docs/validation/package-1.3.2-corrected.md),
[candidate-derived PDFs](distribution/reference_docs.py) and the
[repeatable update procedure](docs/update-workflow.md).

## What is here

| Folder | What it is |
| --- | --- |
| `sgp12/` | The library. One command builds 1.2.5 from an unmodified HeartGold ROM, one command checks the result. `base11.json` pins stage 0 (the public xdelta that turns that ROM into the 1.1 base) and `scarica_base.py` fetches it. `blocchi/` has one module per feature, each with an `applica()` and a read-back written independently of it. `build/` holds the validated payloads each block writes — code we compiled from the C sources in `native-*/` and `features/*/sorgenti*/`. |
| `sgp13/` | Earlier 1.3 feature builder from exact 1.2.5. Current HF02 sources are distinct from the historical HF01 V4 input required by 1.3.1. |
| `sgp131/` | Version-composition code, independent readbacks, owner activation, workbench and regressions, including the battle type-loop fix. Development sources now select V1.3.3 candidate identity. See its [build guide](sgp131/README.md). |
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

This is an explicit download step; the build does not invoke it automatically.
The current command obtains the single player ZIP identified by
[`distribution/build-input-delivery.json`](distribution/build-input-delivery.json),
authenticates the complete archive and extracts only the requested stage-zero
patches. Their hashes and sizes must also match `sgp12/base11.json`; the historical
patch bytes are unchanged. Reuse an existing exact ZIP with `--container /path/to/archive.zip`
to avoid another download. The destination must belong to the current user and
not be group/world-writable. Transfers are bounded by the pinned archive size
and a 30-minute deadline; only verified members are published, without following
output symlinks. See the [input downloader](distribution/download_inputs.py) for
the current container checks. An already authenticated stage-zero patch can
also be supplied to the builder with `--delta`.

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
time. The JSON is atomically replaced at startup, before each suite or compilation
phase, and after each accounted suite result. An interrupted run retains the last
checkpoint with `complete: false`, `ok: false` and `active_suite` naming the active
suite or compilation phase (`null` between phases). Only normal completion of
both classes sets `complete: true`; `ok` then contains their combined verdict.
A failed report write propagates before the final PASS, leaving the previous
report intact if atomic replacement fails. Without `--json`, no report is written.
These checkpoints report suite progress, not per-suite timeouts or game/hardware
acceptance. Use the timings before changing CI scheduling or reducing a test.
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
and the limitations of each checkpoint. Those historical ROM fingerprints and
battle-loop regression are in the [1.3.1 composition guide](sgp131/README.md).
For current 1.3.2 game, frozen package and document-only identities, use the
[authorities above](#five-language-132); the current package requires its explicit
contract rather than the historical packager default.

The [complete native Box move caller](docs/validation/native-box-move-caller-source-rom-1.3.2.md) now joins move54, PP-Up62,
MaxPP/NARC/30SDK/DIV and PP58 in one uninterrupted context. Three original
EN calls pass with51565 instructions total,26 mapped pages and32 rejected
forgeries; the native caller stack carries the PP value. Independent1242-byte
lineage matches eight exact EN/IT images, with null plaintext physical offsets
for compressed owners. Original C compilation, natural gameplay/CARD, other
slots and physical save validation remain outside this scope.

The [native trainer first-move prefix](docs/validation/native-trainer-first-move-prefix-source-rom-1.3.2.md) follows an exact108-byte
trainer record through the Mon veneer and complete Box caller, then advances
cursor/index once. Three original runs pass with51613 instructions,26 mapped
pages,45 raw falsifiers and three complete cached-data input controls. Entry
is an explicit owned fixture inside the type3 constructor; the stop is before
the first loop branch, with no full-trainer, lost-checkpoint, natural gameplay
or save claim. The pinned C-definition comparator also corrects two previously
mislabeled callsite hashes while preserving earlier native evidence.

The [complete native Mon PP-Up setter](docs/validation/native-mon-ppup-setter-source-rom-1.3.2.md) verifies the separate party100/PID
and Box128/checksum transaction in one context. Three original calls pass with
17481 instructions total,8 mapped pages,24 transcript falsifiers and eight-image
bounded lineage. Same-count convergent inputs and party roundtrip false greens
require transient evidence; OFF retains endpoints without a native trace. An
owned50-halfword qualifier and CPU-free verifier are reusable. Original C
compilation, other attributes, natural activation and physical SAVE remain outside
this proof; no gameplay or installed ROM changed.

The [complete native move/PP-Up Reset](docs/validation/native-mon-reset-source-rom-1.3.2.md) connects its four actual child
calls, two MaxPP/NARC transactions and live guest Value words in one context.
Three first-attempt Reset runs pass with105568 instructions,26 pages,32 raw
falsifiers and three cached-input controls;20 ROM-free tests and six owned64k
limit cells cover the new bounds. Contextual checks preserve stack residues
and keys02B4→02B1→02A8. Original C compilation, natural gameplay and physical
SAVE remain outside this proof; no game or installed ROM changed.

The [original Reset C compilation experiment](docs/validation/native-reset-c-codegen-source-rom-1.3.2.md) authenticates an unchanged
PRET definition, minimal ABI projection, one LLVM object, four internal BL
relocations and three guest linkage thunks. ELF/ABI readback, owned frame
ON/OFF checks and three compiled guest cells pass (105586 instructions). It
reuses the executed native baseline and separates full per-build verification
from scoped cross-build semantic equality. No ROM build or speedup is claimed.

The [pivot/Shell Bell order case](docs/validation/uturn-shellbell-order-source-rom-1.3.2.md) identifies the installed command213
handler and prefix boundaries. It rejects a late-consumer premise using source
and exact EN/IT bytes, without inventing healing-loss evidence or launching a
new CPU campaign. The existing U-turn compatibility failures remain separate.

For the ordinary after-move item path, the [Shell Bell static reader](docs/validation/ordinary-shellbell-source-rom-1.3.2.md)
connects source aliases, controller37, code/data boundaries and actual item253
mapping. It is a compiler-free readback, with no new healing execution claim.

The [owned continuous dispatcher experiment](docs/validation/ordinary-shellbell-source-rom-1.3.2.md#owned-continuous-dispatcher-qualification)
adds an authenticated44-byte ASM fixture and compiler-free raw reverification.
Its two passing owned cells qualify the loop/BLX/frame, with no ROM or original
API execution. The native ordinary Shell Bell caller proof remains separate.
