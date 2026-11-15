# Native SendCommand: source, bytes and finite idle path

This follows [Find in the complete caller](native-fs-find-caller-source-rom-1.3.2.md)
to its remaining Send boundary. It identifies `FSi_SendCommand`, the queue and
dispatch wrapper. `FSi_ExecuteSyncCommand`, command translation, Release/Next,
card operations and filesystem completion are separate links. No installer,
game behavior, ROM, save, ABI, identifier or default changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate an opaque archive token from the structure fields a native function
actually dereferences. Recover both source/recipe→ELF→ROM and ROM→caller→ABI→
source links. Require source-owned field/stack deltas, conditional effects and
interrupt-state restoration before interpreting a trace. A return-value boundary
that leaves a file linked and busy must not be described as completed filesystem
work. Preserve original fixtures and seek a different return after the same bytes.

## Il materiale più grezzo da cui partire

Supply your own exact ROM inputs. All have revision0. EN and inherited/localized
IT use IPKE; retail IT uses IPKI. ARM9 load is`0x02000000`, entry`0x02000800`,
file offset`0x4000`. Older compressed images use decoded section mapping; a logical
address does not establish a physical offset in those images.

| Language/stage | Bytes | SHA-256 |
| --- | --- | --- |
| EN retail |134217728|`65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105`|
| EN base1.1 |127104144|`281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d`|
| EN V4 |147345256|`179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90`|
| EN current |152786844|`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`|
| IT retail |134217728|`013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1`|
| IT base1.1 |131906120|`7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077`|
| IT V4 |153228136|`2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156`|
| IT current |159029760|`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`|

The function is`[0x020D7788,0x020D792C)`:420 bytes,105 ARM starts, no literal
pool. Current physical ROM offset is`0x000DB788`, in the uncompressed main
section; no overlay/autoload lifetime is introduced. The new prologue at
`0x020D792C` is outside the attributed body. All eight images match the same
420-byte SHA-256:
`ca74d4ff51db8cb32a7d6235e6b4d453554d65ac6162dc4092b7f285d0e4051a`.
This is retained native HGSS code, not a newly inserted Plus payload or padding.

