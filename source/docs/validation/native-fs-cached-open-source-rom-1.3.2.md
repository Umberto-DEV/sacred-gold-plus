# Complete cached Open: a real pathname becomes a live file handle

Nine isolated native executions pass: five observed successes, two observed
finite bounds failures and two successful OFF runs. The real move-archive path
`a/0/1/1` resolves to fileID140 and opens with the exact cached FAT limits.
All22 functions execute original installed bytes, with zero service models or
runtime host writes. Input CPU/client/stack remain synthetic and the archive
procedure projection remains explicit.

This composes the [complete Convert API](native-fs-cached-convert-source-rom-1.3.2.md)
with Open/Fast and the real default Fast/Direct handlers. It closes the metadata
and handle boundary used by the [owner](../../features/trainer-strategy/README.md);
it does not execute the later NARC payload reader or a natural DTCM caller.
The [full ROM build/composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom)
explains how this native component relates to the existing Plus source pipeline.

## Professional checks beyond the minimum

Keep the three consumer identities separate: source NARC index11 is waza_tbl,
FNT fileID140 identifies the archive, and member310 is an archive member. PRET
file metadata and game-source callers establish meaning; the exact FNT/FAT
establish numeric IDs and bounds. Follow both source→recipe→ELF→ROM and
ROM table→path→function→caller. Reuse authenticated parents without rebuilding
them merely to compose a larger execution.

Treat lifetimes as part of the ABI. A completed command restores an empty archive
queue, but a successful Open leaves the client handle **live** with IS_FILE set.
Do not clear it to force a closed-file expectation. Conversely, Convert's
on-stack directory is dead after it returns: later native frames may reuse
those bytes. Check that directory at its real lifetime boundary, then compare
all subsequent writes chronologically. Do not transplant the earlier fixture
or restore its temporary file between phases.

Use both a same-final-state writer falsifier and a new finite failure condition.
An initially completed client property must still receive the four native
Direct stores. A declared FAT size exactly equal to the record's start must
fail before the FAT read/Direct call, while the preceding FNT lookup succeeds.
That negative fixture is deliberately truncated metadata, not a natural failure
or an injected return value. Independent review checks ABI, offsets, both branch
routes, raw replay and source/recipe identities.

## Raw starting material and provenance

