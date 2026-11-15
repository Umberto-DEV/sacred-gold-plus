# Native memory-archive Read: open, read, seek, read and close

Seven isolated executions pass the complete five-API chain using original SDK
bytes and an explicitly configured memory payload. They produce the exact owned
NARC header16 and member31016, return `[1,16,1,16,1]` and close the handle.
Each run executes **4252 original ROM instructions plus27 project caller
instructions**, with zero service models or runtime host writes.

This follows the [complete Open case](native-fs-cached-open-source-rom-1.3.2.md).
The new archive input projects base/read_func/procedure fields; it is not the
ROM's natural CARD configuration. CARD async/controller/completion remains a
separate gap. The small test caller is compiled project code mapped into the
isolated bench, never installed in a game. The [owner](../../features/trainer-strategy/README.md)
and [full ROM build map](../test-bench.md#from-the-source-tree-to-the-complete-rom)
connect these native attribution artifacts to the existing composition pipeline.

## Professional checks beyond the minimum

Identify why cached FAT/FNT does not supply file data. Natural `read_func`
`0x020D84C4` calls CARD_ReadRomAsync and returns ASYNC6. Its controller, task,
thread, completion and lock state is not qualified by the prior isolated cases.
Do not turn that gap into a host memcpy or a forged completion0.

The SDK defines a real memory callback, `FSi_ReadMemCallback`, selected by
FS_LoadArchive when no read callback is supplied. It computes `ARC.base+pos`,
whereas the cached table callback `FSi_ReadMemoryCore` copies an absolute table
pointer and ignores base. Use the memory callback as a declared **new hybrid
input**, preserving FAT/FNT offsets and distinguishing it from observed boot
or an observed FS_LoadArchive call. Match source/recipe/ELF/ROM and the actual
memory reads in both directions.

Keep original game code, recovered comparison recipes and the project test
caller separate. Validate its ARM instructions, branches, literal pool,
callee-saved registers, alignment, return vector and bounds before execution.
A result already present in the destination must not conceal missing native
copy stores. OFF retains all enforcement while recording no observations.
Independent review checks complete contexts and chronology, not only32 bytes.

## Raw starting material, ownership and requirements

Use your owned exact r4 EN152786844bytes SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
optional IT readback159029760bytes SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both are IPKE/revision0; presentation language is recorded separately. The
[Open input guide](native-fs-cached-open-source-rom-1.3.2.md#raw-starting-material-and-provenance)
explains cached resources, clean SDK pin
`cb614ad23449d5852b40321dc409c4143872b35c`, optional qualified historical
MainRAM and the independent ROM-derived synthetic ARC/root mode.

Root12 at`0x021E362C` is BSS, not initialized ROM data. Parent resource receipts
may describe authenticated historical resources as natural; the **projected
memory-archive input and synthetic caller/CPU/stack are not a natural entry**.
No DTCM, controller or whole-memory image is inferred from those slices.
The newer PRET research snapshots supply file metadata, not a replacement
production pin, original compiler or Italian regional build.

FileID140 is the actual `a/0/1/1` path for source NARC index11 (waza_tbl).
Member310 is a third namespace. FAT140 is `[0x01093800,0x0109645C)`,11356bytes.
The independent bounded metadata parser reads only six windows totaling68bytes,
never an entire NARC object: header16, BTAF12, member entry8, BTNF8, GMIF8,
selected payload16. It checks count471, chunk layout and bounds, then derives
member310 at file-relative`0x224C`, ROM`0x01095A4C`, length16.

|Owned window|ROM offset|Mapped source RAM|SHA-256|
|---|---|---|---|
|NARC header16|`0x01093800`|`0x02310020`|`6ee74f5eec705d828dc93263a65dbbf260a9bbaa561e8c35d1b6caaa5bc1ff47`|
|Member310/16|`0x01095A4C`|`0x0231226C`|`85ac8d2ffc1e263ba41dfed64ea9b07613bd3fe76e8a68ef13e93394179dc5c8`|

Only these32 payload bytes are mapped into two sparse read-only source windows,
with synthetic guards/neighbors. No complete archive/ROM/address-space copy is
made. EN/IT current windows agree by fresh readback; Italian execution is not
claimed. Member byte6=15 is an authenticated copied scalar, not a native PP
getter/setter or a native NARC parser result.

### Explicit archive configuration

Before entry, copy the authenticated source ARC or its separately declared
ROM-derived version, then project:

|Field|Historical source|New input|Reason|
|---|---|---|---|
|base at40|0|`0x0127C820`|top+base maps the two file positions to the source windows|
|read_func at72|`0x020D84C4`|`0x020D7448`|native memory payload callback|
|proc_flag at88|`0x602`|`0x2`|disable ACTIVATE/IDLE CARD locks, retain WRITE unsupported bit|

ROM-derived ARC starts with declared synthetic unused fields/read_func0/proc0;
its projection records0→7448 and0→0 separately. All other ARC bytes and the
entire FAT/FNT stay intact. Flags start7, lists/queues empty. No RUNNING17 or
completion result is injected. These are initial fixture projections, not game
patches, runtime host writes or natural CARD observations.

## Methods, components and recovered compilation

Retain27 prior objects:22 from Open and Read wrapper16/core124, Wait192,
Seek108 and Close60. Three new comparison objects cover80 original bytes:

|Native component|RAM extent|Current ROM start|SHA-256|
|---|---|---|---|
|ReadFileCommand44|`0x020D6B94..0x020D6BC0`|`0x000DAB94`|`a28edc117522c9993df5831add97fc2e04ddc068c75ede7da505e73b72cfdd76`|
|ReadMemCallback28|`0x020D7448..0x020D7464`|`0x000DB448`|`f5075f0378cb58f5f03c91e634ac04828ffd4f545c9b59316d833a04d3feb86e`|
|CloseCommand8|`0x020D73E8..0x020D73F0`|`0x000DB3E8`|`6dcd5e75586fe6683156c0d559d4827b73bd48d501fa5781a1c6099aacd7c877`|

These30 SDK bodies total4636bytes =4616code/1154 ARM starts +20pool; default
table36 is separate data. The Read wrapper contributes12code+4pool at83D8.
Initialized ARM9 mapping is checked from the header; no overlay/compressed
ownership is attributed to these current windows. Independent ELF/physical/
ARM9-only-autoload reads compare the three new bodies across eight EN/IT
retail→base→V4→r4 inputs (24 body comparisons), plus six current physical reads.
The remaining objects retain their parent lineage coverage and current readback.

Sources are FS_file.c, FS_command_default.c, FS_archive_prefix.c, archive.h and
FS_archive_suffix.c, with the prior FS/MI/OS dependency set. The
[native comparison recipe](../../features/trainer-strategy/sorgenti/fs-memory-read.S)
and [builder](../../features/trainer-strategy/tools/compila_fs_memory_read.py)
reuse the pinned cached builder with extra ABI assertions and six source hashes.
Eighteen original headers verify ReadInfo12, dst48/org52/len56, pos44,
base40/read_func72, command0/8 and result/status values. Clang21 SHA-256 is
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
Build receipts retain source/recipe/ELF hashes, flags, commands, dependencies,
layout checks and exits. Original Metrowerks C code generation is unavailable;
these are recovered byte comparisons, not a whole-ROM-from-C rebuild.

One retained Close builder's historical receipt differs only in its later
CLI-help docstring; the archived help-only receipt and AST equivalence record
that drift without pretending a new compilation. Matching text does not prove
the compiler origin of a newly supplied object. Keep your own build receipts.

### Project caller and execution contract

The [test caller](../../features/trainer-strategy/sorgenti/memory-narc-driver.S)
is a separate116-byte ELF,108code/27ARM +8pool, at synthetic RAM`0x022F0800`.
Complete text SHA-256:
`96474b1b6cc63a7210be3761705bcbcd0398fefc7c61e53fff50cb770fb2198c`.
Five ARM BL sites call Open8278, Read83CC, Seek83DC, Read83CC and Close82C0.
The literal pool contains only the result-vector address and relative offset224C.
No veneer, relocation, runtime patch or installer is used.

Entry R0=client`0x022F0000`, R1=actual path`0x0210F198`,
R2=header destination`0x022F0200`, R3=member destination`0x022F0240`;
R4–R12 are cookies, SP`0x023FD000`, LRstop`0x022F0180`, CPSR`0x6000001F`.
Client72 has the same declared seven-field Init precondition as Open, not a
captured Init call. The driver PUSHes six words (24bytes, eight-byte alignment),
preserves R4–R8 and records five native return values at`0x022F0280`.
It returns that vector pointer, not Close's Boolean.

Compile the own caller **before the complete memory freeze**, because its ELF
is an input. Source/recipe/addresses/ABI are fixed before compilation; the full
freeze precedes the new oracle and CPU. This ordering needs no second assembler
or host register dispatcher. The qualified arithmetic/IRQ helper is unchanged.
Static227 read/148 write sites are rederived from1181 admitted ARM starts
(1154 original+27 project); only PC/read/write enforcement sets enter the CPU
producer, never predicted memory or registers.

Driver24 shifts every Open frame: live directory at SPtop−128, localID at
SPtop−40. Replay624 prefix stores (driver6/Open2/Convert616) checks those while
live; later frames legitimately reuse dead stack. Global frame504 =caller24+
Open480, guard56 beneath; header/member/vector and client guards16 are distinct.
All17 sparse4KiB pages (69632bytes) are compared completely.

Read core sets SYNC4 before Send0; command0 is outside Send's sync mask1FC.
ReadFileCommand **stores new position at6BAC before BLX6BB8**, but passes the
old position in R2. ReadMemCallback adds base and copies the exact16 bytes,
returns FSResult0; Read core/Wait return16 after native completion. Header
read advances to01093810, Seek SET224C to01095A4C, member read to01095A5C.
Close returns1 and clears client ARC/status/command to0/0/INVALID14, preserving
property bounds/position and the final read argument union. ARC returns to7
with empty queues after all five APIs; its three projections remain unchanged.

## Reproduce with your own inputs

Run from repository root with Python3/Git and owned exact inputs. Native probe/
matrix additionally need Unicorn2.1.4. Reader/freezer/prepare/verify need no CPU
package; original build receipts and the clean pinned SDK remain required.
Rebuilding comparisons uses the authenticated Mac Clang toolchain; another
compiler/platform requires its own qualification, not bypassing the digest pin.
No compiler, emulator, BIOS, ROM, save or personal capture is installed here.

Choose fresh private output outside `source/`, one producer,180s/1GiB OS RSS/
2MiB log per command,16MiB per case, planned1GiB disk peak and at least10GiB
free afterward. Reuse verified objects; the full sequential list below is for
a developer who has none. It creates comparison/caller objects, not a ROM.

```sh
export SGP_READ_ROM=/absolute/path/to/owned-exact-r4-EN.nds
export SGP_READ_REF=/absolute/path/to/clean-pinned-sdk-checkout
export SGP_READ_OUT=/absolute/path/to/fresh-private-read-case
export SGP_READ_CC=/absolute/path/to/authenticated-clang
mkdir "$SGP_READ_OUT"

# Reuse verified objects if available; otherwise build these small comparisons
# sequentially, retaining each manifesto.json. No game image is generated.
for recipe in fs_init fs_convert fs_find fs_send fs_exec_sync fs_release \
    os_wakeup fs_next fs_wait fs_translate fs_cached_seekdir fs_cached_findpath fs_open fs_fast fs_cached_open \
    fs_read fs_seek fs_close fs_memory_read
do
  python3 "source/features/trainer-strategy/tools/compila_${recipe}.py" \
    --uscita "$SGP_READ_OUT/recipe-$recipe" \
    --cc "$SGP_READ_CC" --reference "$SGP_READ_REF" || exit
done

python3 - <<'PYMAP'
import json, os
from pathlib import Path
out=Path(os.environ['SGP_READ_OUT'])
names={'close': ('fs_close', 'fs-close.o'),
 'close_command': ('fs_memory_read', 'close_command.o'),
 'convert': ('fs_convert', 'fs-convert.o'),
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
 'read_callback': ('fs_memory_read', 'read_callback.o'),
 'read_command': ('fs_memory_read', 'read_command.o'),
 'read_core': ('fs_read', 'fs-read-core.o'),
 'read_dir': ('fs_cached_findpath', 'read_dir.o'),
 'read_memory': ('fs_cached_seekdir', 'read_memory.o'),
 'read_table': ('fs_cached_seekdir', 'read_table.o'),
 'read_wrapper': ('fs_read', 'fs-read-wrapper.o'),
 'release': ('fs_release', 'fs-release-command.o'),
 'restore': ('fs_wait', 'fs-wait-restore.o'),
 'seek': ('fs_seek', 'fs-seek.o'),
 'seekdir': ('fs_cached_seekdir', 'seekdir.o'),
 'send': ('fs_send', 'fs-send-command.o'),
 'strnicmp': ('fs_cached_findpath', 'strnicmp.o'),
 'translate': ('fs_translate', 'fs-translate-command.o'),
 'wait': ('fs_wait', 'fs-wait-core.o'),
 'wakeup': ('os_wakeup', 'os-wakeup-command.o')}
(out/'objects.json').write_text(json.dumps({
    name:str(out/('recipe-'+owner)/filename)
    for name,(owner,filename) in names.items()},indent=2)+'\n')
PYMAP

python3 source/features/trainer-strategy/tools/rileggi_fs_memory_read.py \
  --rom "$SGP_READ_ROM" --json "$SGP_READ_OUT/resources.json"
python3 source/features/trainer-strategy/tools/congela_fs_memory_read.py \
  --rom "$SGP_READ_ROM" --recipe-dir "$SGP_READ_OUT/recipe-fs_memory_read" \
  --json "$SGP_READ_OUT/input.json"

# Freeze before predicting or executing. Each command requires fresh output.
for mode in prepare probe matrix
do
  python3 source/features/trainer-strategy/tools/attribuisci_fs_memory_read.py     --mode "$mode" --rom "$SGP_READ_ROM" \
    --objects "$SGP_READ_OUT/objects.json" \
    --recipe-dir "$SGP_READ_OUT/recipe-fs_memory_read" --reference "$SGP_READ_REF" \
    --input-contract "$SGP_READ_OUT/input.json" \
    --out-dir "$SGP_READ_OUT/$mode" || exit
done

# CPU/compiler-free rejudgment of saved raw and all control evidence.
python3 -I -S -B source/features/trainer-strategy/tools/attribuisci_fs_memory_read.py \
  --mode verify --rom "$SGP_READ_ROM" \
  --objects "$SGP_READ_OUT/objects.json" \
    --recipe-dir "$SGP_READ_OUT/recipe-fs_memory_read" --reference "$SGP_READ_REF" \
  --input-contract "$SGP_READ_OUT/input.json" \
  --raw-dir "$SGP_READ_OUT/matrix" --out-dir "$SGP_READ_OUT/verified"

python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_memory_read*.py'
```

The JSON map contains exactly30 **original SDK** object names. `--recipe-dir`
also supplies the separate project driver and its build receipt. Relative paths
are relative to the current working directory. To use the historical qualified
MainRAM instead of ROM-derived resources, pass the same optional `--snapshot`
to reader, freezer and every attribution command. `--it-rom` is an optional
reader-only byte comparison, not Italian activation.

The [CLI](../../features/trainer-strategy/tools/attribuisci_fs_memory_read.py)
uses prepare/probe/matrix/verify. Verify runs with `-I -S`, standard Python/Git,
without importing Unicorn or invoking the compiler. It reauthenticates56 source
files, native ELF and separate driver, exact inputs and two frozen fixtures
for the selected resource mode (four across both modes), raw schema/local
names/hashes, complete registers/ledgers/pages and every control. Native,
project and combined instruction counters are separate in the raw schema.
These ordinary CLI/JSON interfaces are usable by other developers and agents
without sharing assistant prompts or private handoffs.

### Independent ROM readback without execution

For a second ROM extraction path, use ndspy4.2.0 in your existing project
environment. The following streams the full ROM identity hash, then loads only ARM9,
decodes its sections/autoload and
compares the three new native objects. It creates no ROM model or extracted
game tree. `SGP_READ_IT_ROM` is optional; omit it for EN-only readback.
Output is a fresh private JSON receipt, not raw code or payload bytes. To reuse
a retained recipe directory, set optional `SGP_READ_RECIPE` to that directory.

```sh
# Optional: export SGP_READ_IT_ROM=/absolute/path/to/owned-exact-r4-IT.nds
python3 - <<'PYREADBACK'
import hashlib, importlib.metadata, importlib.util, json, os, struct
from pathlib import Path
import ndspy.code
assert importlib.metadata.version('ndspy') == '4.2.0'
path=Path('source/features/trainer-strategy/tools/compila_fs_memory_read.py')
spec=importlib.util.spec_from_file_location('owned_readback_builder',path)
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
out=Path(os.environ['SGP_READ_OUT'])
texts=C.objects(Path(os.environ.get('SGP_READ_RECIPE',str(out/'recipe-fs_memory_read'))))
images=[(Path(os.environ['SGP_READ_ROM']),152786844,
         '2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d')]
if os.environ.get('SGP_READ_IT_ROM'):
    images.append((Path(os.environ['SGP_READ_IT_ROM']),159029760,
                   '13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a'))
rows=[]
for image,size,digest in images:
    assert image.stat().st_size==size
    with image.open('rb')as stream:
        h=hashlib.sha256()
        for chunk in iter(lambda:stream.read(65536),b''):h.update(chunk)
        assert h.hexdigest()==digest
        stream.seek(0);header=stream.read(512)
        offset,ram,length=(struct.unpack_from('<I',header,p)[0]for p in(0x20,0x28,0x2c))
        assert 0<length<=16*1024**2 and offset+length<=size
        stream.seek(offset);arm9=stream.read(length)
    module=ndspy.code.MainCodeFile(arm9,ram)
    for name,(address,length,expected)in C.BODIES.items():
        sections=[s for s in module.sections if s.ramAddress<=address and address+length<=s.ramAddress+len(s.data)]
        assert len(sections)==1
        section=sections[0];start=address-section.ramAddress
        decoded=bytes(section.data[start:start+length])
        assert decoded==texts[name]and hashlib.sha256(decoded).hexdigest()==expected
        rows.append(dict(image_sha256=digest,component=name,ram=address,bytes=length,sha256=expected,decoded_equal=True))
    del module,arm9
with(out/'readback-independent.json').open('x')as stream:
    json.dump(dict(ROM_model_loaded=False,CPU_executed=False,compiler_invoked=False,comparisons=rows),stream,indent=2)
    stream.write('\n')
print(len(rows),'independent ARM9-only component comparisons passed')
PYREADBACK
```

To repeat optional historical comparisons, extend `images` with the eight
owned EN/IT retail/base/V4/r4 images and independently trusted size/SHA-256
receipts. A stage label alone is not an authenticated input identity. The same
section extraction handles initialized/autoload ownership; it does not infer
BSS contents from RAM-minus-ROM offsets. Current direct physical windows are
checked separately by the resource reader. This second extraction is independent
of that reader, not a new compiler-origin or runtime claim.

## Results, counterexamples and limits

Seven guests (five ON/two OFF) pass:4279 total instructions,4252original ROM+
27project,811 unique starts,1224reads/930stores,4280code callbacks including
the stopped gate,peak504. The project caller accounts for11stores/8reads;
original code accounts for919stores/1216reads. Five return boundaries contain
`[1,16,1,16,1]`; both output16-byte hashes match their owned sources and the
handle closes with correct final state. No expected-state adjustment followed
the first guest.

Full16 final: R0=result vector`0x022F0280`, R1=0, R2=`0x6000001F`, R3=0,
R4–R11 preserved, IP=`0x022F0250`, SP restored, LR=`0x020D76A4`,
CPSR=`0x2000001F`. Initial R2/R3 are pointers, not the preceding case's cookies.
Close/Send's POP PC returns preserve the last Next/Restore LR residue.
The native calls include5Send/Execute/Release/Wake/Next,16Translate,
27Disable/27Restore,21cached table copies plus two memory payload copies.

Two precompleted32 controls converge to the same full CPU/all17pages/flow/read,
but native MI stores760–763 and837–840 have different preimages. The verifier
rejects input camouflage and deletion of any of these eight writers:18 forged
variants total. OFF still enforces every access and counter with empty observed
ledgers and identical final CPU/pages. Seven runs are four distinct input
fixtures: the first probe duplicates a normal run and OFF repeats its normal
initial state. Two saved-raw verifications pass without a new CPU/compiler.
Eighteen new ROM-free tests cover tiny NARC bounds, archive domain, writer
ownership/replay and CLI/OFF/manifest guards.

The source forecast4279 was independently derived before the arithmetic run;
functional FNT/FAT/owned payload and per-API state checks are separate from that
finite instruction predictor. Backend is Unicorn2.1.4 CPU17, not ARM946 silicon,
timing/cache or interrupt delivery. Host matrices take under1.01s and68MB OS
peak RSS here; no DS speed or memory gain is claimed.

Provenance is documented; assembly binary matching, finite semantic agreement
and isolated activation have their own coverage above. Still unproven: natural
CARD protocol/async/controller/DTCM caller, original C compiler/full-ROM rebuild,
Italian execution, native Thumb NARC parsing/PP consumer and physical SAVE.
No game ROM, save, settings, IDs, ABI or player input is changed. A useful next
case is the actual nonallocating Thumb NARC reader using these qualified APIs,
with a new mixed-mode contract; it is not inferred from these copied bytes.

## Native caller follow-up

The [original NARC reader case](native-fs-memory-narc-source-rom-1.3.2.md)
subsequently joins the real Thumb wrapper/parser to these thirty SDK bodies,
with 6262 original instructions and no project caller. It retains the explicit
memory archive projections and does not qualify natural CARD delivery.
The five-API result above retains its own historical scope.
