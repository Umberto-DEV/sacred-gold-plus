# Complete cached SeekDir: source, installed bytes and execution

This case follows the retained SDK path `FSi_SeekDirCommand → FSi_ReadTable →
FSi_ReadMemoryCore → MI_CpuCopy8 → return`. All four functions execute their
original ARM instructions, with zero service models or runtime host writes.
CPU, FSFile and stack are explicit isolated fixtures. Authenticated historical
EN filesystem resources and a reproducible ROM-derived fixture are separate
input modes; neither is a captured natural SeekDir caller.

The [owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[previous dispatch case](native-fs-nested-seekdir-source-rom-1.3.2.md) explain
where this callee fits. The latter still stops at SeekDir: this isolated test
has not joined its different input state to that caller.

## Professional checks beyond the minimum

Check both directions: source/recipe → ELF → physical and decoded ROM bytes,
and ROM function/callback → original source and ABI. Separate retained native
SDK code from Plus payloads, data and padding. These functions have no new
installer: the Plus composition retains their bytes. Reassembling them is a
comparison artifact and does not rebuild the complete ROM or the original C.

Seek counterevidence in regional literal pools, callback selection, state,
conditional instructions, alignment and saved registers. Independent review
caught an incorrect predicted residual LR: POP PC restores control flow but
leaves LR `0x020D7494`. Tests also reject a false fresh-directory input, an
invented backend identity, an ON record relabelled OFF, an output directory
inside the public source tree, and a final match with incorrect writer evidence.

## Raw starting material and input identities

Use your own r4 image produced by the [existing complete Plus build](../../README.md).
No ROM, table dump, save, BIOS or private capture accompanies this guide.

| Image | Bytes | SHA-256 |
| --- | ---: | --- |
| r4 EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| r4 IT, byte comparison only | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Both r4 headers are IPKE/revision0; presentation language is a separate identity.
The optional historical resource input is a gzip of precisely4194304 MainRAM
bytes, decompressed SHA-256
`28903b369f17bd56ab12949ec66f60b323839d1bb431d4f8e0bf384d2e026c7e`.
Its producer used the exact EN image above. The reader bounds compressed input
to8MiB and decompressed input to4MiB, streams64KiB chunks and retains only
requested slices. It does not obtain DTCM, full natural entry registers or a
natural stack from MainRAM. A different capture requires a separately qualified
identity and provenance; do not substitute a hash to make this historical claim pass.

For reproduction without that private capture, omit `--snapshot`. The reader
uses tables from your exact ROM and creates a92-byte synthetic ARC with explicit
flag, table addresses, physical backups and memory callback; unused fields are
zero. The receipt marks `natural_state: false`. This mode was also executed and
checked. It reproduces the finite source/byte/execution contract with owned
inputs, while keeping the historical resource provenance separate.

The semantic reference is the clean SDK checkout
[`cb614ad23449d5852b40321dc409c4143872b35c`](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c):
`lib/NitroSDK/src/fs/FS_command_default.c` (SeekDir/ReadTable),
`FS_archive_prefix.c` (ReadMemoryCore), `mi/mi_memory.c` (copy), and original
FS/OS headers. The builder authenticates four source files and18 header
dependencies. Its8-byte private parameter typedef is extracted verbatim and
pinned separately: including all of `nitro.h` requires an unavailable unrelated
generated `fx_const.h`. This is a limited ABI check, not a complete SDK build.

## Methods, addresses and resources

| Component | ARM RAM start | Current physical ROM offset | Extent | SHA-256 |
| --- | --- | --- | ---: | --- |
| SeekDir | `0x020D6BEC` | `0x000DABEC` | 148 code +4 literal | `3b0c0a3721993fdf50396c8cf2102e1ea43f92149f4f763586d919e21d680f81` |
| ReadTable | `0x020D6AA0` | `0x000DAAA0` | 192 | `0119efeea4f6d4bdf200624a7ff9c3cee2790fee1e8f8ea8592420ed4aaebf92` |
| ReadMemoryCore | `0x020D7484` | `0x000DB484` | 24 | `b433aaee1c510f86a113d1fe9b857435b6f615e96df11f285c1e8991d6eae0a0` |
| MI_CpuCopy8 | `0x020D4A50` | `0x000D8A50` | 384 | `369b6f2e559f13da0a9ba7a741ebf8ca3213db866a8f4eb97460809d8b54b86e` |

All752 retained bytes match across retail→inherited base→V4→r4 in both EN/IT
via decoded ARM9/autoload sections. Current physical offsets independently
match. The selected path visits96 distinct ARM starts/384 instruction bytes;
it does not execute every instruction in those752 bytes. The4-byte literal at
`0x020D6C80` is maskFFF, not code. Other components' regional data relocations
remain separate; this result establishes no global address shift.

Natural ARC `0x021E3654` has92bytes and cached flags7. FAT is4104bytes at
`0x023BE580`, SHA-256
`51bb4a3635df58a8bf5d2ee3f33d778e891a23bda1e4be54b75169d9f28b5b0a`;
FNT is2902bytes at `0x023BF588`, SHA-256
`80816c1f6829d388b81d53fa9b5eb5fd65dbef654c8fb03e0735cad714b03afe`.
Their physical offsets are `0x0015F400` and `0x0015E800`. The aligned cache
and backup offsets agree with SDK LoadArchiveTables. Earlier raw callback
records attest table loading through read_func `0x020D84C4`, returning through
`0x020D6BBC`; that is a different callback from table_func `0x020D7484` here.
EN and IT FNT/code agree, but their FAT differs in63 of513 records. No EN
natural ARC/FAT state is transferred to IT; IT execution remains unqualified.

Newer PRET references add useful independent metadata. At
[HeartGold6bf138d](https://github.com/pret/pokeheartgold/tree/6bf138d6035aa6b43d6f8f4132a12df70f86dcec),
`heartgold.us/filesystem.csv` contains384 targets and46 directories.
[`packer.c`](https://github.com/pret/pokeheartgold/blob/6bf138d6035aa6b43d6f8f4132a12df70f86dcec/tools/nitrorom/src/packer.c)
writes root.parent as directory count, start as8×count, and first_file after
ARM9+ARM7 overlays. Header counts129+0 independently give root `(368,129,46)`;
name lengths and directory overhead give FNT2902bytes. Thus root parent46
must not be normalized to0. Platinum shares this packer code: it is not a
second independent oracle or a regional donor. New SDK wraps are not materialized
in those reference clones and do not replace the authenticated older SDK.

### Fixture, ABI and activation conditions

The bank maps ten synthetic4KiB pages, initiallyA5, then overlays authenticated
code/resources and explicit input objects. FSFile is72bytes at `0x022F0000`,
guarded by16bytesD3 on each side; SP starts at `0x023FD000`, with72-byte frame
and56-byte lower guard. These arenas are disjoint from ARC/code/FAT/FNT and
are not claims of free game RAM. The old fixture FILE/stack intersects the
natural FAT and is rejected by the overlap gate.

FILE.arc is at+8, arg.seekdir.pos at+48, prop at+32. The explicit status is
45 decimal (`0x2D`), command4 and error2; none is read or changed by this
callee. Directory argument is `{ARC,own_id,index0,pos0}`. Other FILE bytes are
zero except initial16-byte property poisonA5. Full input page hashes and
R0–R14/CPSR are frozen before the first new predictor/compiler/guest; PC is
recorded separately. A later re-export changed only freezer source identity
for an output guard/comment, with all six complete fixture records unchanged.

BL6C20 enters ReadTable with `{arc,pos}` on the stack. BLX6ACC selects the real
ARC.table_func; BL7490 enters Copy. The native callback copies8 bytes and
returns SUCCESS0, so ReadTable's async/IRQ/Sleep path is unreachable here.
ARC.flag goes7→207→7, param.pos advances8, and original POP PC returns to a
synthetic sentinel at `0x020D749C`, stopped before execution. Its zero sentinel
bytes are fixture policy, not authenticated next-function instructions.

Root output is `{arc=ARC,own_id0,index129,pos=0x023BF6F8,parent46}`. Directory1
uses the next authentic record `(431,129,0xF000)` and produces
`{ARC,own_id1,index129,pos=0x023BF737,parent0}`. Final R0=0,R2=0,R3=0,
R1=raw parent46/F000, R4–R11 preserved, R12=FILE+32, SP restored,
LR=`0x020D7494`, CPSR=`0x6000001F`. Do not restore LR to the sentinel on the host.

### Reproduce with owned inputs

Requirements: Python3.9+ standard library for resource reading/freezing, existing
Unicorn2.1.4 for execution, and the authenticated Apple Clang21 production compiler
SHA-256 `fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
The SDK reference must be clean at the pin above. These commands use no private
report, capture, save or ancestor ELF. Keep outputs outside `source/`.

```sh
# Set these to your own Python environment and private input/output locations.
export PYTHON=/path/to/venv/bin/python3
export ROM_EN=/private/path/to/your-exact-r4-EN.nds
export SDK_REFERENCE=/private/path/to/pinned-SDK-reference
export CASE_OUT=/private/path/to/new-case
mkdir "$CASE_OUT"

"$PYTHON" -B source/features/trainer-strategy/tools/rileggi_fs_cached_resources.py \
  --rom "$ROM_EN" --json "$CASE_OUT/resources.json"
"$PYTHON" -B source/features/trainer-strategy/tools/congela_fs_cached_seekdir.py \
  --rom "$ROM_EN" --json "$CASE_OUT/input.json"
"$PYTHON" -B source/features/trainer-strategy/tools/compila_fs_cached_seekdir.py \
  --reference "$SDK_REFERENCE" --uscita "$CASE_OUT/recipe"
"$PYTHON" -B source/features/trainer-strategy/tools/attribuisci_fs_cached_seekdir.py \
  --mode prepare --rom "$ROM_EN" --recipe-dir "$CASE_OUT/recipe" \
  --reference "$SDK_REFERENCE" --input-contract "$CASE_OUT/input.json" \
  --out-dir "$CASE_OUT/prepare"
"$PYTHON" -B source/features/trainer-strategy/tools/attribuisci_fs_cached_seekdir.py \
  --mode matrix --rom "$ROM_EN" --recipe-dir "$CASE_OUT/recipe" \
  --reference "$SDK_REFERENCE" --input-contract "$CASE_OUT/input.json" \
  --out-dir "$CASE_OUT/matrix"

"$PYTHON" -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_cached*.py' -v
python3 -I -S -B source/attribution_cases.py show native-fs-cached-seekdir-source-rom-1.3.2 --json
```

`prepare` invokes no CPU or compiler. `probe` runs root only; `matrix` runs root,
root OFF, root with precompleted initial property, and directory1. To reproduce
the historical resource mode, pass the exact qualified gzip with `--snapshot`
to the resource reader, freezer and every attribution command. Do not mix its
contract with the ROM-derived mode. Optional reader `--it-rom` compares only
code/FNT/FAT identities; it is not an Italian execution switch.

Each command requires fresh output. The production compiler remains pinned;
a different compiler requires separate qualification rather than a skipped
byte check. Bound work to180s/1GiB RSS/2MiB logs,1GiB planned disk peak and
at least10GiB free afterward. The actual guest cap is256 starts/1second.

For independent readback, read only the ARM9 region selected by the512-byte
header and construct `ndspy.code.MainCodeFile(arm9_bytes, arm9_ram_address)`.
For each table row, find the decoded section containing its complete extent
and compare that slice's SHA-256. Compare the same extent via
`arm9_rom_offset + address - arm9_ram_address` only when uncompressed current
mapping has been independently established. Do not apply this physical formula
to a compressed retail component or treat `.text`/pool bytes as all instructions.
The ELF reader rejects unexpected allocations, external symbols and ARM CALL
relocations; recovered BL words use explicit signed PC+8 expressions.

### Results, counterproofs and remaining gaps

Nine guests passed: first root probe, then two four-run matrices for the two
resource modes. Each has100native/96unique/27stores/35reads/101callbacks including
the stopped gate, peak72. Seven ON records contain full16 context at every
native instruction and exact ordered read/write/preimage ledgers; two OFF
records retain enforcement/counters/final pages without observation projections.
All40KiB mapped pages are checked against the source result, including unused
bytes, full ARC, FAT/FNT, code, file guards and lower stack guard.

In each resource mode, precompleted_prop changes only the initial16 property
bytes. Final full CPU/pages, read ledger and context flow converge; store
preimages differ at exactly four events (three STM words and final parent).
The six native property stores remain required. Camouflaging the projected
initial record as the normal one fails specifically on native stores, even
with the same final pages. Deleting any one of the six property stores also
fails. OFF returns exactly the same full CPU/pages within its mode. The two
resource modes are judged against their own full inputs; unused ARC differences
are preserved, not masked for a false whole-state equivalence.

19 ROM-free tests passed without skips. Independent review checks source oracle,
raw records, ABI, resources, region identities, frozen inputs and false-success
controls. The source-level tests do not stand in for the recorded guest runs.
The native backend is explicitly CortexA15 in Unicorn, used for the permitted
ARMv5 instructions; this establishes neither ARM946 timing/cache/IRQ behavior
nor Nintendo performance.

Documented provenance and recovered binary matching are established. Semantic
and isolated activation coverage is exactly the two directory inputs and declared
property projection. Natural FindPath/SeekDir caller, DTCM entry, other copy
alignments/sizes, failure/async/card/thread routes, Italian natural state,
original Metrowerks C rebuild and physical SAVE/cold restart remain open.
No game change, saved-memory gain or speedup is claimed. The reusable improvement
is the bounded resource/overlap gate, portable ROM-derived input, independent
metadata check and source/byte/causal verification for subsequent callees.

The [complete FindPath follow-up](native-fs-cached-findpath-source-rom-1.3.2.md)
now uses these native callees in a whole four-segment pathname search. It adds
qualified1/2-byte copy routes and their neighboring-byte checks. Its new RUNNING
input and larger frame remain a separate isolated context, not a natural-caller
upgrade of this SeekDir case.
