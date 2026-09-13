# The runtime test bench

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
that exact commit before touching anything and is idempotent on an already-instrumented tree.

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

`MELONDS_SOURCE` accepts any pinned checkout. Set `CMAKE_MAKE_PROGRAM` if Ninja is not on
`PATH`. Choose an empty output directory when rerunning; the build writes everything under
`work/`.

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
per-frame watches, named captures and SRAM export. The public scripts contain only input, waits,
reads, status and local exports: no RAM writes, no cheats, no freezes, no savestate loads.

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
| `frames.csv` | one row per guest frame: frame number, `arm9_pc`/`arm7_pc` end-of-frame samples, the game's vblank counter, observation counters, and any address the script asked to watch |
| `commands.log` | the commands actually executed, in order, with their frame |
| `stdout.log` | everything the harness printed, including the answers to `read` and `status` |
| `session.txt` | the run's configuration: core, settings, ROM path, script, frame budget |
| `latest.ppm` plus the captures the script named | frame captures |

Two cautions that have already cost time here: `arm9_pc` is an end-of-frame *sample*, not a
visit count; and harness counters accumulate across state restores, so a run that reloads a
state cannot be compared to one that does not.

---

## 4. The automatic gates

They live in `source/verifiche/` and are meant to be used as exit-code gates, not read by eye.

### `rileva_crash.py` — is the game alive?

```sh
python3 source/verifiche/rileva_crash.py runs/<name>/frames.csv [...]
```

Exits 1 if at least one run is in a crash.

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