The [Convert input identities](native-fs-cached-convert-source-rom-1.3.2.md#raw-starting-material-identity-and-provenance)
remain mandatory: owned exact r4 EN152786844bytes SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
IT readback159029760bytes SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`,
IPKE/revision0. Use the clean SDK/game source pin
`cb614ad23449d5852b40321dc409c4143872b35c`, not the newer PRET research checkout
as a production replacement. The public parent guide identifies the optional
historical MainRAM gzip; no private capture, BIOS or save is required in the
separate ROM-only mode.

The actual path literal at RAM`0x0210F198`, FNT2902bytes, FAT4104bytes,
ARC92bytes and root BSS12 have separate authenticated identities. Root at
`0x021E362C` remains BSS with no initialized physical ROM offset; its source,
loader descriptor and historical snapshot provenance are separate from a
synthetic ROM-only initialization. No natural entry registers or DTCM stack
are recovered by copying these resources.

FAT record140 is at RAM`0x023BE9E0` (FAT`0x023BE580` +1120). Its top is
`0x01093800`, bottom`0x0109645C`, length11356bytes. The full FAT stays read-only;
no archive payload bytes or `read_func` callback are needed to open it. The
independent FNT parser resolves directories0/1/2/4 and file140. Its20 logical
reads precede exactly one8-byte FAT copy on successful Open.

## Methods, source and recovered compilation

The earlier18 objects retain their original sources, recipes, compiler/layout
receipts and limits. Open72 and Fast112 are also retained. Only the two default
handlers are newly assembled for this case:

|Component|RAM|Current ROM offset|Extent|Text SHA-256|
|---|---|---|---:|---|
|Open wrapper|`0x020D8278`|`0x000DC278`|72code|`844c19c244efe83b1be9dd83f73da60917d201793d237d72cf0a429ca9158a2d`|
|Fast wrapper|`0x020D8208`|`0x000DC208`|112code|`465013782ef4760fff5100c626a4ddc63e8611d1517a1b9bc105b23092638bd9`|
|Fast command|`0x020D7340`|`0x000DB340`|128code|`b8f19fba6a413a29a20b56c8a6d404d3eae2dd4282424fa398e0dc986f91bee4`|
|Direct command|`0x020D73C0`|`0x000DB3C0`|40code|`88d89e44e514c13c621af01ddd078a8fc112dcbce021ebd2d90b1ef53788bfaf`|

Total retained bodies4056bytes =4040code (1010 ARM starts) +16pool bytes;
the default command table adds36 data bytes. Slots6/7 point to7340/73C0.
Initialized current ARM9 header mapping is RAM−`0x02000000`+`0x4000`; these
windows are not overlay/compressed code. Independent ELF parsing, current
physical reads and ARM9-only/autoload decoding compare the two new handlers
across retail→inherited base→V4→r4 in EN/IT (16 exact body comparisons).
That is coverage of those two bodies, not a fresh whole-ROM lineage proof.

`FS_file.c::FS_OpenFile/FS_OpenFileFast` and
`FS_command_default.c::FSi_OpenFileFastCommand/FSi_OpenFileDirectCommand`
provide the source counterparts. Fast reads `arg.openfilefast.id.file_id` at52,
checks its shifted record start against `ARC.fat_size`, reads the record through
native ReadTable/ReadMemory/Copy, rewrites `ARGdirect={top48,bottom52,index56}`
and calls Translate7. Direct stores property top36/position44/bottom40/ID32.
Nested Translate7 does not change the client's command6: it is not Send7.

The [new recipe](../../features/trainer-strategy/sorgenti/fs-cached-open.S) and
[builder](../../features/trainer-strategy/tools/compila_fs_cached_open.py) reuse
the pinned cached SeekDir build function with explicit component metadata,
recipe, extractor and extra ABI assertions. Two ELF objects match168bytes,
with no relocations;18 original headers verify FAT8, FastInfo8, DirectInfo12,
argument/property offsets and command/result IDs. Compiler is the qualified
Clang21 SHA-256`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
Keep compiler commands/flags, source/header hashes, layout checks and exit codes
from each `manifesto.json`. Original Metrowerks C code generation is missing:
these are recovered comparison objects, with no installer or ROM mutation.
Matching ELF text does not authenticate a new object's compiler origin.

### Context, callbacks, activation and lifetime

```mermaid
flowchart LR
  Open["Open / full Convert / native lookup"] --> Fast["Fast / Send6 / ExecuteSync"]
  Fast --> Table["Translate6 / default Fast / FAT ReadTable"]
  Table --> Direct["Translate7 / default Direct"]
  Direct --> Return["Release / Wakeup / Next / live handle return"]
```

Client FSFile72 at`0x022F0000` has an explicit source-initialized precondition:
zero links, queue, ARC and status; commandINVALID14; other bytes A5, except the
precompleted-property control. This is not an observed client Init call.
Convert internally calls native Init for its separate temporary directory.
CPU entry`0x020D8278` has R0client/R1actual path, R2–R12 cookies,
SP`0x023FD000`, LRstop`0x022F0180`, CPSR`0x6000001F`.

Open allocates localID8 at SPtop−16; Convert's DIR is at SPtop−104.
At Convert→Fast, replay of618 prefix stores (Open PUSH2 +Convert616) checks
DIR72 and ID8 while both are live. Later Send/FAT frames legitimately overwrite
dead DIR bytes. No host phase reset, copied parent frame or register bridge is
used. Full frame480 and guard56, client guards16 and all15 mapped4KiB pages
(61440bytes) are verified, including untouched neighbors.

As in the parent, ARC starts flag7 with empty queues/list. Historical
proc_flag`0x602`→`0x2` is a minimal declared input projection disabling
ACTIVATE/IDLE card-lock callbacks; other ARC bytes/pointers remain intact.
ROM-only proc0/unused synthetic fields are judged separately. Each of two
native Send cycles sets RUNNING and later Release/Next restores flag7.
The projected card protocol is not claimed natural. Native IRQ Disable/Restore
execute ten calls each; the qualified finite arithmetic/IRQ helper is unchanged.
No new ISA or host service is added.

The [reader](../../features/trainer-strategy/tools/rileggi_fs_cached_open.py),
[freezer](../../features/trainer-strategy/tools/congela_fs_cached_open.py),
[source bench](../../features/trainer-strategy/test/fs_cached_open_bench.py)
and [CLI](../../features/trainer-strategy/tools/attribuisci_fs_cached_open.py)
keep functional FNT/FAT/handle checks separate from instruction arithmetic.
Static194 read/127 write sites are rederived before the guest. Only PC and
read/write site/address/width enforcement sets reach the producer, not predicted
state. Backend Unicorn2.1.4 CPU17 executes original bytes with zero models or
runtime host writes; it is not ARM946 silicon, timing, cache or IRQ delivery.

## Reproduce with your own inputs

Run from repository root with the project Python environment and Git. Reader,
freezer, prepare and saved-raw verification use standard Python/Git and do not
need a CPU package; probe/matrix need Unicorn2.1.4. New object builds need the
qualified compiler and clean pinned SDK. Preserve the original input files and
choose fresh private output outside `source/`. Plan1GiB disk peak with at least
10GiB free afterward; bound each command180s/1GiB OS RSS/2MiB logs and the case
16MiB. Do not rebuild retained objects when you already have verified copies.
The [parent recipe list](native-fs-cached-convert-source-rom-1.3.2.md#methods-recovered-compilation-and-installed-bytes)
explains their source and provenance; the commands below also construct a fresh
object set for a developer who has none. They produce comparisons, not a game.

```sh
export SGP_OPEN_ROM=/absolute/path/to/owned-exact-r4-EN.nds
export SGP_OPEN_REF=/absolute/path/to/clean-pinned-sdk-checkout
export SGP_OPEN_OUT=/absolute/path/to/fresh-private-open-case
export SGP_OPEN_CC=/absolute/path/to/authenticated-clang
mkdir "$SGP_OPEN_OUT"

# Reuse verified objects if available; otherwise build these small comparisons
# sequentially, retaining each manifesto.json. No game image is generated.
for recipe in fs_init fs_convert fs_find fs_send fs_exec_sync fs_release \
    os_wakeup fs_next fs_wait fs_translate fs_cached_seekdir fs_cached_findpath fs_open fs_fast fs_cached_open
do
  python3 "source/features/trainer-strategy/tools/compila_${recipe}.py" \
    --uscita "$SGP_OPEN_OUT/recipe-$recipe" \
    --cc "$SGP_OPEN_CC" --reference "$SGP_OPEN_REF" || exit
done

python3 - <<'PYMAP'
import json, os
from pathlib import Path
out=Path(os.environ['SGP_OPEN_OUT'])
names={'convert': ('fs_convert', 'fs-convert.o'),
 'copy': ('fs_cached_seekdir', 'copy.o'),
 'direct_command': ('fs_cached_open', 'direct_command.o'),
 'disable': ('fs_wait', 'fs-wait-disable.o'),
 'execute': ('fs_exec_sync', 'fs-exec-sync-command.o'),
 'fast': ('fs_fast', 'fs-fast.o'),
 'fast_command': ('fs_cached_open', 'fast_command.o'),
 'find': ('fs_find', 'fs-find-path.o'),
 'findpath': ('fs_cached_findpath', 'findpath.o'),
 'init': ('fs_init', 'fs-init.o'),
 'next': ('fs_next', 'fs-next-command.o'),
 'open': ('fs_open', 'fs-open.o'),
 'read_dir': ('fs_cached_findpath', 'read_dir.o'),
 'read_memory': ('fs_cached_seekdir', 'read_memory.o'),
 'read_table': ('fs_cached_seekdir', 'read_table.o'),
 'release': ('fs_release', 'fs-release-command.o'),
 'restore': ('fs_wait', 'fs-wait-restore.o'),
 'seekdir': ('fs_cached_seekdir', 'seekdir.o'),
 'send': ('fs_send', 'fs-send-command.o'),
 'strnicmp': ('fs_cached_findpath', 'strnicmp.o'),
 'translate': ('fs_translate', 'fs-translate-command.o'),
 'wakeup': ('os_wakeup', 'os-wakeup-command.o')}
(out/'objects.json').write_text(json.dumps({
    name:str(out/('recipe-'+owner)/filename)
    for name,(owner,filename) in names.items()},indent=2)+'\n')
PYMAP

python3 source/features/trainer-strategy/tools/rileggi_fs_cached_open.py \
  --rom "$SGP_OPEN_ROM" --json "$SGP_OPEN_OUT/resources.json"
python3 source/features/trainer-strategy/tools/congela_fs_cached_open.py \
  --rom "$SGP_OPEN_ROM" --json "$SGP_OPEN_OUT/input.json"

# Freeze before predicting or executing. Each command requires fresh output.
for mode in prepare probe matrix
do
  python3 source/features/trainer-strategy/tools/attribuisci_fs_cached_open.py     --mode "$mode" --rom "$SGP_OPEN_ROM" \
    --objects "$SGP_OPEN_OUT/objects.json" \
    --recipe-dir "$SGP_OPEN_OUT/recipe-fs_cached_open" --reference "$SGP_OPEN_REF" \
    --input-contract "$SGP_OPEN_OUT/input.json" \
    --out-dir "$SGP_OPEN_OUT/$mode" || exit
done

# CPU/compiler-free rejudgment of saved raw and all control evidence.
python3 -I -S -B source/features/trainer-strategy/tools/attribuisci_fs_cached_open.py \
  --mode verify --rom "$SGP_OPEN_ROM" \
  --objects "$SGP_OPEN_OUT/objects.json" \
    --recipe-dir "$SGP_OPEN_OUT/recipe-fs_cached_open" --reference "$SGP_OPEN_REF" \
  --input-contract "$SGP_OPEN_OUT/input.json" \
  --raw-dir "$SGP_OPEN_OUT/matrix" --out-dir "$SGP_OPEN_OUT/verified"

python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_cached_open*.py'
```

The object map has exactly22 names, and `--recipe-dir` points to the two new
objects' completed layout/compiler receipt. Relative object paths are relative
to the current working directory. To use the qualified historical MainRAM,
pass the same optional `--snapshot` to reader, freezer and each attribution
command. The optional reader `--it-rom` compares initialized bytes/BSS bounds;
it does not transfer EN RAM into Italian execution.

The CLI pins and reuses the previous generic ELF verification function with
explicit22-component metadata; it does not edit the parent source or execute
its producer. CPU-free `--mode verify --raw-dir` reauthenticates43 runtime
sources, exact inputs, the three frozen fixtures of the selected resource mode
(six across both qualified modes), SDK/recipes/ELF/manifests, raw
schema/names/hashes and every control. Ordinary CLI/JSON lets other developers
and agents review evidence without private assistant handoffs.

## Results, counterexamples and coverage

Source predictions were frozen before the first guest and agree with every
native context, memory read/store and final page. No expected-state adjustment
followed the first execution. Positive:3191 native instructions,681 distinct
PCs,942 reads,715 stores,3192 code callbacks including the stopped gate,
peak480. Negative equality input:3053/645PC/902 reads/681 stores/3054 callbacks,
peak480. Fifteen new ROM-free tests pass with zero skips.

On success the client is a live file: ARC,command6,error0,statusIS_FILE16decimal;
property`{ID140,top01093800,bottom0109645C,pos01093800}`, Direct argument union
contains top/bottom/ID, zero links/queue. Other unused bytes retain their source
lifetime values. Full16 return is BOOL1, R1=`0x10`, R2=`0x6000001F`, R3 and
R4–R11 preserved, IP=SPtop−112=`0x023FCF90`, SP restored,
LR=`0x020D82A4`, CPSR=`0x2000001F`. Fast explicitly restores LR before BX;
Open POP PC leaves that LR residue, different from the earlier Convert API.

Both precompleted-property controls converge in final CPU/all15pages/flow/read,
but stores682–685 at PCs`0x020D73C4/73CC/73D4/73DC` have different preimages.
The verifier rejects input camouflage and deletion of each writer, ten forged
variants total. Two OFF runs retain counters/enforcement and exact final state
without observed ledgers. Both resource modes get separate judgments.

The extra negative input projects only ARC.fat_size from`0x1008` to`0x460`,
the record start. Lookup still yields140, but native Fast returns failure1
without the21st/FAT copy or Translate7/Direct. Open returns FALSE0, client
error1/status0, property A5, argument remains FastID{ARC,140}; ARC preserves
the deliberately shortened size. Returned R1=`0x6000009F`, IP=`0xFFFFFFF0`,
LR=`0x020D82A4`, CPSR=`0x6000001F`. Source checks only **start < size**, not
record-end <= size; a declared size`0x461` would pass that source condition.
That limit is documented and unit-tested, not silently repaired or generalized
to arbitrary malformed archives/overflowing IDs. Actual ID140/FAT4104 is valid.

Nine runs are six distinct input fixtures: the first probe duplicates the
natural-resource normal input and OFF duplicates its corresponding initial
state. Success callgraph adds13Translate/21ReadTable-memory-copy; failure has
12Translate/20copies/noDirect. Both have2Send/Execute/Release/Wake/Next and
10Disable/10Restore. Two CPU-free raw verifications pass without Unicorn or
compiler. Native matrices take under0.75s and69MB OS peak RSS here: those are
host costs, not a DS performance improvement.

Distinguish documented source provenance, reconstructed binary agreement,
finite semantic equivalence and isolated activation. Not established: original
MWC/full-ROM-from-C build, natural caller/DTCM/card-lock protocol, async/payload
read callback, Italian execution, hardware IRQ/timing or physical SAVE. No game,
ROM/save layout, settings, IDs, input or ABI is changed; no memory gain is claimed.
A next useful question is the payload/read callback domain, with its own state
contract, rather than calling cached metadata a complete native NARC reader.

The [subsequent memory-archive Read case](native-fs-memory-read-source-rom-1.3.2.md)
adds native payload Read/Seek/Close with explicit ARC base/read_func/procedure
input projections and a separately compiled test caller. It does not retroactively
qualify natural CARD I/O or the native Thumb NARC parser in this Open case.
