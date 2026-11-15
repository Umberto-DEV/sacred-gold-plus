# Native ExecuteSync: source, bytes and the stored-error result

This follows [native Send](native-fs-send-source-rom-1.3.2.md) into its remaining
ExecuteSync boundary. The finite question is whether the installed wrapper passes
the actual command/result/archive to Translate, Release and Next, and returns a
BOOL from the file's error **after Release**. Those three callees remain explicit,
incomplete models. No game, ROM, save, ABI, identifier or default changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate native wrapper instructions from modeled completion fields. Reconstruct
source/recipe→ELF→ROM and ROM→caller→ABI→source independently. A Translate success
followed by an injected stored error can falsify the claim that the API simply
returns Translate's result. Poison the undefined return of void Release, inspect
all registers and exact RAM, and require independent review of the raw evidence.
A successful wrapper return cannot establish completed directory resolution.

## Il materiale più grezzo da cui partire

Use the eight exact inputs, sizes and SHA-256 values listed in the
[Send input table](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
EN and inherited/localized IT are IPKE revision0; retail IT is IPKI revision0.
ARM9 file offset is`0x4000`, load`0x02000000`, entry`0x02000800`. Older compressed
images require section decoding, not subtraction of the load address alone.

`FSi_ExecuteSyncCommand` occupies`[0x020D7744,0x020D7788)`:68 bytes,17 ARM starts,
no literal pool, current physical offset`0x000DB744`, uncompressed main ARM9.
No overlay or autoload lifetime is introduced. Entire body SHA-256:
`44b2f23b47f01552bd478420b9a14ae0fc2ed6013e7d551d5112075264a43d55`.
All eight retail/base1.1/V4/current images match. It is retained native HGSS code.
The following Send prologue is outside this body.

Source counterpart:
`lib/NitroSDK/src/fs/FS_archive_prefix.c::FSi_ExecuteSyncCommand` in the
[pinned reference](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
File SHA-256`d359268374ed97b359e4344a820c892382fd23f8923d2895a828175662ae3f2d`;
definition SHA-256`9edfebc8b0b6fdb346ed1d348c6db3eb6d0484332f4ea2c885d59f5817766799`.
The inlined `file.h::FS_IsSucceeded` definition has SHA-256
`d0750073e8e967e089376bacd26c528ffaa514f208d1f7bc81a9e888719b1003`.
It tests `file->error == FS_RESULT_SUCCESS`, where success is0.

The [recovered assembly](../../features/trainer-strategy/sorgenti/fs-exec-sync.S)
is an attribution recipe, with no installer. Original MW compiler/objects remain
missing. Authenticated Clang21 targets ARMv5TE/ARM946E-S/ARM mode. Its receipt
records executable hash/version, flags, argv, exit codes, source definitions,
18 original headers and ARM32 layout assertions: FSFile72, FSArchive92,
link8 and queue8. Recovered object SHA-256:
`768a6e34e5cf2ce6535446110482f27edf3c39c3bd3105956c8037e5049bd011`.
Independent ELF text extraction rejects relocations; physical ROM and ndspy
section decoding must agree with all68 bytes.

| Native call | Target | Actual selected arguments |
| --- | --- | --- |
| BL`0x020D7750` | Translate`0x020D68C0` | R0=file, R1=command4 |
| BL`0x020D775C` | Release`0x020D6864` | R0=file, R1=Translate's actual result |
| BL`0x020D7764` | Next`0x020D749C` | R0=file.arc |
| BL`0x020D7770` | Async`0x020D76B0` | excluded when Next returns NULL |

The selected input comes from the actual isolated Send service entry, not its
pre-Send fixture. Copy `services[0].entry`, `services[0].frame_before` (304 bytes),
`services[0].archive_before` (92 bytes)
and the last8 preserved guard bytes, producing frame312. TOP is`0x023BEEC0`,
file`0x023BEDD0`, archive`0x021E3654`, SP=TOP−304, frame=TOP−312. File fields are
prev0/next4/arc8/stat12/command16/error20/queue24/prop32/arg48; archive flag28,
list.next36/proc84/proc_flag88. Incoming file is linked, stat`0x45`, command4,
errorBUSY2; archive flag`0x13` and list.next=file. This archive originated as a
declared no-ACTIVATE fixture, **not natural boot state**.

Native PUSH saves only R4/LR:8 extra bytes. The hypothetical complete caller
peak632 exceeds its old608-byte ownership bound. This is isolated coverage;
no fullcaller guard or RAM projection has been enlarged.

## I metodi e gli strumenti da usare

### Rebuild and independent readback

Use Python3, ndspy, Capstone and Clang with ARM support. Keep a clean reference
checkout at the pinned commit. Inputs and outputs below are developer-supplied
local paths; output directories must be fresh and outside `source/`.

```sh
python3 source/features/trainer-strategy/tools/compila_fs_exec_sync.py \
  --uscita "$SGP_EXEC_RECIPE" --cc "$SGP_CLANG" --reference "$SGP_HGSS_REFERENCE"
python3 source/features/trainer-strategy/tools/rileggi_fs_exec_sync.py \
  --retail "$SGP_RETAIL" --base "$SGP_BASE11" --v4 "$SGP_V4" \
  --rom "$SGP_ROM" --language EN --recipe-dir "$SGP_EXEC_RECIPE" \
  --json "$SGP_OUT/exec-lineage-EN.json"
SGP_FS_EXEC_SYNC_RECIPE_DIR="$SGP_EXEC_RECIPE" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_exec_sync_recipe.py' -v
```

Repeat readback for IT with its four exact inputs. The recipe test checks all17
starts and four direct calls. Readback/build need no emulator or complete ROM
build. Keep commands, exit codes, hashes, source snapshots and logs privately.
One producer at a time;180s/command,1GiB peak RSS,2MiB logs,16MiB case outputs,
1GiB disk peak and at least10GiB free after peak.

### Source path and declared model boundaries

Translate returns FSResult0 or1 and projects only `file.error=result`, a selected
synchronous postcondition. It excludes default FindPath/ID delivery, properties,
ARG, archive IS_SYNC transients, IRQ, threads and card work.

Release receives the actual translated result in R1. Its model unlinks
archive.list.next and file.prev/next, clears stat bits`0x4F`, and writes error
from that result. **Command4 is preserved**; this is not the older command0
completion projection. Five host word writes are recorded, including idempotent
ones. IRQ and wakeup are excluded. Release is void; its R0 is deliberately0,
file or`0xFFFFFFFF` in separate controls.

Next receives archive after the native LDR. The selected empty-list model clears
RUNNING`0x10` (flag`0x13`→3) and returns NULL. It excludes native Next, IDLE
callbacks, suspend/cancel, IRQ and asynchronous dispatch. The three models make
seven host word writes, separate from two native PUSH stores.

A declared `release_error_fault` deliberately writes error1 although Translate
returns0 and Release receives R1=0. It violates the ordinary Release model's
postcondition; it is **fault injection, not a natural SDK failure**. The native
wrapper must still return BOOL0, falsifying the explanation “return Translate”.
Ordinary Translate failure1 is a separate control. Each changes only error20 in
the final frame (offset92, one changed byte for0→1), so their whole RAM differs.

### Authenticated isolated execution

First reproduce the linked Send and Find-caller reports with your own inputs.
The CLI authenticates all24 Send cells, exact policy grid,69 ancestor source
identities, original Find-caller proof/objects/recipes, OFF and counters without
executing their guests again. Historical Find-caller captures require their
retained source with `--parent-source`, as explained in the Send guide. Current
matching captures may omit it.

```sh
python3 source/features/trainer-strategy/tools/attribuisci_fs_exec_sync.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_SEND_REPORT" \
  --find-parent-report "$SGP_FIND_CALLER_REPORT" \
  --parent-source "$SGP_PARENT_CAPTURE_SOURCE" --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --find-recipe "$SGP_FIND_RECIPE" \
  --send-recipe "$SGP_SEND_RECIPE" --recipe-dir "$SGP_EXEC_RECIPE" \
  --prepare-only --json "$SGP_OUT/exec-prepared-EN.json.gz"
```

Prepare-only executes no guest and is mutually exclusive with probe. For the
first one-cell probe replace `--prepare-only` with
`--probe --raw-dir "$SGP_OUT/exec-probe-raw"` and choose a fresh report filename.
For the complete32-cell language matrix omit `--prepare-only`, add
`--raw-dir "$SGP_OUT/exec-raw-EN"` and choose another fresh report. Repeat for IT.
Unicorn2.1.4/model17 is Cortex-A15: only admitted instruction semantics are
qualified, not ARM946 silicon, timing or interrupt delivery.

Raw records, faults and halted registers are saved before source evaluation.
The native collector whitelists instruction width/live bytes and exact read/write
owners. The source oracle predicts all16 register vectors, reads, stores and
model preimages independently. The entire4MiB image is reconstructed from fill,
actual frame312, archive92, native68 bytes, original stopped Send POP fetch and
three own model NOP gates. Source-derived final-image hashes must match actual
CPU RAM readback with no exclusion. OFF omits native transcripts but must preserve
all functional registers, model records and whole RAM exactly, with0 projection.

Normal returns BOOL1/CPSR`0x6000001F`; error1 returns BOOL0/CPSR`0x2000001F`.
Native POP restores incoming R4 and SP, returning to original Send`0x020D7928`;
LR remains`0x020D7768`. R3 clobber persists because it was not pushed. This differs
from Send, whose larger PUSH/POP restored R3. Void Release R0 changes context
`0x020D7760` only; the archive LDR makes contexts converge before`0x020D7764`.
Final CMP overwrites clobbered NZCV.

### CPU-free replay

Portable tests need no ROM. Private replay requires a JSON config object with
EN and IT keys. Each value has `report`, `raw_dir` and `prepare`; `prepare` holds
these keyword arguments, mapping CLI hyphens to underscores:
`rom`, `language`, `parent_report`, `find_parent_report`, `capture_source`,
`objects`, `strategy_object`, `read_recipe`, `wait_recipe`, `find_recipe`,
`send_recipe`, `recipe_dir`. All are local path strings except language and an
optional null capture_source. Report and raw_dir name each final matrix and its
32 numbered gzip records. Do not publish this machine-specific config.

```sh
SGP_FS_EXEC_SYNC_REPLAY_CONFIG="$SGP_EXEC_REPLAY_CONFIG" \
SGP_FS_EXEC_SYNC_RECIPE_DIR="$SGP_EXEC_RECIPE" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_exec_sync*.py' -v
```

Absent private inputs produce explicit skips; complete qualification requires
zero skips. Replay checks74 runtime source identities, reconstructed parent
proofs, exact32-cell grids, raw/report equality, full CPU/RAM evidence and strict
types. It falsifies return/LR/R3/flags/flow, native and model writes, preimages,
guards, hashes and bool/float aliases. A counter disguised with normal policy
and model metadata must be rejected using its actual native return.

### Results and limits

Byte correspondence is established for all eight inputs and the recovered ELF.
The final64 isolated runs cover four actual parent fixtures per language and
eight policies: normal, OFF, Translate failure1, declared Release-error fault,
void R0 all-ones/file, volatile clobber and fill39. EN takes5.340s with647413760-byte
OS peak RSS; IT5.529s with660783104 bytes, including authenticated preparation.
The56 ON runs each expose16 native contexts, two stores, five reads, three model
calls and20 steps including the original return fetch. Eight OFF runs preserve
exact registers/model records/whole RAM with no projection. The eight Release
faults preserve Translate success and Release argument0, change only final frame
error byte92 and return0 instead of1. Positive metadata disguises are rejected
with `ExecuteSync source-derived returned`.

Void and clobber controls preserve whole RAM; fill39 preserves owned frame and
archive outputs while changing the declared unowned image. Final flags follow
the stored error, and R3 clobber persists. Source semantics remain finite:
NextNULL, three incomplete projections, I0 and isolated Send fixtures. The Async
call and complete native callees are not exercised.

Independent pure review found that an early counter-pair helper accepted a valid
counter built with a different initial fill or pre-PUSH bytes. Two RED tests
reproduced that omission; the helper now requires identical fixture, entry,
initial RAM hash, fill, observation mode and baseline policy except the declared
fault, plus the single final error-byte delta. Only `counter_rejection` changed
in the CLI AST; all remaining module AST and the other73 runtime source hashes
are unchanged. The original probe source/raw remain retained. No guest was
repeated for this verifier correction, made before both final matrices.

Sixteen tests pass with zero skips: eleven portable and five requiring private
objects/reports,7.131s/838516736-byte OS peak RSS. One negative test initially
replaced an already-zero archive byte with zero; it now flips a bit, and every
mutant must first prove it changes the typed receipt. Only the test changed;
no guest campaign was repeated. Source, recipe, collector/preparation, probe and
matrix evidence receive independent review against raw materials.

| Conclusion | Scope |
| --- | --- |
| Documented provenance | pinned native source, inline success test, original headers/layout, authenticated Send inputs |
| Recovered binary match |68-byte recovered assembly/ELF, eight decoded and current physical readbacks; original MW build missing |
| Finite source semantics | actual wrapper ABI, stored-error BOOL and explicit callee projections |
| Observed activation |64 isolated calls from eight authenticated Send fixtures; no complete caller or natural filesystem completion |
| Unattributed links | native Translate/Release/Next/Async, directory resolution/ID delivery, natural archive/full caller/completion |

No game resource recovery or speedup is claimed. SAVE/cold restart, physical
hardware, natural execution and the older independent physical requirements
remain pending. The next attribution should remove one concrete modeled callee
boundary, starting from its actual ABI/preimage rather than assumed completion.

The following [Release attribution](native-fs-release-source-rom-1.3.2.md) uses this case’s actual Release entry/preimage, including translated result0/1 and the explicit modeled-Translate provenance.

A later [independent frozen-contract comparison](native-fs-release-source-rom-1.3.2.md#independent-comparison-with-the-earlier-frozen-contract) checks the retained Release projection against native field/frame records while preserving this case's original modeled scope and explicit ABI differences.
