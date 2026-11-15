# Native Seek and FAT-backed property inputs

This extends the [Close case](native-fs-close-source-rom-1.3.2.md) through the
five selected `FS_SeekFile` calls in the same PP caller CPU. The native function
needs file properties that the former opaque backend did not populate. A
**declared field projection** now supplies those properties from authenticated
ROM FAT data and advances position after modeled reads. This does not reconstruct
the whole dispatcher or native FSArchive. No game, ROM, save or ABI changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Attribute the data read by a function as carefully as its instructions. Establish
whether coordinates are physical ROM addresses or archive-relative positions.
Separate source-derived model inputs from native writes, and record known
excluded effects. Verify source/recipe→ELF→ROM and ROM→caller→source; trace each
native position into its actual read consumer. Keep admitted code distinct from
executed starts. Seek an alternative origin with identical final output, and
review ABI, frame ownership, flag propagation and replay falsifiers independently.

## Il materiale più grezzo da cui partire

Use developer-owned exact inputs and project objects from the
[parent input guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Current EN:152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both headers are `IPKE`, revision0; IT is text-localized. ARM9 loads from ROM
`0x4000` at `0x02000000`. This main-section body has no overlay, compression
or autoload lifetime. Initialized ARM9 execution does not establish ARM7/full boot.
ROMs, extracted retail data, RAM, packets, saves and BIOS remain private.

Seek occupies `[0x020D83DC,0x020D8448)`, physical ROM `0x000DC3DC`,108 bytes,
27 ARM starts, SHA-256
`99e8a8db572238f5c2aa23d35ddfe505843277a0623dedfe207c2d5872236747`.
The exclusive end begins ChangeDir and is excluded. There are seven internal
branches, no BL, stack frame, literal pool or embedded data in this body.

The counterpart is `lib/NitroSDK/src/fs/FS_file.c::FS_SeekFile` at
[ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
pin `cb614ad23449d5852b40321dc409c4143872b35c`, file SHA-256
`7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f`.
It adds top/current/bottom according to SET/CUR/END, clamps using signed
comparisons and stores position. ARM32 header assertions verify FSFile72,
properties own_id32/top36/bottom40/pos44 and four-byte seek mode SET0/CUR1/END2.
The historical size80 comment is not a layout proof. Original compiler/object
provenance remains unavailable.

The resource is [custom move310 PP15](native-pp-caller-source-rom-1.3.2.md):
NARC11/FNT `a/0/1/1`, FAT file140,16-byte member310, byte6. The current FAT table
is at ROM `0x0015F400`, its file140 row at `0x0015F860`: top=`0x01093800`,
bottom=`0x0109645C`, length11356, in both exact images. The tool reauthenticates
FNT/FAT/NARC identity, row bounds and whole-file hash rather than trusting these
numbers. Manual archive arithmetic and ndspy checks remain inherited.

The same pinned SDK's `FS_command_default.c::FSi_OpenFileFastCommand` reads the
FAT entry and dispatches OpenDirect; `FSi_OpenFileDirectCommand` assigns
own_id/top/bottom/pos. `FS_rom.c` supplies ROM archive base0 and passes the read
position to CARD directly. These sources justify physical FAT coordinates for
the declared default-ROM input model. The opaque archive token itself is not
observed native archive state.

## I metodi e gli strumenti da usare

The [assembly recipe](../../features/trainer-strategy/sorgenti/fs-seek.S)
and [builder](../../features/trainer-strategy/tools/compila_fs_seek.py) reproduce
108 exact bytes with internal branches resolved by the assembler, without BL,
external linker or relocation changes. Apple Clang21 `clang-2100.4.1.1` was
authenticated by SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
target `armv5te-none-eabi -mcpu=arm946e-s -marm`. Optional layout checks record
18 original headers. Recovered assembly identity is distinct from reconstructing
the original SDK compiler invocation.

From repository root, use Python3 dependencies in `source/requirements.txt`
and a compatible Clang. Define private input paths as in the parent guide:

```sh
python3 source/features/trainer-strategy/tools/compila_fs_seek.py \
  --uscita "$PRIVATE/fs-seek-recipe" --cc clang --reference "$REFERENCE"
python3 source/features/trainer-strategy/tools/rileggi_fs_seek.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" \
  --language EN --recipe-object "$PRIVATE/fs-seek-recipe/fs-seek.o" \
  --json "$PRIVATE/fs-seek-history.json"
python3 source/features/trainer-strategy/tools/attribuisci_fs_seek.py \
  --rom "$R4" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$TEAMS_OBJECT" --json "$PRIVATE/fs-seek-EN.json.gz"
```

Use corresponding IT inputs and fresh private outputs. Generated manifests
contain local paths and remain private. `--readback-only` verifies current
composition and geometry without CPU execution. The
[lineage reader](../../features/trainer-strategy/tools/rileggi_fs_seek.py) parses
ELF independently and compares only this new108-byte question across
retail→base1.1→V4→r4. Decoded legacy sections do not imply a direct physical
offset, whole-image equivalence or historical activation.

The [verifier](../../features/trainer-strategy/tools/attribuisci_fs_seek.py)
and [adapter](../../features/trainer-strategy/test/fs_seek_bench.py) authenticate
47 source identities. Seven recipes derive the run, four context oracles,
OFF oracle and native oracle; five namespace bindings reuse unchanged parent
code. A buried Init count is changed from15 to10 by an authenticated derivative,
with its seven-store/frame checks retained. No parent source file is changed.

The new model effects are deliberately limited:

| Point | Explicit model write | Source/data basis |
| --- | --- | --- |
| After modeled SendOpen6 | FILE+32,16 bytes: file140,physical top,bottom,initial pos=top | Raw FAT; default OpenFast→OpenDirect property assignments |
| After each successful modeled Read | FILE+44,4 bytes: top+actual relative cursor | Default ReadCommand position increment; exact delivered bytes |

There are eight projection events/11 word writes, separate from native stores,
raw payload copies and modeled Find ID8. The full handlers also rewrite argument
unions, command/error/stat/queue fields and perform dispatcher/thread/card work.
Those known effects are **excluded** here. The previous ARC/file-id argument
bytes remain synthetic. This is caller-relevant property input/output semantics,
not complete Send/Read field-state equivalence or native filesystem execution.

The producer never assigns an expected table position to simulate a Seek. At
native return it reads the actual guest position and sets the host relative
cursor to `pos−top`. Read requires that guest/host positions agree, delivers the
original raw slice, then advances the projected word. Reads must complete the
whole request, remain within the file, avoid overlapping FSFile and leave that
file unchanged before the explicit position update. Every frame transition is
checked; no extra file or stack mask hides the model writes.

```text
native Init/Open/Convert/Fast → modeled Find/SendOpen6
 → modeled property input16 from exact FAT
 → native Seek SET writes physical pos
 → modeled Read consumes actual pos, copies raw bytes, advances projected pos4
 → repeat through five Seek and seven Read occurrences
 → native Close → PP getter/setter → complete six-Mon caller
```

The relative timeline is:

| Seek target | Position before Seek | Read slices following it |
| --- | --- | --- |
| 12 | 0 | 12,2 bytes |
| 20 | 14 | 20,4 bytes;24,2 bytes |
| 3800 | 26 | 3800,4 bytes |
| 2508 | 3804 | 2508,4 bytes;2512,4 bytes |
| 8780 | 2516 | 8780,16 bytes |

Guest positions add physical top to these values; final cursor is8796. All
addresses and additions in this finite domain stay below2³¹ and within the
file. No negative-offset, END, invalid-origin, overflow or active-clamp behavior
is claimed observed. Their code/source correspondence is static here.

Seek receives R0=FILE,R1=relative offset,R2=SET,R3/IP as actual volatile residues,
SP=TOP−136 and the caller's Thumb LR. It uses no stack frame or lower call.
It returns R0=1,R1=physical position,R2=bottom, preserves R3/IP and saved registers,
and returns Thumb through BX LR. Incoming NZCV are recorded, not source-attributed:
the first unconditional CMP overwrites all four before using a condition.
Only that entry permits their ABI domain; Q/T/mode remain checked. Every later
flag and register vector follows the native instructions exactly. In-range
returns have CPSR=`0x8000003F` from the signed comparison with bottom.

On qualified Unicorn2.1.4 CPU model17, each SET call observes14 starts, including
false MOVLT/MOVGT hooks with no register effect. The27 decoded starts are admitted;
only14 distinct Seek locations execute across the five SET calls. The complete
reader has277 hooks,201 unique starts and57 native stores: five more position
stores than the parent. Five opaque Seek calls disappear, leaving10 modeled
events in three categories: Find, Send and Read. Guest peak240/global560,
actual guard56, extra8 readonly bytes and final608 projection remain unchanged;
the inherited heap-only OFF projection remains1124 bytes.

The counter changes only the first origin from SET0 to CUR1 before CMP, retaining
the actual preshadow caller vector. Initial pos equals top, so CUR and SET
produce the same target, return ABI, native store values, models, property
projections, phase/final RAM, PP flow, names and party. CUR executes16 starts
instead of14; the reader has279 hooks and206 unique starts, two more hooks and
five additional locations. The disguised counter fails the positive SET caller
ABI check. This finite equivalence does not make CUR interchangeable when
position differs from top, or establish an SDK failure.

Two replay false successes were rejected before the first CPU query. Projection
registers now require unsigned32 values, including CPSR. The last Read's actual
full16 vector is linked to Close entry by the caller's ADDsp/BLX effects: only
R0 becomes FILE, LR becomes `0x02007409` and T clears; NZCV are preserved. This
prevents incompatible snapshots from being accepted without forcing arbitrary
flags. It is an oracle linkage, not a CPU register bridge.

Portable tests need no ROM:

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_seek_bench.py -v
```

For [pure receipt replay](../../features/trainer-strategy/test/test_fs_seek_attribution.py),
set `SGP_FS_SEEK_ROM_DIR` to authenticated `r4-EN.nds`/`r4-IT.nds` and
`SGP_FS_SEEK_REPORT_DIR` to generated `fs-seek-EN.json.gz`/`fs-seek-IT.json.gz`.
Set `SGP_REMATCH_OBJECT_DIR` and `SGP_STRATEGY_OBJECT_DIR` as in the parent guide;
run discovery with `-p 'test_fs_seek*.py'`. Missing private inputs yield explicit
skips, not exact-ROM verification.

Documented provenance covers the SDK counterparts and recovered recipe. Binary
correspondence covers108 installed bytes. Finite activation covers the selected
initialized caller with the declared property projection. Original compiler,
native Find/Send/Read, other dispatcher fields and native archive/card/thread/
error state, natural encounters, full battle, UI, SAVE/cold restart and hardware
remain outside. No gameplay fix, speedup or reclaimed memory is inferred.


The final matrix passed20 complete runs,10 per language: four Normal/Plus and
seed positives, one alternate fill, two backend controls, two OFF runs and the
first-CUR counter. EN107.716s/595984384 bytes OS peak RSS;
IT109.353s/614121472 bytes. Sixteen portable/replay tests passed with zero skips,
7.037s/725663744 bytes OS peak. These are host verification costs, not game timings.
Independent reviews covered source/raw/recipe, ABI, observer, OFF, counter,
both final languages and public CLI/documentation.

All eight positives preserve the Close-parent six packets, Trainer data, seed,
all names, complete PP flow/store/checkpoint and whole final4MiB RAM hash, with
65 extra hooks. Phase RAM differs because native position fields are now supplied
and updated. All eight retail/base1.1/V4/r4 bodies match the108-byte recovered
recipe using independent ELF readback without CPU execution. The lineage reader
reports no BL targets; the separate recipe qualification checks seven internal
branches. Earlier provider campaigns were not repeated.

The counter switches the first origin to CUR while initial position equals top.
It preserves every modeled event, property projection, native store, phase RAM,
final RAM, PP flow and name, but takes two additional hooks and five additional
unique starts. The caller ABI oracle rejects it even when relabeled positive.
This is a finite path counterexample, not general SET/CUR equivalence.