The source counterpart is `lib/NitroSDK/src/fs/fs_send_command.c::FSi_SendCommand`
in [the pinned reference](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
Source file SHA-256:
`4cc68728ca70d26fb620e996493b7b7ef259d07d8150aab607957851a502e587`;
definition-only SHA-256:
`d54006d46407f418a263d5fe9bca449b4e2ced1cb123afaaf440969d1025204c`.
The receipt also hashes its Suspended/Busy/Sync inline helpers and18 original
headers. Original MW compiler/objects remain unavailable. The
[assembly](../../features/trainer-strategy/sorgenti/fs-send.S) is a recovered
attribution recipe with no installer. Clang21 targets ARMv5TE/ARM946E-S/ARM mode;
its receipt records executable hash/version, flags, commands and exit codes.
Recovered object SHA-256:
`028aa5b34853fdbf9500e15766a91d9626383773e59f6e933eb020c57a9f5492`.

The independent ELF reader rejects text relocations and checks the entire420
bytes. Raw ROM mapping and ndspy section decoding agree. The body contains12
BL sites plus a conditional-path BLX R2 callback. Binary coverage is distinct
from the finite path considered below.

ARM32 header assertions establish FSFile72, FSArchive92, FSFileLink8 and thread
queue8. FSFile has prev0/next4/arc8/stat12/command16/error20/queue24/prop32/arg48.
FSArchive has flag28/list32/list.next36/proc84/proc_flag88. Command FINDPATH is4,
ACTIVATE9, BUSY result2, CANCELED3; file BUSY1/SYNC4/OPERATING`0x40` and archive
SUSPEND8/RUNNING16/UNLOADING128 are explicit. These layout checks are not an
observed FSArchive initialization.

ROMs, raw data, RAM, saves, BIOS, assets and private captures remain local.
Public tests use synthetic inputs or developer-supplied recovered objects.

## I metodi e gli strumenti da usare

### Reproduction of source and byte correspondence

Use Python3, ndspy, Capstone, an authenticated Clang with ARM support, and a clean
reference checkout at the pinned commit. Set paths to your own files and fresh
private output directories outside `source/`:

```sh
python3 source/features/trainer-strategy/tools/compila_fs_send.py \
  --uscita "$SGP_SEND_RECIPE" --cc "$SGP_CLANG" \
  --reference "$SGP_HGSS_REFERENCE"

python3 source/features/trainer-strategy/tools/rileggi_fs_send.py \
  --retail "$SGP_RETAIL" --base "$SGP_BASE11" --v4 "$SGP_V4" \
  --rom "$SGP_ROM" --language EN --recipe-dir "$SGP_SEND_RECIPE" \
  --json "$SGP_OUT/send-lineage-EN.json"

SGP_FS_SEND_RECIPE_DIR="$SGP_SEND_RECIPE" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_send_recipe.py' -v

python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_send_bench.py' -v
```

Repeat the lineage reader with IT and its four inputs. Tests verify protected
output ownership, independent ELF bytes,105 ARM starts and all direct/indirect
call sites. The object test explicitly skips without private artifacts;
qualification requires zero skips. No ROM build or emulator installation is
needed for byte readback. Keep local argv, exit codes, hashes, source snapshots,
logs and OS peak RSS. Use one producer,180s/1GiB RSS/2MiB log/16MiB case limits,
with at least10GiB free after peak.

### Finite source path and declared state

The selected source path is command4, an empty file/queue link, idle archive and
no ACTIVATE callback. A new92-byte archive fixture declares the accessed state;
it is not inferred from the old opaque token. Normal ROM initialization installs
ACTIVATE|IDLE handling, so the no-ACTIVATE fixture must not be called natural boot.
The actual original Find→Send entry and304-byte frame must be authenticated
against the complete caller's raw receipt before isolated native execution.
Use `Find.services[0].entry` and its `frame_before`, not the pre-Find frame.

Native source preparation sets command4/errorBUSY2, stat1→5→`0x45`, links the
file after the archive sentinel (`archive+32`), sets file.prev/successor and
archive.list.next, and adds archive RUNNING. Other object bytes remain owned
preimages. The proposed ExecuteSync boundary changes a return value and permitted
volatile registers only. It performs no ID delivery, unlink, error reset,
Release/Next or completion. Linked/busy/error2 state therefore remains after
this boundary; it is not a successful completed Find or a natural SDK failure.

Four IRQ calls can reuse the qualified native
[Disable/Restore leaves](native-fs-wait-source-rom-1.3.2.md). A finite source
oracle follows the selected Send instructions and both IRQ bodies, with strict
32-bit registers and typed metadata. Rotated TST immediates`0x1FC` and`0x200`
produce shifter carry0; unrotated masks preserve carry. MSR control writes preserve
flags. Restore's final R2 includes the restored I bit; its intermediate I-cleared
value is not the final register. A source test checks this distinction.

Actual Send entry SP is TOP−280. Its PUSH24 reaches TOP−304, giving a complete
caller peak624. This exceeds the preceding608-byte bound and overwrites24 bytes
of its guard. This case is isolated: it cannot inherit the old fullcaller guard
or silently enlarge its projection. Frame304 uses the actual Send280 preimage
plus the last24 bytes of the preceding guard; an isolated lower guard is a
separate declared preimage.

### Evidence and remaining coverage

Source/byte reconstruction is qualified: eight420-byte matches, recovered ELF,
18 header dependencies and ARM32 layout assertions. Two recipe tests pass with
private object input. Six source-only tests cover queue fields, IRQ residuals,
FALSE0/truthy2, clobber and rejected input states. The final isolated matrix validates90 native hooks (68 Send plus22 IRQ
executions),15 stores,19 reads,79 unique native starts and92 steps including
one value boundary and the original return fetch. Five conditional hooks are
present without their architectural effects. Hook counts are not retired
instruction counts or hardware timing.

### Caller-derived execution and private replay

Runtime execution requires Unicorn2.1.4/model17, which is Cortex-A15. Only the
admitted ARMv5TE instruction semantics are qualified; this is not ARM946 silicon,
interrupt delivery or hardware timing evidence.

The [attribution CLI](../../features/trainer-strategy/tools/attribuisci_fs_send.py)
authenticates four distinct complete-caller Plus/seed cells and replays their
parent source oracles before copying the actual Send entry/frame. It checks the
parent ROM/proof, project objects and Read/Wait/Find recipe directories.
Historical parent captures from runtime`90071ed9…cfeb` require their exact retained
source; the qualified parent verifier`a2c0b332…5373` differs only in its Find
oracle. All other parent source identities and the entire remaining module AST
must match. Reports keep their original capture identities.

For your own current parent captures, omit `--parent-source` when their source
identities already match the qualified verifier. The example includes it for
the historical parent revision described in the linked guide. Set all paths to
your own input files and fresh private outputs:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_fs_send.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_FIND_CALLER_REPORT" \
  --parent-source "$SGP_PARENT_CAPTURE_SOURCE" --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --find-recipe "$SGP_FIND_RECIPE" \
  --recipe-dir "$SGP_SEND_RECIPE" --prepare-only \
  --json "$SGP_OUT/send-prepared-EN.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_send.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_FIND_CALLER_REPORT" \
  --parent-source "$SGP_PARENT_CAPTURE_SOURCE" --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --find-recipe "$SGP_FIND_RECIPE" \
  --recipe-dir "$SGP_SEND_RECIPE" --probe --raw-dir "$SGP_OUT/probe-raw" \
  --json "$SGP_OUT/send-probe-EN.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_send.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_FIND_CALLER_REPORT" \
  --parent-source "$SGP_PARENT_CAPTURE_SOURCE" --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --find-recipe "$SGP_FIND_RECIPE" \
  --recipe-dir "$SGP_SEND_RECIPE" --raw-dir "$SGP_OUT/raw-EN" \
  --json "$SGP_OUT/send-EN.json.gz"
```

Repeat with IT and its own parent report/project objects. Prepare-only executes
no guest and is mutually exclusive with probe. Raw per-run records are saved
before semantic evaluation, including faults and halted state. Admission checks
whitelist native ARM widths/live bytes, word owners, stack bounds and the model
boundary. CPSR is initialized before banked registers. The isolated whole4MiB
image is reconstructible from fill, captured frame, declared archive, three
native code bodies and two stopped/model fetch gates. Independent source
predictions modify only frame304/archive92; their complete image hash must match
actual CPU RAM readback. There is no excluded RAM range or OFF projection.
This is a reconstructible isolated image, separate from the complete caller's
retained final RAM byte pairs.

For optional CPU-free private replay, provide `send-EN.json.gz`/IT, directories
`raw-EN`/IT containing24 numbered records each, ROM links `r4-EN.nds`/IT and the
parent `find-caller-EN.json.gz`/IT reports. Set:

```sh
SGP_FS_SEND_REPORT_DIR="$SGP_SEND_REPORTS" \
SGP_FS_SEND_RAW_DIR="$SGP_SEND_RAW" \
SGP_FS_SEND_ROM_DIR="$SGP_ROM_LINKS" \
SGP_FS_SEND_PARENT_DIR="$SGP_FIND_REPORTS" \
SGP_FS_SEND_PARENT_SOURCE="$SGP_PARENT_CAPTURE_SOURCE" \
SGP_REMATCH_OBJECT_DIR="$SGP_REMATCH_CAMPAIGN" \
SGP_STRATEGY_OBJECT_DIR="$SGP_STRATEGY_CAMPAIGN" \
SGP_FS_SEND_READ_RECIPE="$SGP_READ_RECIPE" \
SGP_FS_SEND_WAIT_RECIPE="$SGP_WAIT_RECIPE" \
SGP_FS_SEND_FIND_RECIPE="$SGP_FIND_RECIPE" \
SGP_FS_SEND_RECIPE_DIR="$SGP_SEND_RECIPE" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_send*.py' -v
```

The parent-source variable is optional for current parent receipts. Object
campaign layout follows the linked caller guide. Replay authenticates each
fixture against parent preparation, exact distinct cells/policies,69 runtime
source identities, raw/report equality, source-owned fields, full register
contexts, complete reconstructed RAM and counters. It rejects typed aliases,
missing/forged stores, flow/IRQ flags, wrong return LR, guard/frame/archive changes
and wrong RAM hashes. Missing private artifacts cause explicit skips.

### Qualified results and limits

The final48 isolated runs cover four parent fixtures per language, each with
normal, OFF, ExecuteSync0, ExecuteSync2, volatile clobber and fill39. EN takes
4.413s/634552320-byte peak RSS; IT4.623s/647938048 bytes, including parent
preparation. All40 ON runs have90 native contexts,15 stores and19 reads; eight
OFF runs omit transcripts but preserve exact functional registers and whole RAM.
No compiler runs during these matrices. The native body, predictor and collector
remain unchanged between the first probe and both matrices.

Native API return restores R3–R7/SP/PC to the original Find return address;
LR remains`0x020D7928`. With no clobber, R1=`0x2000009F`, R2=`0x2000001F`,
CPSR=`0x2000001F`. Clobber changes R1/R2/IP/flags; native POP still restores R3.
The model value becomes API R0=0/1/2 without normalization. The eight FALSE
counters keep identical queue/frame/archive and complete RAM hashes, but return0
instead of1. Disguising their policy/result metadata as success is rejected with
`Send source-derived returned`. This is a deliberate boundary control, not a
naturally observed completed SDK failure. Truthy2/clobber preserve RAM; fill39
preserves owned outputs while changing the declared unowned fill.

Sixteen tests pass, zero skips,5.967s/829472768-byte peak RSS: eleven portable
and five requiring private objects/reports. Independent reviews cover source,
recipe/layout/ABI, collector/preparation, probe and all48 raw results. A negative
replay test initially replaced a zero byte with zero; it was corrected to flip
a bit. Only the test changed, so no guest campaign was repeated.

| Conclusion | Evidence and coverage |
| --- | --- |
| Documented provenance | pinned native SDK counterpart, original headers/layout, caller-derived input receipts |
| Recovered binary match |420-byte assembly/ELF and eight decoded/current physical readbacks; no original MW build |
| Finite source semantics | idle command4/no-ACTIVATE/empty-list path, native IRQ and declared ExecuteSync value boundary |
| Observed activation |48 isolated runs using eight authenticated caller fixtures; no complete caller Send integration |
| Unattributed links | real archive initialization, ACTIVATE/cancel/suspend/busy/nonempty queue, native ExecuteSync/translation/Release/Next/completion |

Natural archive state, fullcaller integration, SAVE/cold restart, hardware and
timing remain outside coverage. Only actual I0 Send entries are qualified; a
pure IRQ I1 test does not expand that domain. No game memory or performance
improvement is established. A matching payload or final hash cannot replace the
separate ABI, source-state and activation proofs.

The following [ExecuteSync attribution](native-fs-exec-sync-source-rom-1.3.2.md) uses this case’s actual service entry/preimage, preserving the archive-fixture and isolated-stack limits.
