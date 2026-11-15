# The runtime test bench

For current source-to-ROM work, start at
[Linking source to an exact ROM](#linking-source-to-an-exact-rom). The early
sections describe the historical melonDS bench; source-only tests and byte
readback do not require building that emulator.

Every runtime claim in Sacred Gold Plus 1.2 — "the game is still alive", "the patched literal
reaches RAM", "the repel re-arms" — comes from the same place: a headless build of melonDS,
driven by a scripted input timeline, writing a per-frame log that automated gates then judge.

**No binary is distributed here. You build it yourself.** What this repository ships is the
harness source, the core patch, the input scripts and the gates.

---

## 1. What it is

`source/runtime/` contains a small POSIX command-line frontend around an unmodified, pinned
melonDS core:

| file | role |
|---|---|
| `README.md` | build and replay instructions, recorded results, declared limitations |
| `CMakeLists.txt` | build definition; `MELONDS_SOURCE` is a parametric cache path, no personal path is baked in |
| `main.cpp` | the CLI: command loop, input timeline, per-frame sampling, capture and export |
| `platform.cpp` | the platform glue the core expects (POSIX file and dynamic-library APIs) |
| `hg_trace.h` | the observation counters the core patch feeds |
| `patch_core.py` | applies the core patch, and only to the expected commit |
| `melonds-observation-hooks.patch` | the reviewable diff: three hunks, in `src/ARM.cpp` and `src/NDS.cpp` |
| `source-provenance.json`, `SHA256SUMS` | provenance of each distributed file |
| `inputs/*.script` | the public, sanitised input timelines |

The core patch adds observation counters only. It does not patch ROM instructions and does not
change guest registers, memory or cycle accounting.

## 2. Building it

The required core is official melonDS commit
`906e9ebb27da8c6a715cd7abab4abfe8a8d29427`. Use a separate checkout: `patch_core.py` verifies
the complete build-consumed filesystem tree against the pinned Git objects before touching
anything and is idempotent only on the exact two-file observation patch. It rejects other
modified, untracked and ignored entries, shared hardlinks and unexpected types/modes without
trusting index flags, status output or replacement refs. CMake repeats that verifier immediately
before `add_subdirectory` evaluates the core and whenever the `core` target is built. Index-only
staged content is outside this assertion because CMake never consumes it.

Requirements: Git, Python 3.9 or newer, CMake, Ninja and a C++17 compiler. No Qt, no SDL, no
proprietary BIOS. The build has been exercised on macOS ARM64 with AppleClang; Linux has not
been tried and Windows platform glue is not implemented.

From `source/runtime/`:

```sh
git clone https://github.com/melonDS-emu/melonDS.git work/melonDS
git -C work/melonDS checkout --detach 906e9ebb27da8c6a715cd7abab4abfe8a8d29427
python3 patch_core.py --source work/melonDS
cmake -S . -B work/build -G Ninja \
  -DMELONDS_SOURCE="$PWD/work/melonDS" \
  -DHG_BUILD_WAIT_LOOP_TEST=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build work/build --target hg_runtime --parallel 8
```

`MELONDS_SOURCE` accepts an exact pinned checkout. Set `CMAKE_MAKE_PROGRAM` if Ninja is not on
`PATH`. Choose an empty output directory when rerunning; the build writes everything under
`work/`, outside the checkout. The configure/build rechecks close pre-existing dirty-input
bypasses; a concurrent same-account writer after the last check remains outside this cooperative
local-tool boundary.

The 1.3.1 successor workbench uses the same cooperative boundary. Its root,
lock, transactions, journal, consumer leases and long-lived private scratch
anchor are bound to recorded inodes. During UI composition it changes cwd with
`fchdir` to the already pinned scratch descriptor, so compiler and verifier
relative paths remain on that inode even if its directory entry is renamed;
cleanup is descriptor-relative. A concurrent process under the same account
can still force a refusal or make the next session reject the changed anchor.
It is not an authorized concurrent writer and no availability guarantee is
claimed against it.

There is also an optional ROM-free instruction probe (`hg_wait_loop_test`, off by default in a
standalone build) that runs individual ARM words through the core's own interpreter tables. It
takes synthetic buffers of zeros and two ordinary instruction words — not ROM files — and is
the cheapest way to confirm a fresh build behaves like the recorded one. `README.md` in
`source/runtime/` has the exact reproduction.

## 3. Running it

```
hg_runtime --rom ROM --out DIR [--frames N] [--script FILE] [--interactive]
           [--sram FILE] [--load FILE]
```

The standard form of a proof run:

```sh
hg_runtime --rom "$ROM" --sram "$SAVE_COPY" --out runs/<name> --script runs/<name>.script
```

- `--sram` takes a **copy** of the test save. `--load` restores a savestate when a run has to
  start from a specific scene.
- A cold run (boot plus `--sram`) is worth more than a savestate run, and the two are not
  interchangeable. Which one was used is declared in the result.
- Each invocation starts a new emulator process. The harness never searches for, nor silently
  overwrites, a save sitting next to its input.
- `--interactive` is never used in a run that produces a proof.

Script commands cover key presses, touch coordinates and releases, bounded waits, memory reads,
per-frame watches, named captures and SRAM export. The public scripts in `source/runtime/inputs/`
contain only input, waits, reads, status and local exports: no RAM writes, no cheats, no freezes,
no savestate loads (checked 18/09/2026: `grep -n '^write' source/runtime/inputs/*.script` finds
nothing).

That guarantee does **not** extend to the scripts that `anim2/tools/copioni.py` (the
`PROLOGO_FREDDO` prologue every sub-command starts from) and `squadra-lotta/tools/copione.py`
generate for the anim2/Bag/party proof runs. Their prologue contains exactly one write:
`write 0x023D8716 1 1`. `0x023D8716` is the "animations" option byte inside the Plus save
chunk — the same byte `borsa_cache.c:13` and `squadra_cache.c:13` gate their fast paths on — and
the write is there because the option defaults to **off**: without it the anim2 motion, the
Bag-in-battle cache and the party-move cache never engage, and the run would be measuring the
native fallback path instead of the feature under test. A run built from one of these generated
scripts is therefore **not** a "ROM-intact proof" in the sense the rest of this document uses
that phrase: it starts from one RAM byte set deliberately away from its shipped default, and
that has to be declared alongside the result the way any other non-default setting would be.

### Deterministic settings

These are part of every proof, and every run records them in `session.txt`:

- ARM **interpreter**, never the JIT (the JIT is disabled at configure time);
- **software** renderer, no OpenGL;
- **FreeBIOS** and **generated firmware**, so no proprietary image is involved;
- fixed initial clock;
- no Qt/SDL, no GDB stub, no release LTO.

Two runs of the same ROM, same save and same script on this configuration produce the same
frame log. That is what makes a comparison against a counter-proof meaningful.

### Output of a run

Everything lands in `--out`:

| file | content |
|---|---|
| `frames.csv` | one row per guest frame: frame number, `RunFrame`-only host nanoseconds, IPKE scene identity, `arm9_pc`/`arm7_pc` end-of-frame samples, the game's vblank counter, observation counters, and any address the script asked to watch |
| `commands.log` | the commands actually executed, in order, with their frame |
| `stdout.log` | everything the harness printed, including the answers to `read` and `status` |
| `session.txt` | the run's configuration: core, settings, ROM path, RTC, timing/scene observer and initial trace state; later trace changes are frame-stamped in `commands.log` |
| `latest.ppm` plus the captures the script named | frame captures |

Three cautions that have already cost time here: `arm9_pc` is an end-of-frame *sample*, not a
visit count; `host_runframe_ns` excludes CSV and audio work and is not display FPS; and harness
counters accumulate across state restores, so a run that reloads a state cannot be compared to
one that does not.

---

## 4. The automatic gates

They live in `source/verifiche/` and are meant to be used as exit-code gates, not read by eye.

### `rileva_crash.py` — is the game alive?

```sh
python3 source/verifiche/rileva_crash.py runs/<name>/frames.csv [...]
```

Exits 1 for an exception, a sustained fixed-PC loop outside the vector, or an
unusable trace. A changing-PC `STALLO` remains inconclusive and needs a separate
assertion that the intended gameplay state was reached.

**The process exit code is not a verdict.** This script exists because a defect stayed invisible
for hours: the game had taken an exception, but the harness's return code stayed 0, the emulator
kept producing frames, and the captures were byte-identical. It looked like a paused screen.

The verdict needs two signs together:

- `arm9_pc` stuck inside the ARM9 exception vector (`0xFFFF0000..0xFFFF01FF`), **and**
- the game's vblank counter no longer advancing.

Neither sign alone is enough. The CPU passes through the vector during normal operation
(measured: over twelve thousand frames of a healthy run), and the counter also stops during a
legitimate blocking load — which has already been mistaken for a fault in this project. What
identifies a crash is the *tail*: from some frame on, the counter stops and the PC does not
change. A short stall is noise and is ignored.

The detector measures the final constant-PC suffix independently of the first
stopped-vblank frame. A loading transition can stop vblank before taking an
exception; its earlier changing PC samples must not hide a later frozen suffix.
Six ROM-free regression cases cover this boundary, ordinary vector visits and
inconclusive blocking loads. The 1.3 playtest found this diagnostic gap during
an instrumented debugger warp; normal-input controls are reported separately
from instrumented scene setup. `BLOCCATO` is a conservative rejection of a
sustained fixed-PC sample sequence, not proof of an irreversible deadlock:
sampling can alias a legitimate busy loop. Inspect the reached state and a
longer observation before diagnosing the game.

### `collauda_repellente.py` — did the fixed behaviour actually happen?

```sh
python3 source/verifiche/collauda_repellente.py --corsa runs/<name>
```

Four gates in order, each able to fail, exit 0 only if all four pass:

1. the game is alive at the end (delegated to `rileva_crash.py`);
2. the watched repel counter actually reaches zero;
3. something appears on screen when it expires — the frame after zero differs from the frame
   before;
4. the counter goes back above zero: the re-arm fired.

Gate 2 is the guard against a result that cannot fail. Without it, "no crash" on a run where the
repel never expired would be a false green.

`source/verifiche/riserva_arm9.py` and `source/verifiche/test_riserva.py` are the corresponding
static gates for the ARM9 reserve layout.

---

## 5. Run discipline

The bench only produces evidence if the run is set up to be able to fail.

**Criteria are written before the run.** Each run has a dated criteria note, written before the
harness is started, stating: the ROM under test with its SHA-256 and the counter-proof ROM; the
**precondition** without which the run proves nothing; the numbered list of green gates, each
one able to fail; the **discriminant**, the measurement that separates the correct case from the
broken one; what result makes the run red; and the limits declared in advance — what this run
will not cover.

**The counter-proof runs first.** Run the **unfixed** ROM, with the same fixture and the same
script, and check that it fails. If the fixed ROM and the counter-proof give the same result,
one of the two is not measuring anything: stop. In 1.1 this rule is what saved both the repel
fix and the camera fix — each of them crashed the unfixed ROM at a specific frame and did not
crash the fixed one.

**No criterion is added, removed or softened after a result is seen.** Deleting a failing test
without fixing its cause is not a result.

**Frames are looked at.** A gate saying "the frame changed" does not say *what* it shows. The
captures named in the criteria are opened and examined, and the result states which ones.

**New behaviour is measured against the previous release**, not against a recollection of how it
used to be: same fixture, same script, two ROMs. Earlier recorded outputs may be reused as the
reference instead of being regenerated, as long as the reuse is declared.

Finally: what the bench does not establish is written down every time. It says nothing about
real DS hardware, nothing about Android front-ends, nothing about performance on a handheld —
and, as `docs/contracts.md` notes, nothing about ARM9 cache behaviour, which melonDS does not
model.

---

## 6. Test saves

Test saves are **described here, not included**. Saves, ROMs, BIOS images, firmware, savestates
and RAM dumps never enter this repository, are never attached to an issue or a pull request, and
are never opened as text. They are worked on through scripts that print numbers; a SHA-256, a
size or an offset is metadata and may be quoted, the bytes may not.

A save is useful for this project when:

- it is a **raw cartridge SRAM image**, 524,288 bytes, double-buffered, with no emulator header
  — that is what `--sram` expects, and no conversion is needed;
- its **position is known and stable**: which map, indoors or outdoors, and the coordinates. An
  outdoor town save and an indoor save are not interchangeable; frame-cadence measurements need
  the outdoor one;
- it carries the **items a gate needs** — a repel for the repel gate, the field moves needed to
  reach a distant map for a camera gate;
- it leaves **something still to do**: at least one gym leader not yet defeated, for any gate
  that measures trainer levels. A save where everything is beaten cannot prove a level change;
- its **facts have been read back in RAM**, not only offline. Badge counts read from an
  unverified offset in the file were wrong here once, and only a bench run reading the game's own
  structures caught it;
- it is recorded by **SHA-256**, and every run uses a **copy**, never the original file.

Different gates want different saves — a prepared UI fixture, an outdoor town save, a
late-campaign save — so keep several, describe each one by map, position, badges, party and
inventory highlights, and state in each result which one was used.


## Linking source to an exact ROM

A source-to-ROM attribution records the source revision, compilation recipe,
placement in the image and executable entry path for one component. Contributors
can reproduce the checks with their own compatible input ROM. The public
repository carries source, tools, hashes and the explanation of the evidence.
Keep ROM images, extracted game data, saves and raw captures in private storage.

Keep C calling-convention guarantees separate from observed volatile registers
and CPSR. Full16 is an attribution check over exact instructions: residual R1
or LR values describe the exercised input/revision and add no guarantee to a
C prototype. A source-level alternative can return the same pointer or scalar
while differing in these registers or memory reads. Check actual callers before
treating implementations as interchangeable.

### Use attribution to decide a maintenance change

Start with a reproducible symptom or a measured cost and a finite question.
Record the source owner, exact image, trigger, expected result and a counterexample
before extending a trace. The deliverable is a decision about a bug or a cost,
with a regression and a bounded change proposal when supported. An attribution
count does not measure game improvements or whole-ROM reconstruction progress.

| Evidence available | Reuse or next check |
| --- | --- |
| Same complete component bytes and relevant metadata in two images | Reuse the static attribution for that interval; verify caller state, data and localized resources separately |
| Same instructions with different literals, tables or placement | Resolve each image's data and call targets; do not apply a global regional address shift |
| Recompiled source with different bytes | Check relocations, ABI and side effects, then compare explicit semantic outputs on a declared domain |
| A suspected caller path contradicted by order or guards | Preserve the counterproof and close that hypothesis before creating a new probe |

For correctness, a regression must expose the original defect and protect the
relevant state, including negative paths and fallback arguments. For performance,
measure the same path before and after on the intended backend; isolated guest
instruction counts do not establish DS frame time. A proposed installation also
needs its own save-copy and cold-restart validation. Keep these acceptance steps
distinct from source identification and byte readback.

### Choose the question and find its owner

To rebuild the game, follow the [complete stage map](#from-the-source-tree-to-the-complete-rom)
and its production configuration/toolchain requirements. For a project feature,
find its [owner](../features/README.md), source, installer and independent reader.
For retained game code, open the attribution guide: recovered assembly with no
installer is a comparison artifact, not a replacement inserted by the builder.

| Case guide | Qualified execution scope | Still modeled in that case |
| --- | --- | --- |
| [Send](validation/native-fs-send-source-rom-1.3.2.md) | isolated copied Find entry | ExecuteSync |
| [ExecuteSync](validation/native-fs-exec-sync-source-rom-1.3.2.md) | isolated copied Send entry | Translate, Release, Next |
| [Release](validation/native-fs-release-source-rom-1.3.2.md) | isolated copied ExecuteSync entry | empty Wakeup |
| [Empty Wakeup](validation/native-os-wakeup-source-rom-1.3.2.md) | isolated copied Release entry | none on the empty path; nonempty scheduling excluded |
| [Release + empty Wakeup](validation/native-fs-release-wakeup-source-rom-1.3.2.md) | one isolated original Release context | none on the selected path; upstream translation/Next excluded |
| [Empty Next](validation/native-fs-next-source-rom-1.3.2.md) | observed parent return, original LDR/BL bridge | none on selected empty/no-callback paths; upstream excluded |
| [ExecuteSync join](validation/native-fs-exec-sync-join-source-rom-1.3.2.md) | observed native NextNULL return | none in the seven-start suffix; original Send POP and upstream excluded |
| [ExecuteSync with native callees](validation/native-fs-exec-sync-native-callees-source-rom-1.3.2.md) | one context from copied Send entry through Release/Wakeup/Next/IRQ and final wrapper | Translate error4/R0 projection only; original Send POP and natural filesystem excluded |
| [Send with native callees](validation/native-fs-send-native-callees-source-rom-1.3.2.md) | one context from actual Find→Send input through Send POP to stopped Find return | Translate error4/R0 projection only; higher caller and natural filesystem excluded |
| [Translate](validation/native-fs-translate-source-rom-1.3.2.md) | actual copied Send boundary; native transient flags, dispatch and error STR | value-only default handler with zero RAM writes; native handler and caller integration excluded |
| [Send with native Translate](validation/native-fs-send-translate-native-source-rom-1.3.2.md) | one continuous Send/ExecuteSync/Translate/Release/Wakeup/Next/IRQ context; actual isolated whole boundaries and full final fields | value-only default handler; native handler, natural filesystem and higher caller excluded |
| [Default FindPath prefix](validation/native-fs-default-findpath-source-rom-1.3.2.md) | actual default entry, prefix28 to stopped nested Translate(SEEKDIR), deeper stack with104 derived bytes | zero service models; complete default return, nested filesystem and higher caller excluded |
| [Nested SEEKDIR dispatch](validation/native-fs-nested-seekdir-source-rom-1.3.2.md) | parameter2/stored command4, slot2 to stopped default; actual AFTER image anchor and24 derived guard bytes | zero models; projected flag input rejected as actual; default execution/natural filesystem excluded |
| [Complete cached SeekDir](validation/native-fs-cached-seekdir-source-rom-1.3.2.md) | whole SeekDir/ReadTable/memory callback/Copy return, authentic resources with disjoint synthetic CPU/File/stack; portable ROM-derived mode also checked | zero models; natural caller/DTCM and Italian execution excluded |
| [Complete cached FindPath](validation/native-fs-cached-findpath-source-rom-1.3.2.md) | whole normalized-path search through eight native functions to ID129; independent functional/ARM oracles and CPU-free evidence verification | zero models; synthetic caller/RUNNING projection; natural wrapper, NARC140 and payload I/O excluded |
| [Complete cached Convert](validation/native-fs-cached-convert-source-rom-1.3.2.md) | complete API through18 native functions, real move archive path to ID140; independent ELF/FNT/ARM/IRQ checks and CPU-free raw verification | zero models; synthetic CPU/stack, explicit root-BSS provenance and proc602→2 projection; natural card protocol and payload I/O excluded |
| [Complete cached Open](validation/native-fs-cached-open-source-rom-1.3.2.md) |22 native functions from actual pathname through FAT140 to a live handle, with a finite equality failure and temporary-stack lifetime checks | zero models; explicit input projections; no payload/card protocol or natural caller claim |
| [Memory-archive native Read](validation/native-fs-memory-read-source-rom-1.3.2.md) | Open/Read/Seek/Read/Close through30 original SDK functions plus a separate compiled caller; exact owned NARC32 bytes and native completion | explicit hybrid memory-archive projections; no natural CARD protocol, native Thumb parser or PP-consumer claim |

| [Original NARC caller and native SDK](validation/native-fs-memory-narc-source-rom-1.3.2.md) | actual Thumb wrapper/parser, fifteen outer API calls, seven source-selected reads and close; 6262 original instructions with mixed ISA qualification | zero models or project caller; explicit memory archive, original C compiler and natural CARD still open |

| [Complete native PP getter](validation/native-pp-memory-getter-source-rom-1.3.2.md) | actual GetMoveAttr, stack buffer, native NARC/SDK and scalar PP load; source-memory PP15→1 causes native return1 | zero models/project caller/runtime host writes; explicit memory archive, no PP-Up division/Mon setter or natural CARD claim |
| [Complete native MaxPP](validation/native-maxpp-memory-source-rom-1.3.2.md) | source-bound 524-byte division rebuild, native clamp/multiply/divide/u8 return and PP source causality | four finite inputs and explicit memory archive; no original Thumb compilation, natural CARD or Mon mutation claim |
| [Native Mon segment cipher](validation/native-mon-cipher-source-rom-1.3.2.md) | original wrapper/core/local LCG on owned128B;64seed/XOR writes/fullABI/maps with seed counterproof | fixed isolated domain, no original C compilation/decrypt/Mon setter/checksum or global RNG claim |
| [Native Mon checksum](validation/native-mon-checksum-source-rom-1.3.2.md) | native LEhalfword/u16 sum, odd-tail exclusion/overflow/zero and fullABI with existingfrontend | four owned input profiles; no Ccodegen/Mon lifecycle/composedchecksum-cipher or naturalcaller claim |
| [Native Mon substructure selector](validation/native-mon-substructure-source-rom-1.3.2.md) | full128table-domain selections, source/pointer/ABI/replay plus retailITliteral relocation and pinnedPRET adapter |130isolated API calls; no Ccodegen/Box header read/completegetset or naturalcaller claim |

| [Complete encrypted Box PP-Up getter](validation/native-box-ppup-source-rom-1.3.2.md) | native decrypt/checksum/header-PID selection/field load/reencryption; checksum-preserving counter, transient writes and full-state replay | three isolated EN calls on synthetic Box records; no original C build, natural caller, other attributes or save claim |

| [Complete encrypted Box PP setter](validation/native-box-pp-setter-source-rom-1.3.2.md) | native PP write/two checksums/header update/new-key encryption; Value counter, full void ABI and136-byte frame replay | three isolated EN calls; static caller only, no MaxPP→Value bridge, original C build or save claim |

| [Complete encrypted Box move setter](validation/native-box-move-setter-source-rom-1.3.2.md) | native halfword/idempotent move and checksum stores, post-ADDSP ABI, causal key change and full replay | three isolated EN calls; complete caller static only, no original C build/save/other slot claim |
| [Complete native Box move caller](validation/native-box-move-caller-source-rom-1.3.2.md) | native move→PP-Up→MaxPP/NARC/SDK/DIV→stack byte→PP setter; uninterrupted full16/map/access proof and eight-image lineage | three exact prepared EN calls; original C build, natural gameplay/CARD, other slots and physical SAVE remain unproved |
| [Native trainer first-move prefix](validation/native-trainer-first-move-prefix-source-rom-1.3.2.md) | exact type3 record+8→veneer→full Box caller→cursor/index/CMP; complete cached-data pins,106B historical code and strict source-definition comparison | three own prefix entries before the first BLT; no lossless prior checkpoint, full trainer, natural gameplay, original C build or SAVE claim |

A later isolated callee result does not upgrade an earlier model. Joining it
requires its own caller/state/ownership proof. The independent
[frozen-contract comparison](validation/native-fs-release-source-rom-1.3.2.md#independent-comparison-with-the-earlier-frozen-contract)
checks the earlier Release field predictions against the later native records;
it explicitly reports ABI differences and does not claim complete-caller or
whole-RAM equivalence.

Follow a guide's exact input hashes, recipe and private-input schema before its
prepare/readback mode. Prepare-only authenticates dependencies without guest
execution; it still needs the ROM, ancestor reports and objects. Source-only tests
need the project Python environment, which can import Unicorn without starting
a guest. Missing private inputs remain skips and do not establish qualification.

### Public discovery for developers and automation

The [read-only catalog](../attribution_cases.py) runs with Python3.9+ standard
libraries, without ROMs, optional packages, `local/`, Git history or producer
imports. It derives report names from the existing validation index and uses the
public allowlist as its file boundary. Any editor or code assistant can consume
the same relative-path JSON; no conversation memory or vendor-specific setup is
needed.

Run from the repository root:

```sh
python3 -I -S -B source/attribution_cases.py list --match native-fs --json
python3 -I -S -B source/attribution_cases.py show native-fs-release --json
python3 -I -S -B source/attribution_cases.py check --json
python3 -I -S -B -m unittest discover -s source/verifiche \
  -p test_attribution_cases.py -v
```

`list` covers indexed validation reports; `show` currently describes commands
for Send, ExecuteSync and Release. Other reports return their guide and explicitly
unknown command metadata. Command arrays are descriptions with placeholders and
`cwd: "."`; the catalog never executes them. Send uses directory environment
variables and fixed artifact names; ExecuteSync and Release use different JSON
config schemas. Consult the linked guide rather than assuming symmetry.

`check` verifies indexed public paths and the three described interfaces' supported
static flag declarations, replay environment names and filename patterns. Static
inspection supports literal strings and simple string loops; unresolved argument
syntax is an issue. It does not prove parser choices, defaults, exclusivity,
new required options, bytes, execution or acceptance. Those remain the original
tools' and tests' responsibilities. JSON scope is always navigation-only.

### From the source tree to the complete ROM

Use the [source build entry point](../README.md) and the
[current composition guide](../sgp131/README.md) for the complete build. The
following map connects component attribution to that route; the linked guides
contain the production commands, configuration objects and toolchain pins.

| Stage | Inputs and source owner | Producer and verification |
| --- | --- | --- |
| Retail → base1.1 →1.2.5 | Own exact retail ROM, pinned base patch in [base11.json](../sgp12/base11.json), project feature sources | [sgp12 builder](../sgp12/costruisci.py); per-owner compilation/installers and independent block readbacks; retain every input/output hash |
|1.2.5 → historical V4 | Exact1.2.5 and208 pinned published source blobs | [Authenticated bootstrap](../distribution/bootstrap_13.py) and its [manifest](../distribution/bootstrap-13-v4.json); require the documented V4 hash for each language |
| V4 → current EN/IT core | Current UI/mechanics sources, exact production compiler/Python/data and explicit owner configuration | [workbench](../sgp131/workbench.py) through the identity stage; stage receipts, independent readbacks and final candidate hash |
| EN core → FR/ES/DE presentation | Exact English core, matching owned regional donor, authored locale recipes | [localization composition/readback](localization.md); retain regional substitutions, preimages and exact output identity |
| Candidate → tested exact image | Generated ROM plus its complete source/configuration/tool receipts | Compare the intended [current game contract](../distribution/game-1.3.2-r4.json); run only the required validation on that exact candidate, recording separate runtime/save/hardware coverage |

The bootstrap uses historical HF01 only as a build intermediate; current
composition upgrades it to HF02. Initial all-inert and current player profiles
have different owner configurations. Follow the complete guide's activation
and identity checks rather than assuming that a version label selects a profile.
A current source build, a historical published build and a changed candidate
must retain their own receipts.

Within a project-owned stage, follow C/assembly → compiler/linker → ELF/symbols →
payload → installer/preimage/hook → composed cartridge readback. The component
case identifies its owner in that complete route. Retained retail/SDK code can
instead survive all composition stages unchanged: record its inheritance and
verify it separately. A recovered attribution assembly with no installer, such
as the native filesystem cases below, reconstructs bytes for comparison; it
does not rebuild the original game C or insert a replacement into the ROM.

A complete file build establishes its output bytes. The later caller/ABI and
execution checks below establish which of those bytes execute under the tested
conditions. Preserve both chains; neither receipt substitutes for the other.

### Using newer PRET references

Keep a production reference and a newer research reference separately identified.
Record the actual repository root, full commit, dirty state and hashes of the files
used. A Git command in a borrowed source directory can resolve its containing
repository; that HEAD does not authenticate the borrowed component. Keep reference
clones read-only: current PRET configuration can generate files inside the source
tree and fetch dependencies. Do not use a build or dry run as a read-only inventory.

The inspected [HeartGold snapshot](https://github.com/pret/pokeheartgold/tree/6bf138d6035aa6b43d6f8f4132a12df70f86dcec)
and [Platinum snapshot](https://github.com/pret/pokeplatinum/tree/62bdaacdca6c56a6a396f3e9911e2f922b79bba8)
provide reusable source, naming and build references. Their configured targets are
USA releases. An Italian language enum does not establish an Italian build target.
The HeartGold target SHA-1 `4fcded0e2713dc03929845de631d0932ea2b5a37`
matches the owned USA retail input pinned by this project. This authenticates the
input relationship; no fresh whole-ROM PRET rebuild was performed for this check.
The standard upstream recipes do not request a baserom, but their Meson,
MetroSkrew/compiler and wrapped library dependencies must also be acquired and
authenticated before a clean offline build can be claimed. Keep checksum checks
enabled for the first matching build and record compiler versions per library,
generator inputs, ELF/maps and complete output identity.

Useful information need not wait for that full build. At the HeartGold snapshot:

- `tools/msgenc/charmap.txt` has SHA-256
  `58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded`,
  identical to the older production charmap, with a different path.
- `tools/py_scripts/scrcmd.json` has SHA-256
  `1248d46548280a8f3c9c2d220788a915c03b4dc1951b4f7bb1c6317d07f45061`.
  Compared with the production `fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a`,
  all 853 entries retain their non-name JSON fields and `argtypes` are identical.
  IDs 315, 316 and 317 acquire the names
  `BindEcruteakGymCandleToTrainerSprite`, `UnbindEcruteakGymCandleFromTrainerSprite`
  and `ExtinguishEcruteakGymCandle`. Follow the implementations in
  `src/scrcmd_c.c` and callers in `scr_seq_0953.s` as research leads.

Reproduce this comparison with
[`confronta_metadata_pret.py`](../features/borsa/tools/confronta_metadata_pret.py)
and your own two metadata files; the [Bag README](../features/borsa/README.md)
gives the command and ROM-free counterexamples. Names alone do not prove ABI,
function equivalence or execution. The current builders retain their exact
metadata hash checks. Passing the new charmap path directly also fails consumers
which derive the metadata path relative to its parent: byte identity does not
establish path or tool compatibility. Do not replace `SGP_PRET_SOURCE` globally.

A concrete reuse is the [cached SeekDir case](validation/native-fs-cached-seekdir-source-rom-1.3.2.md):
HeartGold filesystem metadata and the NitroROM packer independently explain root
FNT start368, first_file129 and directory count46. The root parent field contains
that count, which prevents an incorrect parent0 expectation. Cached resources
were recovered from authenticated earlier raw material before any new capture.
The resource reader also rejects the old test stack inside the natural FAT.
These checks improve the method immediately without waiting for a full PRET build.

For each new question, reuse upstream source and tooling only after checking its
scope against the existing owner, recipe and independent ROM reader. Platinum
offers comparative implementations and bug documentation; it is a different game,
not a drop-in HGSS executable, regional donor or address table. Preserve project
credits and assess the applicable license before copying upstream code or assets.
Public instructions may link sources and record hashes; keep owned cartridge
data and extracted fixtures private.

The existing Italian Plus build preserves the common USA executable/internal
game identity while localizing presentation. Rebuilding an exact Italian retail
cartridge would require a separate regional target, resource/layout reconciliation
and an exact Italian checksum. It is not a prerequisite for reusing PRET knowledge
or continuing the current [localized Plus route](localization.md).

The [Mon source alignment adapter](../features/trainer-strategy/tools/confronta_mon_pret.py)
adds a concrete component comparison: checksum, substructure selector, cipher
and local LCG function fragments are unchanged between the productive HGSS pin
and newer HeartGold snapshot, despite whole-file drift. Platinum provides the
same32×4 block-index mapping through a different switch/macro implementation;
its checksum declares a different return type. The [selector case](validation/native-mon-substructure-source-rom-1.3.2.md#aligning-with-the-newer-pret-sources)
records commands, pins and hashes. This source comparison uses no ROM or CPU;
compiled addresses, ABI and language targets retain their own verification.

These source-only entry points are useful before a build or a new capture. They
use Python's standard library; the two pinned-tree comparisons also use Git.
Run from the project root. Supply your own read-only reference trees and fresh
output files outside `source/`; none of these commands changes a production pin.

| Question | Tool and inputs | Result and limit |
| --- | --- | --- |
| Did script metadata change names or argument structure? | [Metadata comparator](../features/borsa/tools/confronta_metadata_pret.py), `--before OLD_JSON --after NEW_JSON` | JSON on stdout with both input hashes; exit1 for incompatible structure. Names do not establish ABI. |
| Do Mon primitives and block mappings agree across references? | [Mon comparator](../features/trainer-strategy/tools/confronta_mon_pret.py), `--reference PRODUCTIVE_HGSS --heartgold-ref NEW_HGSS --platinum-ref PLATINUM --json PRIVATE_JSON` | Four HGSS fragments and32×4 mappings; records the Platinum checksum return-type difference. No executable interchangeability claim. |
| Are the actual move/trainer C definitions unchanged? | [Definition comparator](../features/trainer-strategy/tools/confronta_box_move_pret.py), `--reference PRODUCTIVE_HGSS --heartgold-ref NEW_HGSS --json PRIVATE_JSON` | Six complete definitions, exact extents and hashes. Rejects missing/ambiguous definitions and prevents mistaking a callsite for a definition; bounded ordinary C syntax only. |

The pinned-tree tools require the clean productive fork at
`cb614ad23449d5852b40321dc409c4143872b35c`, HeartGold at the snapshot above,
and, for the Mon comparison, Platinum at its snapshot above. They authenticate
the participating files as well as the commits. A different revision needs an
explicit comparison adapter and counterexamples, rather than bypassing a hash
check. For example:

```sh
python3 source/features/trainer-strategy/tools/confronta_box_move_pret.py \
  --reference /path/to/productive-hgss \
  --heartgold-ref /path/to/newer-pokeheartgold \
  --json /path/to/private/fresh-definitions.json
```

The [complete Box move caller](validation/native-box-move-caller-source-rom-1.3.2.md)
records the dated definition-hash correction; the
[trainer prefix](validation/native-trainer-first-move-prefix-source-rom-1.3.2.md)
uses those source findings alongside independent ROM bytes and native execution.
The distinction matters when recovering older notes: a matching symbol name,
callsite fragment or source text does not establish compilation or activation.

For comparative research, Platinum's pinned
[trainer data guide](https://github.com/pret/pokeplatinum/blob/62bdaacdca6c56a6a396f3e9911e2f922b79bba8/docs/datafiles/trainers.md)
and [move data guide](https://github.com/pret/pokeplatinum/blob/62bdaacdca6c56a6a396f3e9911e2f922b79bba8/docs/datafiles/moves.md)
help form questions about optional fields, generated records, PP metadata and
apparently redundant values retained for binary matching. Before transferring a
conclusion, find the HGSS definition, generator and consumer, then verify its
layout against the required ROM. These guides supply research questions, not
HGSS record offsets or a regional build recipe.

The [complete Mon setter](validation/native-mon-ppup-setter-source-rom-1.3.2.md)
adds a useful counterexample: two wrong-key cipher passes or no passes at all
can leave the same final100-byte tail. Its owned50-halfword loop and original
native transaction check intermediate plaintext, separate PID/checksum keys and
every preimage. The same endpoint is a reason to inspect the path, not sufficient
evidence that the required path ran.

The [complete Reset caller](validation/native-mon-reset-source-rom-1.3.2.md)
shows why allocation does not imply initialization: its second FILE retains
six words from the first NARC parser and two from a preceding cipher frame.
The adapter reuses parent instruction semantics and source checks on journal
views, while reconstructing actual entry/return registers, Value locations and
memory at each boundary. The new64k bound changes only audited cap nodes and
qualifies the return callback boundary; earlier8k/32k runners remain unchanged.

### Reuse execution evidence without rerunning the guest

The [complete FindPath verifier](validation/native-fs-cached-findpath-source-rom-1.3.2.md#reproduce-with-your-own-inputs)
adds `--mode verify --raw-dir`: it authenticates current sources, retained ELF
recipes, owned exact inputs, frozen fixtures and raw files, then rejudges every
context, access, preimage, page and control. It runs with Python standard library
and Git, without importing Unicorn or invoking the compiler. This makes review
and automation accessible to other development agents through normal CLI/JSON.
It is evidence replay, distinct from a new guest or natural activation.

Its finite ARM checker was first matched against the earlier manual SeekDir
oracle and native records, then tested for new width/writeback/carry cases.
For future code, inventory the new instructions and data lifetime before reuse;
a matching final result or a decoder's instruction names does not qualify a new
arithmetic operation. Keep independent source functional checks and native producer.

The [complete Convert composition](validation/native-fs-cached-convert-source-rom-1.3.2.md)
reuses18 authenticated objects without recompilation and adds native wrapper,
queue and return lifetime around the actual move-archive path. It illustrates
three extra checks: BSS has no initialized ROM offset, a previous synthetic
return gate can become a real callee in a larger composition, and IRQ Restore
must preserve current flags while restoring the saved I bit. New instruction
support is a bounded derivative with an automated AST drift test; the earlier
qualified helper stays unchanged. Its object JSON and prepare/verify modes can
be used by developers and other agents through ordinary Python CLI.

The [complete Open case](validation/native-fs-cached-open-source-rom-1.3.2.md)
adds an explicit lifetime check: replay the Convert prefix while its temporary
directory is still live, then allow subsequent native frames to reuse those
dead bytes. Its independently parsed FAT record and equality-size failure
separate a valid open handle from final-output coincidence. Preserve the source
bounds condition exactly; do not silently strengthen it in the oracle or infer
arbitrary malformed-archive safety from the finite ID140 test.

The [memory-archive Read case](validation/native-fs-memory-read-source-rom-1.3.2.md)
separates a new input configuration from code provenance: original ROM functions
read through the SDK's memory callback, while a small project caller supplies the
API sequence. Source plan precedes caller compilation, complete memory freeze
precedes oracle/CPU, and raw counters distinguish4252 ROM instructions from27
project instructions. A memory-backed payload is not evidence of the natural
CARD async/controller path. Preserve that distinction when extending a case.

### Establish the input and component

Record the complete input/output SHA-256, size, language, revision and patch
chain. Hash the actual working source and build inputs as well as recording the
Git revision. A dirty working tree can produce different code from that revision.
Record inherited components and the stage that inserts or replaces them.

Use the cartridge header, FAT/FNT, overlay table and module parameters to locate
the component. Record both its physical file offset and its runtime address,
including compression, autoload and relocation. Resolve each ARM or Thumb
branch through any veneer. Check the surrounding instruction window and data
references so that an address alone cannot substitute for a function identity.
Overlay IDs and addresses require verification for each input revision.

### Follow the recipe and independently read the image

For a payload built from this project's source, retain the compiler identity,
target, flags, source hashes, symbols and compiled output hash. Use its actual
installer to locate the hook, preimage, allocation and composition order.
Rebuild only the component needed for the question. Compare the emitted bytes
with the installed bytes after the relevant decompression or mapping step.

Use an independent reader to verify the hook target, payload, padding, guards
and unaffected content. It should parse the resulting image without calling the
installer being checked. A correct installer result must pass, and deliberate
changes to the payload, branch or protected region must fail the relevant check.
Preserve those negative cases when maintaining the reader.

The [Battle Bag component](../features/borsa-lotta/README.md) supplies an example:

| Link | Existing implementation |
| --- | --- |
| Source and ABI | `source/features/borsa-lotta/sorgenti/borsa_cache.c` |
| Compiler, flags and source manifest | `source/features/borsa-lotta/tools/compila.py` |
| Composition stage and preimage | `source/sgp12/blocchi/borsa_lotta.py` |
| Independent ROM readback | `source/features/borsa-lotta/tools/rileggi.py` |
| Compiled behavior and negative cases | `source/features/borsa-lotta/test/` |

For that component, overlay 8's Thumb call at `0x02223C30` reaches a hook in the
256-byte reservation at `0x023DBD00`. The recorded baseline contains 162 code
bytes, padding and a 16-byte canary. The compiler emits source fingerprints and
symbols. The reader resolves the hook independently and verifies the allocation
and unrelated content. These numbers identify the documented baseline recipe.
A changed source or compiler needs its own identity and comparison result.

From the repository root, with the documented dependencies available, supply
an output directory and the two local ROM paths for the exact Bag composition
stage. `BEFORE_ROM` is the image immediately before that stage and `AFTER_ROM`
is its output. The reader's protected-content checks require this stage pair.

```sh
python3 source/features/borsa-lotta/tools/compila.py --uscita "$BUILD_DIR"
python3 source/features/borsa-lotta/tools/rileggi.py \
  "$BEFORE_ROM" "$AFTER_ROM" --build "$BUILD_DIR" --json "$READBACK_JSON"
python3 -m unittest discover \
  -s source/features/borsa-lotta/test -p test_build.py
```

The compiler and reader produce the local payload and verification report.
An input from another composition stage requires the corresponding reader and
contract. Record command arguments in a sanitized form, tool versions, exit
codes, output hashes and the checked intervals in the public report.

The [Battle Party case](validation/party-source-rom-1.3.2.md) applies this
method beyond the Bag. It checks a final composed image, two overlay decoders,
physical contiguous move data, and native ARM equivalence using installed
bytes. Its counterexample catches a test that silently replaced ROM code with
a repository blob: verify the executable you intend to attribute before
running it, and retain that identity throughout the comparison.

The [native move-getter follow-up](validation/native-move-callers-1.3.2.md)
then explains native spans outside Party without rerunning the game. It verifies
caller branches, a native switch and a conditional type-icon lookup, while
separating ROM-to-ROM inheritance from an unperformed original-compiler rebuild.

The [resident ANIM v4 case](validation/anim-v4-source-rom-1.3.2.md) checks the
opposite situation: exact source/bytes can survive after their original roots
are retired. A lexical reference scan finds data dependencies and a false ISA
match; neither a matching payload nor retired hooks proves reclaimable space.

The [inherited camera case](validation/camera-source-rom-1.3.2.md) recovers a
project assembly recipe and separates unchanged instructions from two updated
pool pointers. Its invalid-ID counterexample shows why identical final output
is insufficient: check native normalization and assertions as well as ABI.

The [Summary hint case](validation/summary-hint-source-rom-1.3.2.md) covers a
machine-code recipe when the original surrounding compiler is unauthenticated.
It follows the installed function entry through resource gates, the replacement
and real return, keeping synthetic opening transitions separate from rendering.

The [Summary controls case](validation/summary-controls-source-rom-1.3.2.md)
checks an initially inert resident payload. It reconstructs current C with a
protected compiler, derives wrappers from final BLs, and demonstrates why an
OFF flag must be combined with ownership/lifetime conditions.

The [Rare Candy case](validation/candy-source-rom-1.3.2.md) connects a current
C rebuild to an inherited native tail. It catches metadata-only hook tests and
budget-exhaustion false returns, while preserving a retail-IT literal difference
and a separately rejected legacy expanded-Bag integration fixture.

### Verify the executable path

Follow callers, callbacks, dispatch tables, settings gates and fallbacks.
Document the calling convention, preserved registers, stack alignment and data
ownership across initialization, update and teardown. When dynamic evidence is
needed, identify the exact ROM, observer build, input route and measured sites.
Qualify an observer with an OFF/ON comparison and tests that reject mismatched
instructions, incomplete returns and exhausted buffers. Record the limits of
the exercised path, including unobserved conditions and asynchronous completion.

The [host qualification report](validation/development-host-1.3.2.md) contains
candidate-bound examples of dispatch, allocation, transfer and file-completion
observations. Use a new observation only when it resolves a stated question
that the existing raw records and static analysis cannot decide.

### State what each result proves

| Evidence | Supported conclusion |
| --- | --- |
| Authenticated source snapshot and build receipt | Provenance of the recorded build inputs |
| Matching rebuilt and installed bytes | Binary correspondence in the verified interval |
| Controlled execution or compiled-code equivalence tests | Behavior under the exercised inputs and assumptions |
| Observed caller, gate and lifetime | Activation and ownership in the recorded scenario |
| Missing original source or unmatched toolchain | An attribution gap with a named missing dependency |

For inherited native code, a decompilation at a pinned revision can explain a
routine. Verify its instructions, calling convention and data layout against
the actual image. A semantic correspondence supports a behavioral explanation.
Document the original-source provenance and binary-reconstruction status
separately. Record uncertain matches and the evidence needed to resolve them.

### Make each completed case reusable

A public case should include the component's purpose, input identities, source
and recipe links, address/offset mapping, independent checks, observed behavior,
negative cases, result and remaining gaps. Use relative repository paths and
portable arguments. Document required fixtures by their properties and hashes.
Keep personal paths, identifiers, save contents, credentials, extracted assets
and long binary/disassembly dumps outside the public report.

Preserve the scripts, tests and concise manifests that let a contributor with
the required local inputs reproduce the result. Run the repository's public-file
checks before a delivery. Source attribution, functional correctness and a
performance improvement each need evidence appropriate to their own claim.

The [expanded-Bag successor case](validation/bag-quantity-source-rom-1.3.2.md)
shows how to preserve a strict bench when a later owner changes a compiled core:
reconstruct both source recipes, compare the complete current owner and keep the
attribution artifact separate from installer builds. Derive the real resource
mapping before choosing native/extra slot boundaries for caller tests.


The [gift/pickup case](validation/gift-source-rom-1.3.2.md) demonstrates why an
exact code payload is insufficient for a source-to-behavior claim: a later
script producer can invalidate generated offset/fingerprint keys while the
owner stays byte-identical. Preserve that counterexample and distinguish the
native callback checkpoint from a complete parent return.

The [final Fairy-flags case](validation/fairy-flags-source-rom-1.3.2.md) adds compressed-overlay readback, a retained own-project ELF and a native combiner with another source owner. New immunity counterexamples show why a historical helper/loop proof cannot silently qualify a later composition.

The [full scalar case](validation/fairy-scalar-source-rom-1.3.2.md) extends that chain through actual Thumb→ARM division and an inline tail which returns through its parent frame. It reuses the verified ELF and separates inherited scalar equivalence from dense battle-policy agreement.

The [post-KO case](validation/postko-source-rom-1.3.2.md) follows its caller through wide best/narrow scratch and declared query models. A same-slot immunity mutant demonstrates why intermediate outputs and call order belong in the oracle.

The [Conversion2 case](validation/conversion2-source-rom-1.3.2.md) extends the method to a compiled replacement and native RNG state. It checks the complete row domain and rejects identical outputs when the seed write is missing.

The [Grounding case](validation/grounding-source-rom-1.3.2.md) follows pointer data through actual indexed reads and native damage arithmetic. It records inherited chart adoption separately and permits the compiler's legitimate reuse of an incoming damage word.

The [Wonder Guard case](validation/wonder-guard-source-rom-1.3.2.md) binds actual move records to two caller contracts. It distinguishes boolean zero/nonzero from canonical1 and uses a second state to reject an incomplete fix that passes the first positive.

The [Rage case](validation/rage-source-rom-1.3.2.md) reuses native leaf qualification to remove historical service models. It separates legitimate controller writes from the status-word invariant and binds a bitwise proof to actual mask/load/store instructions.

The [Transform transport case](validation/transform-transport-source-rom-1.3.2.md) follows a controller output word through native serialization and consumption. An exact-byte bridge replaces only the unqualified asynchronous delivery; identical final decisions do not excuse a wrong intermediate packet word.

The [Transform reload case](validation/transform-reload-source-rom-1.3.2.md) distinguishes an own-project assembly rebuild from an inherited native C build. Its equal-state/missing-query-guard counterexample and protected build-artifact outputs strengthen reproducibility without changing installed code.

The [U-turn case](validation/uturn-source-rom-1.3.2.md) reconstructs two artifacts but finds failed compatibility gates. Native getter execution exposes a callback that ignored corrupted arguments; native field writers show that a one-bit marker can alias legitimate signed data. Report attribution separately from correctness, preserve failed gates and record the exact controlled counterexamples.

The [native HP continuation](validation/hp-flinch-source-rom-1.3.2.md) extends a consumer fixture with its guest writer and intervening native script. Check every checkpoint and RNG transition, including a non-flinching move that still consumes RNG. An explicit continuation state qualifies that slice; earlier controller states and asynchronous transports remain separate links.

The [native snapshot producer](validation/uturn-producer-source-rom-1.3.2.md) replaces a semantic producer model with real handlers and variable-pointer lookup. Authenticate the full raw member, preserve the exact exercised insertion, disclose the synthetic stop and verify intermediate packing/lifetime independently of final output. Reusable VM domains preserve the preceding case's defaults.

The [AfterDamage continuation](validation/afterdamage-source-rom-1.3.2.md) replaces an explicit late state with native earlier states and their required scripts. Check summaries against first/last checkpoints and preserve the distinction between an effect request, execution of that effect script and observed turn behavior.

The [native flinch effect](validation/flinch-effect-source-rom-1.3.2.md) follows the request through real ability gates and a native target setter. A completed script can still set the wrong bit; check exact stores,unchanged status bits and another battler. Applying a status bit remains distinct from executing the next action consumer.

Native C correspondence in these cases uses the public
[HGSS source reference tree](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
pinned to `cb614ad23449d5852b40321dc409c4143872b35c`.
The [battle utility source](https://raw.githubusercontent.com/ctrl-cheeb-del/pokeheartgold/cb614ad23449d5852b40321dc409c4143872b35c/src/battle/battle_util.c)
was checked against the clean local reference by SHA-256;this is optional source
inspection,not a replacement for exact ROM identities or proof of the original
native compiler build. The executable verifiers use your ROM inputs directly.

The [native flinch-bit consumer](validation/flinch-consumer-source-rom-1.3.2.md)
preserves a guest-produced bit across an explicit actor-selection boundary,
then follows the actual caller and status loop into cancellation script15.
Keep command39 separate from execution of UpdateMoveHistory/ActionEnd;direct
no-bit status returns alone do not establish a successful normal move.

The [native action-end continuation](validation/action-end-source-rom-1.3.2.md)
checks the selected action row and index alongside the final controller value.
Checkpoint cancellation before native Init clears temporary state. Keep native
bulk-write bounds separate from host loader allowances,and count RNG calls even
inside neutral ability gates.

The [native next-action dispatch](validation/next-action-source-rom-1.3.2.md)
requires the selected handler's full return:an early command write can precede
attacker or target initialization. Verify both order arrays,exact stores and
real arithmetic;use a same-command stale-state counter to test the conclusion.

The [inert rematch module case](validation/rematch-source-rom-1.3.2.md) links
C/ASM and stage-specific configuration to exact overlay126/stub readback,
independent ELF mapping/relocation checks and native prefix/load/unload execution.
Its missing-unload counter preserves the reader output but leaks the registry;
its final-archive guard refuses a documented later trainer swap. Active variants
and natural context remain separate qualifications.

The [active rematch RAM continuation](validation/rematch-active-source-rom-1.3.2.md)
keeps the installed module inert while qualifying source gates, inline selection
and all108 native stores. A107-store counter retains identical output hashes,
showing why execution evidence needs precise store coverage as well as readback.

The [native rematch consumer](validation/rematch-consumer-source-rom-1.3.2.md)
continues the same CPU/RAM after unload126, checks native personality RNG and
IV division, all seven strategy exclusions and six opponent-level reads, then
stops before CreateMon. Separate record-pointer and level-cap counterproofs
show why buffer identity alone cannot qualify the consuming caller.

The [first rematch Pokémon case](validation/rematch-firstmon-source-rom-1.3.2.md)
continues through native construction and actual PartyAdd return. It checks
independent decrypted fields against raw resources, SDK model ABI/lifetime and
sparse code/data admission. Stage comparison identifies the fifty-byte owned
post-form repair; a skipped zero-item setter demonstrates identical final output
with a missing call link. The name-string model correction affects only the bench.

The [complete rematch constructor](validation/rematch-complete-source-rom-1.3.2.md)
closes the six-member loop, persistent PID state, exact capsule slices, native
seed restoration and original allocation lifetime. Identical-party missing-free
and wrong-restore controls show why the return boundary needs its own proof.
SDK filesystem internals remain modeled, separate from native game execution.

The [void SDK return case](validation/sdk-void-return-source-rom-1.3.2.md)
separates modeled results from caller dependence. Follow actual return edges,
check read/modify/write before a kill and confirm the instruction executed.
A nonmutating observer must preserve preceding receipts; poison comparisons
may mask only unspecified return-log fields, with a known-live read calibration.

The [positive trainer-strategy hook](validation/trainer-strategy-source-rom-1.3.2.md)
checks sequential calls on the same buffer, so a once-only transformation cannot
pass by resetting its source between slots. A late invalid delta must change
only the local copy; a preapplied same-output buffer cannot prove this call
performed the edit. Require the complete helper chain and actual instruction
boundaries, including the width of the following native BL.

The [trainer21 move consumer](validation/strategy-move-consumer-source-rom-1.3.2.md)
records every host initialization when a copied fixture bridges two qualified
boundaries. Keep the source identity and hybrid limitation visible even if the
same CPU retains the real edited buffer. Compare all decrypted bytes as well
as decoded fields, and calibrate call coverage with an identical-output skip.

The [native trainer21 constructor](validation/strategy-constructor-source-rom-1.3.2.md)
removes a copied-Mon boundary by retaining one constructor API execution through
return. Keep the subsequent seed getter separate from the restore store. Compare
the current component against declared installer-preimage RAM BLs to isolate its
contribution across complete packets, including fields outside a short decoder.
Replay can then validate proofs and false receipts without repeating CPU work;
it preserves the capture's original source identity.

The [trainer31 extension](validation/strategy-31-source-rom-1.3.2.md) keeps a
finite authenticated profile and the trainer21 default. Verify a refactor
against an entire prior producer receipt before extending it. A move duplicated
in another party member provides a counterproof against overbroad attribution;
check both packets, including valid-checksum wrong replacements.

The [trainer32 case](validation/strategy-32-source-rom-1.3.2.md) moves the target
to another party position. Keep target selection separate from a historical
counter name, and require the exact packet count and width before zipped byte
comparisons. Missing or equal short packets are useful comparator calibrations;
they do not replace the full source-semantic oracle.

The [trainer33 case](validation/strategy-33-source-rom-1.3.2.md) groups multiple
edits within each packet and qualifies a new PID branch from source and raw
instructions before execution. Check count-valued returns as counts; expose
intermediate stores when final state alone cannot distinguish the operations.
Keep per-edit counterproofs and unchanged non-target packets separate.

The [trainer34 case](validation/strategy-34-source-rom-1.3.2.md) requires each
new profile-specific instruction in both the decoded map and the executed-PC
receipt. Removing an executed PC is a different falsifier from changing its
ROM bytes. Keep actual capture provenance when strengthening replay guards.

The [trainer244 case](validation/strategy-244-source-rom-1.3.2.md) proves a
resource's absence through raw IDs, native early-return instructions and BOOL
results, empty setter/service ledgers and zero output fields. Summaries must
follow actual accesses. Replace no-op empty-list mutants with injected events
when an empty list is the correct result.

The [trainer245 case](validation/strategy-245-source-rom-1.3.2.md) changes a
move while retaining PP. Compare the actual value and native call arguments;
an unchanged related field can hide a wrong assignment. Separate source/raw
learnset inference from observed RAM and admit only new instruction starts
while requiring all profile-specific execution obligations.

The [packed trainer-name case](validation/trainer-name-source-rom-1.3.2.md)
shows why decoded text is a different fixture from native packed String words.
It combines two independent decoders with native CopyN/CopyTo, ARM memcpy and
a bounded quiescent assertion path; outer message loading remains explicit.

The [trainer preparation case](validation/trainer-preparation-source-rom-1.3.2.md)
follows a caller to a nested constructor entry, keeping20B raw-header writes
separate from52B native structure copies and preserving stack-derived bytes.
Its endpoint does not imply caller return or completed resource lifetime.

The [complete trainer caller](validation/trainer-caller-source-rom-1.3.2.md)
composes preparation, constructor and suffix in one CPU/RAM context. Reuse the
actual service backends as well as observers; preserve nested incoming registers,
separate outer APIs from nested returns and restore observer stack scope on every
exit. Equal output does not prove an unchanged-value store or resource teardown.
Authenticate bounded adapters, calibrate CPU code-hook granularity with synthetic
instructions and require replay to retain every claimed helper/resource proof.

The [native message case](validation/trainer-message-source-rom-1.3.2.md)
removes the high-level producer model in a finite standalone chain. Supply
encrypted archive slices at the lowest declared I/O boundary and let native
instructions create object fields, decrypt and copy. Verify the entire ordered
write transcript, including stack stores and untouched spare content; match
allocation lifetime at each API return. A counterproof must exercise its named
mutation and fail at the predicted stage. Separate source/byte identity,
finite API execution and original compiler reconstruction; standalone API
proofs do not automatically compose into a previously tested caller.

The [native-message caller composition](validation/trainer-message-caller-source-rom-1.3.2.md)
performs that next step without context handoff. Authenticate the effective
stub table after adapter changes, inspect live code after SDK setup and route
shared helper APIs by their owner stage. Bind nested stack origins without
resetting guest registers; prove live and freed objects survive the constructor
unchanged. Reuse existing pure guards through complete-function AST checks,
including wrappers/signatures, while giving new caller contexts their own
oracle. OFF comparisons must preserve semantic endpoints and declared scratch
scope; a raw whole-RAM digest is not an ownership or difference-localization proof.

The [species-name producer](validation/species-name-source-rom-1.3.2.md)
reuses the message SDK models through an authenticated finite profile, changing
fixture IDs, heap and bank expectations without changing native code. Derive
those parameters from the actual caller: heap0/bank237 differ from trainer
messages. Compare returned object bytes and ownership, distinguish unused spare
from payload, and keep historical header keys separate from current assumptions.
Audit OS high-water RSS with explicit platform units; a polling sample can miss
a short peak. Split image batches and collect completed sandbox cycles before
claiming bounded resource use. A standalone producer proof does not imply its
native composition in an earlier constructor campaign.

The [native species-name composition](validation/species-name-caller-source-rom-1.3.2.md)
removes the high-level name boundary inside the complete trainer caller. Separate
SDK ownership before dispatch, not by filtering a combined trace: the inherited
constructor observer would otherwise create a phantom allocation. Derive nested
stack origins and nickname blocks from source and PID; check canaries before
allocator reuse and freeze the precise union of owned generations. A completed
same-party leak falsifier must still retain all six name chains, exact remaining
SDK dispatch and the source-derived global instruction delta. Truncated evidence
must fail independently of the expected leak rejection.

The [native NARC parser](validation/native-narc-reader-source-rom-1.3.2.md)
lowers a direct member-copy boundary to whole-file cursor services. Derive the
member offset and length in native code, then bind every seek/read to raw FAT/FNT/
NARC evidence. Follow each revision's actual literal/table/path pointers before
classifying regional data differences. A modeled opaque file does not establish
native SDK structure layout; do not fabricate fields to reconcile a different
reference sizeof. Require closure even when payload and whole RAM are identical,
and bind counter return ISA/context as strictly as positive paths. A partial IO
return ignored by native code is an observed contract limit, not a safe refusal.

The [native header caller composition](validation/native-header-caller-source-rom-1.3.2.md)
shows how one installed address can have separate modeled and native roles in
a controlled harness. Remove its installation stub in an isolated namespace,
then preserve each remaining original backend exactly once under its owner.
Bind every dispatch to actual arguments, event position and return. Snapshot a
borrowed frame at its real return before later code reuses it. Contextualize
standalone constants such as seed and destination preimage: an unchanged
algorithm does not make those inputs universal. Derive prefix checkpoints from
qualified instructions and branch conditions before using them as counterproofs.

The [native party-reader caller case](validation/native-party-caller-source-rom-1.3.2.md)
composes a second native role at the same entry before its former callback can
run. Preserve actual preexisting stack bytes rather than synthesizing a uniform
frame. Derive volatile residues from the selected source/raw path and bind the
real return through wrapper and unload. Compare transport and lifetime even
when a prezeroed destination makes a short read indistinguishable by payload.
Observer-side canaries and counters need explicit OFF/ON treatment: project only
source-proven writes, and keep semantic CPU/resource evidence separate from
optional observer logs.

The [personal-data/EXP case](validation/native-personal-caller-source-rom-1.3.2.md)
extends a qualified reader through its first real data consumer. Keep getter
IDs separate from field offsets, and derive volatile residues again when
replacing a model with native code. Link recorded lookup registers to the actual
table/offset/value; metadata equality alone is insufficient. Check the full
before/after vector of a single instruction whose only effect is a field load,
then bound a counter to one later register change. Predict the resulting packet
by changing the source-derived plaintext field and recomputing encryption and
checksum. Preserve evidence predating that change; exclude later whole-RAM scope
hashes only where the predicted state difference makes equality inappropriate.

The [native growth-table case](validation/native-growth-caller-source-rom-1.3.2.md)
shows why a direct call needs a fresh ABI derivation even when it reaches the
same entry as a previously qualified tail. Keep caller curve selection separate
from a reader member argument. A register-only counter must preserve the actual
baseline RAM and stack preimage, including untouched bytes. When an observer
poisons a freed buffer only while ON, bind the difference to the exact free and
allocation history and compare only a precise source-proven projection; retain
all other phase memory and consumer evidence.

The [initial friendship case](validation/native-friendship-caller-source-rom-1.3.2.md)
adds a lifetime counterexample: a native initial value changes, while an owned
Plus patch restores the same final party. Reproduce the50-byte recipe emission,
distinct setter frames and six actual intermediate/final packet checkpoints;
a final-output match alone cannot attribute the earlier path.

The [custom-PP stack-buffer case](validation/native-pp-caller-source-rom-1.3.2.md)
shows why identical resource IDs do not identify the same caller. Bind the
actual API/lifetime and derive its frame before changing a budget. Protect
saved caller words immediately above borrowed output, and record guard bytes
before and after. Keep raw-input expectations separate from a counter's
predicted result so that earlier model reads still verify the original bytes.

The [native SDK Init case](validation/native-fs-init-source-rom-1.3.2.md) adds a
compiled ABI check against original headers: a stale size comment is not a
layout measurement. A recovered assembly recipe can match installed bytes
while a modern C emission differs in register allocation and store order.
Attribute those results separately. Require selective writes, preserved bytes
and interworking in the actual caller; a code hook or unchanged final party
alone does not prove that an initialization store executed.

The [native Open wrapper](validation/native-fs-open-source-rom-1.3.2.md) adds
aggregate ABI and conditional-instruction checks. Distinguish an eight-byte
structure passed by value from a pointer argument,and native PUSH effects
from a model's output write. Derive a new guard from the actual frame extent.
Qualify conditional code-hook delivery separately from instruction effects;
a false return with unchanged final output can still disprove attribution of
the expected boolean path.


The [native Convert extension](validation/native-fs-convert-source-rom-1.3.2.md)
distinguishes two invocations of the same Init by object, frame, lifetime and
return ISA. Repeated starts increase hook counts without increasing unique
locations. A new guard may include host readonly bytes beyond the guest bound;
keep those bytes outside the unchanged final mask and bind their actual
preimage through completion. Check saved volatile registers explicitly:
Convert restores R3 even when its lower model clobbers it. A one-word local
mutation may change phase hashes while leaving final RAM and party identical.


The [native Fast extension](validation/native-fs-fast-source-rom-1.3.2.md)
checks stack reuse at separate lifetimes. An earlier directory checkpoint can
remain correct while a later callee overwrites its dead tail with spilled
aggregate arguments. Reconstruct the later frame from actual native writes
rather than extending an earlier object's lifetime. Preserve the distinction
between newly executed guest field stores and modeled host archive state;
a successful command model does not establish native queue/card/error state.


The [native Close extension](validation/native-fs-close-source-rom-1.3.2.md)
follows residual return state through POP-to-PC interworking. Restoring PC does
not restore LR; a callee's CMP may also replace the backend flag policy. Track
those differences until the actual caller overwrites them. Distinguish two
calls to the same dispatcher by command, frame and lifetime. An idempotent
store needs an instruction/store witness even when its before/after bytes agree.


The [native Seek extension](validation/native-fs-seek-source-rom-1.3.2.md)
attributes required state before replacing a backend. Tie physical FAT coordinates
to typed properties and label a partial model as a projection, including known
excluded effects. Derive the host cursor from the actual guest store. Couple
native and modeled writes through complete frame snapshots without a new mask.
Record incoming volatile flags when the first instruction overwrites them;
require all later flags and actual source bridges between snapshots. Equal
position/output can still conceal a different seek origin and instruction path.

The [Read veneer/core case](validation/native-fs-read-source-rom-1.3.2.md) derives entry inputs from authenticated parent records, reconstructs pre-copy frames and separates isolated native execution from full SDK completion and parent integration.

The [Wait/IRQ case](validation/native-fs-wait-source-rom-1.3.2.md) replaces a BOOL boundary with native control-state execution after a declared completion-field projection. It checks CPSR I/F/mode/flags and records the actual Unicorn model separately from ARM9 hardware.

The [complete Read/Wait caller integration](validation/native-fs-read-caller-source-rom-1.3.2.md) checks chronological native/model writes and source-derived full-register bridges. Bind overlapping output/frame predictions before composing a page witness; otherwise a payload copy can conceal an incorrect frame prediction. Preserve full raw pairs for an independent check of a producer’s outside-page assertion.

The [Find wrapper case](validation/native-fs-find-source-rom-1.3.2.md) separates initialized bytes from BSS state and compares instruction bytes separately from a changed literal pool. Source-definition hashing must skip forward declarations. A prepare-only CLI mode must reject concurrent CPU modes before creating outputs or starting a collector.

The [complete Find caller case](validation/native-fs-find-caller-source-rom-1.3.2.md) initializes a declared BSS fixture once before all APIs, binds read-only fences to actual register contexts and checks a matched final RAM pair. A larger owned frame can already fit an existing projection: derive the new guard without enlarging a mask. Keep capture and later oracle identities separate; strict JSON comparisons reject Python bool/int/float aliases, and repeated oracle evaluation must not append composition receipts.

The [Send case](validation/native-fs-send-source-rom-1.3.2.md) shows why a new native callee can exceed a previously qualified caller frame. Attribute the isolated path with explicit archive/queue state, check source-reconstructible whole RAM without a mask, and preserve the distinction between queue preparation and completion. Authenticate copied caller inputs against their original source revision before using them.

The [ExecuteSync case](validation/native-fs-exec-sync-source-rom-1.3.2.md) separates native wrapper stores from modeled field projections. Poison a void return and inject a declared postcondition fault to establish which stored field actually controls the native BOOL; retain the distinction between this fault and a naturally observed SDK error.

The [Release case](validation/native-fs-release-source-rom-1.3.2.md) distinguishes an idempotent native store from an assignment proved by a declared mismatched old field. Preserve the actual ABI and baseline fixture, record the initial projection separately, and verify both final convergence and the native store preimage. A void residual register is not an application result.

The [empty Wakeup case](validation/native-os-wakeup-source-rom-1.3.2.md) adds prospective earlier-field invariants, aggregate-layout assertions and literal whole-CPU-image grouping. Keep the field comparator separate from native activation proof: a no-op can satisfy unchanged-memory invariants. Original compiler provenance and modern header-layout compatibility are separate conclusions.

The [Release/Wakeup composition](validation/native-fs-release-wakeup-source-rom-1.3.2.md) checks actual nested entry and return in one CPU. A same-code bypass may preserve every earlier caller-output invariant while missing native instructions and stack writes; absolute whole-RAM checks still include code.

The [empty Next case](validation/native-fs-next-source-rom-1.3.2.md) preserves an observed checkpoint through the original bridge, verifies a reconstructed parent whole image before adding code, and labels bytes outside separately observed spans. A source-valid inactive branch can converge on identical final whole RAM while skipping a conditional native store; preserve its trace and flags, including immediate-rotation carry.

The [ExecuteSync join](validation/native-fs-exec-sync-join-source-rom-1.3.2.md)
preserves the real callee's volatile registers while consuming a stored error and
restoring a saved register/PC pair. Reuse the qualified ELF for unchanged bytes,
bind guard metadata to actual RAM, and compare literal images before grouping.
The same NULL CPU input can return different BOOLs because the native read sees
different stored errors; final flags still reflect CMP before conditional MOV.

The [continuous ExecuteSync case](validation/native-fs-exec-sync-native-callees-source-rom-1.3.2.md)
joins the wrapper and qualified native callees in one CPU. Include external
model policy in literal-input grouping: equal CPU/RAM can have different callee
interactions. Freeze historical checkpoint windows before the new guest, label
derived whole-image identity and extra filled bytes, and test a same-code
bypass whose public output converges while native work and dead-stack bytes differ.

The [complete Send context](validation/native-fs-send-native-callees-source-rom-1.3.2.md)
starts from an observed before-image digest and lets native preparation reach
the earlier callee checkpoints. Preserve predecessor guard bytes until PUSH
overwrites them. A coherent alternate dead preimage can pass a source oracle
and converge in output while still failing exact-input provenance. Label the
final saved-register POP prediction as derived until the new guest observes it.

The [native Translate case](validation/native-fs-translate-source-rom-1.3.2.md)
separates396 instruction bytes from a literal pool and initialized dispatch table.
Retail Italian relocates the table despite identical instructions. Compare
explicitly limited old-model fields separately from new native R1/LR/saved24.
An early host error write can disappear from every final CPU/RAM field; the
actual native STR preimage, rather than output equality or instruction counts,
identifies the writer.

The [combined Send/Translate case](validation/native-fs-send-translate-native-source-rom-1.3.2.md)
shows how previously observed isolated whole-RAM hashes can become strong
boundary anchors in a longer guest. Derive initial RAM forward, prove code/data
overlays commute with the native prefix, and compare complete fields without
carrying over obsolete model masks. Matching boundaries or final outputs alone
still does not establish the writer: retain native store preimages and an
explicit same-code early-write control.

The [default FindPath prefix](validation/native-fs-default-findpath-source-rom-1.3.2.md)
shows how to remove the residual model for a finite prefix while preserving
each deeper byte's provenance. Differentiate captured windows from newly
exposed bytes derived from the authenticated whole ancestor. Freeze the actual
input only when no prior native output exists; use separate source/guest
checks for activation. A deliberate pre-PUSH host write can preserve every
final output while changing all native store preimages. A distinct lower-fill
control checks uninitialized-stack independence without normalizing RAM hashes.

The [nested SEEKDIR case](validation/native-fs-nested-seekdir-source-rom-1.3.2.md)
shows why a counterexample that changes input needs its own provenance verdict.
An identical final CPU/RAM state does not make the projected entry an actual
parent observation. Reject that mismatch at the specific captured field and
attest the derivative separately. Compare native temporal contexts, reads and
store preimages even when final hashes and counts agree. Authenticate a
reconstructed whole AFTER image before adding a new code gate or extending
the guard window.

The [Reset C compilation experiment](validation/native-reset-c-codegen-source-rom-1.3.2.md)
shows the next distinction: identical complete source can be compiled with an
authenticated alternative toolchain without reconstructing original Metrowerks
bytes. Its ELF/readback and ABI checks preceded three passing guest cells. It uses the same
required native resources and retained original raw, with an explicit semantic
projection only after each build's own full-trace verification. The compiled caller
passes the scoped semantic comparison; its C object is not installed in a ROM.

The [pivot/Shell Bell order check](validation/uturn-shellbell-order-source-rom-1.3.2.md)
shows a practical stopping criterion: a suspected consequence of a known field
collision does not follow when the relevant item command precedes the snapshot
and later clear. Compare source macros, complete native dispatch and actual
script boundaries before adding a probe. Inline comments must not shift command
IDs, and numeric equality across opcode/subscript/item namespaces is not a link.
A static counterproof can prevent a needless guest campaign; it cannot certify
an unexecuted heal or another consumer's lifetime.

The [ordinary Shell Bell reader](validation/ordinary-shellbell-source-rom-1.3.2.md)
adds a contrasting lifetime question: native controller37 can follow AfterDamage,
but source order alone does not establish neutral intermediate scripts or a
successful input boundary. Resolve the real dispatch BL and itemID/member mapping;
keep the consumer switch table and pool outside instruction ranges. A full-HP
ancestor fixture is a legitimate negative case rather than a positive healing test.

The same reader's `--include-neutral` dependency view separates a held-item
function from its following function and selects only the effect0/88 default
route. A negative script result can still write scratch state or advance RNG.
Preserve these effects when composing caller proofs; per-API stack/register
reinitialization must not be described as a continuous native dispatcher.

The [owned dispatch driver](validation/ordinary-shellbell-source-rom-1.3.2.md#owned-continuous-dispatcher-qualification)
qualifies a continuous Thumb callback loop separately from game behavior. Its
single compiled object, raw ELF readback and source forecasts precede two owned
ON/OFF cells. Mapping symbols distinguish code, literal and handlers; a typed
raw envelope binds the initial state and backend as well as every observed field.
An owned pass does not admit original callbacks or establish their activation.
