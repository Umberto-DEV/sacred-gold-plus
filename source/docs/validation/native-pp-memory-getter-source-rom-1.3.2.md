# Original PP getter through native NARC and filesystem code

`GetMoveAttr(310, MoveAttr_PP)` returns 15 after the original getter loads its
own stack buffer through the complete native NARC/filesystem chain. A second
input changes only the declared memory-source PP byte to 1; the same API then
returns 1. Seven isolated executions pass, with **6,287 original ROM
instructions**, no test caller, service model or runtime host write.

This joins a real scalar consumer to the [original NARC reader](native-fs-memory-narc-source-rom-1.3.2.md).
The archive remains the explicitly configured memory fixture from that case.
Natural CARD delivery, in-game activation, PP-Up arithmetic and Mon setters are
separate questions. See the [owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete ROM composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom).

## Inputs, provenance and compilation boundary

Use your owned exact r4 EN image: 152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`.
Optional current IT readback uses 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both current headers are IPKE/revision 0; presentation language is a separate
property. Fresh readback checks the six new code/data windows in both images;
Italian execution is not claimed. No complete ROM, extracted member, save,
BIOS, capture or personal path is included in this repository.

The candidate source is `src/move.c` in
[ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c) commit
`cb614ad23449d5852b40321dc409c4143872b35c`, SHA-256
`e9adae2d57511a89ec5cc52ebb5741172a5d90123d02d33be66143ddf210e7b2`.
It defines GetMoveAttr, GetMoveTblAttr and LoadMoveEntry. `MoveAttr_PP=5` is
the attribute index; PP occupies byte offset 6 of the member, not offset 5.
The NARC C candidate and reference provenance are recorded by the parent.

Original Metrowerks compiler and Thumb objects remain unavailable. This case
identifies the C recipe and exact installed bytes and checks their finite
valid-input behavior; it does not reconstruct C-to-Thumb compilation. Reuse the
parent's [thirty SDK object recipes and map](native-fs-memory-read-source-rom-1.3.2.md#methods-components-and-recovered-compilation).
No new ARM object or compiler invocation is needed with those authenticated
artifacts retained. A fresh reproduction builds the parent artifacts first
with its documented toolchain and layout checks. The historical project-driver
artifact in that recipe is not mapped or executed here. This bench has no ROM
installer and does not change the complete-ROM build pipeline.

## Physical and logical locations

These six windows are initialized ARM9 bytes. For both current images, ARM9
starts at physical `0x4000`, loads at `0x02000000` and has initialized length
`0x12B8E4`. These intervals are neither overlays nor compressed streams. The
[resource reader](../../features/trainer-strategy/tools/rileggi_pp_memory.py)
compares physical offsets with an independent ndspy ARM9 decode and emits all
span hashes. It hashes the whole ROM as a stream but loads only ARM9.

| Component | Logical interval, end excluded | Physical start | Bytes / starts |
| --- | --- | --- | --- |
| GetMoveAttr | `0x02073314..0x0207332C` | `0x77314` | 24 / 10 |
| LoadMoveEntry | `0x020733B0..0x020733BA` | `0x773B0` | 10 / 5 |
| Attribute dispatch | `0x02073354..0x02073364` | `0x77354` | 16 / 8 |
| PP leaf | `0x02073390..0x02073394` | `0x77390` | 4 / 2 |
| Switch table, data | `0x02073364..0x0207337C` | `0x77364` | 24 / 0 |
| Reader literal, data | `0x020733BC..0x020733C0` | `0x773BC` | 4 / 0 |

This adds 54 code bytes and 25 Thumb starts to the parent's 238-byte NARC
caller. The literal contains the odd Thumb pointer `0x02007509`. The selected
table halfword at `0x0207336E` is the dispatch offset 42. Other attribute leaves,
default, padding and the neighboring GetMoveMaxPP/division path are not admitted
as code. The full table is authenticated, while only its selected halfword is read.

NARC index 11 selects path `a/0/1/1`, filesystem ID 140 and member 310.
The [parent's bounded metadata check](native-fs-memory-narc-source-rom-1.3.2.md#locating-code-and-data)
derives member file offset `0x224C`, physical `0x01095A4C`, length 16.
Original member SHA-256:
`85ac8d2ffc1e263ba41dfed64ea9b07613bd3fe76e8a68ef13e93394179dc5c8`.
The seven native metadata/payload reads still total only 36 owned source bytes.

## Callers, state, resources and ABI

The bench enters the original GetMoveAttr in Thumb/System state with R0=310,
R1=5, declared R2–R12 cookies, SP=`0x023FD000` and an odd return sentinel.
The game caller above that entry is not executed. Its prologue allocates a
24-byte frame containing the native 16-byte buffer at top minus 24 and saves
R4/LR at top minus 8.
LoadMoveEntry tail-calls the original NARC wrapper with R0=that buffer, R1=11,
R2=310, R3=`0x02007509` and LR=`0x02073321`.

The reader creates its own FILE at top minus 136 and parser locals at top minus
160. No host initializes those fields or copies a result between stages.
Combined stack peak is 640 bytes, with a separate 56-byte guard. The destination
is live stack memory; placing a canary inside the reader's frame would corrupt
the fixture. Exact saved-pair addresses and all chronological writes are checked.
There are 18 mapped pages, 73728 bytes, including the new getter code page.

Cached FAT/FNT, root provenance and the three memory-archive input projections
are unchanged from the parent: base `0x0127C820`, native read callback
`0x020D7448` and procedure bits `0x600` cleared. Natural asynchronous CARD
controller/task/completion state remains unqualified. Default reproduction
uses the ROM-derived fixture and needs no private capture. Optional qualified
historical EN resources can be used consistently through `--snapshot`.

After the native reader closes the file, GetMoveAttr dispatches attribute 5
and the original `LDRB` at `0x02073390` reads buffer+6. This is the scalar PP
consumer itself. Unlike the parent's void NARC API residue, R0 here is the
getter's u32 result. Final R0=PP, R1=42, R2=`0x6000001F`, R3=`0x02007509`,
R4–R11 restore their entry cookies, IP=top−8, SP=top, LR=`0x02073329`, CPSR=`0x3F`.

## Instruction qualification and causal test

The [finite PP predictor](../../features/trainer-strategy/test/arm_thumb_pp_oracle.py)
extends the pinned NARC frontend with only BHI, ASR immediate, LDRB immediate,
the two actual high-register ADD words and BX r3/lr. The parent ARM arithmetic
and CPU producer remain unchanged. Reusing the producer with a new frozen
context and byte corpus still gives one uninterrupted `emu_start`; source
segmentation exists only in the arithmetic prediction.

Two PC rules matter. At `0x0207335A`, register-form ADD reads unrounded PC+4
(`0x0207335E`). At `0x02073362`, ADD to PC uses `0x02073366+42` to reach
`0x02073390`, preserving Thumb and NZCV despite an even target. Literal loads
have their separate word-alignment rule. The primary
[ARM Architecture Reference Manual, DDI0100I](https://documentation-service.arm.com/static/5f8dacc8f86e16515cdb865a)
defines these rules in A2.4.3 and ADD(4)/ADD(5). Twenty-six arithmetic tests and
ten owned synthetic CPU kernels qualify the additions before native execution.
The backend is Unicorn 2.1.4 CPU model 17 (Cortex-A15), not an ARM946
timing/cache/interrupt implementation or a measurement of hardware CP15.

The PP1 counterfactual changes exactly one source-memory byte at `0x02312272`
before CPU entry. The owned ROM and original resource receipt remain unchanged.
Its separately identified projected member SHA-256 is
`84184eda6fa58f989bc105b9b9be9c012a5c9fa53836238ad9cedec8a042a67b`.
The native copy must propagate that byte into the actual stack buffer and the
native getter must return 1. Neither R0 nor any SDK response is forced.

Compared with normal PP=15, two read values change: native copy read 1583 and
getter byte read 1734. One native copy store, index 1211, changes its word value.
Final maps differ only at the source PP byte and native buffer PP byte. Final
registers other than R0 and the instruction/access routes are identical. These
differences were predicted before CPU execution. Forged input/scalar claims,
wrong or missing leaf reads and wrong or missing copy stores are rejected:
six forgeries per resource mode, twelve total. They are raw-evidence forgeries,
not additional guest executions or patched ROMs.

## Reproduction with owned inputs

Prepare the [project requirements](../../requirements.txt) in an isolated Python
environment. Readback, prediction and raw verification need ndspy 4.2.0 and
Capstone 5; execution additionally needs Unicorn 2.1.4. Verification imports no
CPU backend and invokes no compiler. Use `-I` with site packages enabled for
verification; `-I -S` hides its required readback dependencies. ROM-free tests
support `-I -S`.

Set `SGP_PP_ROM` to the exact owned EN input, `SGP_PP_OBJECTS` to the parent's
thirty-object JSON mapping, `SGP_PP_RECIPE` to its completed memory-Read recipe,
`SGP_PP_REFERENCE` to the clean source pin and `SGP_PP_WORK` to a fresh private
directory outside `source/`. Every output path below must be new.

```sh
mkdir -p "$SGP_PP_WORK"
.venv/bin/python3 -B source/features/trainer-strategy/tools/rileggi_pp_memory.py \
  --rom "$SGP_PP_ROM" --json "$SGP_PP_WORK/resources.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/qualifica_dispatch_pp.py \
  --json "$SGP_PP_WORK/dispatch-qualification.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/congela_pp_memory.py \
  --rom "$SGP_PP_ROM" --json "$SGP_PP_WORK/input.json"
for phase in prepare matrix; do
  .venv/bin/python3 -B source/features/trainer-strategy/tools/attribuisci_pp_memory.py \
    --mode "$phase" --rom "$SGP_PP_ROM" --objects "$SGP_PP_OBJECTS" \
    --recipe-dir "$SGP_PP_RECIPE" --reference "$SGP_PP_REFERENCE" \
    --input-contract "$SGP_PP_WORK/input.json" --out-dir "$SGP_PP_WORK/$phase"
done
.venv/bin/python3 -I -B source/features/trainer-strategy/tools/attribuisci_pp_memory.py \
  --mode verify --rom "$SGP_PP_ROM" --objects "$SGP_PP_OBJECTS" \
  --recipe-dir "$SGP_PP_RECIPE" --reference "$SGP_PP_REFERENCE" \
  --input-contract "$SGP_PP_WORK/input.json" --raw-dir "$SGP_PP_WORK/matrix" \
  --out-dir "$SGP_PP_WORK/verification"
python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p test_arm_thumb_pp_oracle.py
python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p test_pp_memory.py
```

The [CLI](../../features/trainer-strategy/tools/attribuisci_pp_memory.py) also
offers `--mode probe`; the reader offers `--it-rom`. For historical resources,
pass the same qualified `--snapshot` to reader, freezer and each attribution
phase. Keep source/recipe/toolchain receipts: source drift invalidates a run.
All raw is saved before the verdict, and all artifacts remain private.

## Results, coverage and remaining work

Seven guests cover normal PP, PP1 and observer OFF in two resource modes, with
one initial probe. Each executes 6159 ARM and 128 Thumb instructions, visits
914 unique PCs, performs 1737 reads and 1301 stores, and reaches a 640-byte stack
peak. Five observed runs compare full16 at every PC, data reads, stores with
preimages and all 18 final pages. Two OFF runs retain enforcement and identical
CPU/counters/final maps without observation ledgers. The first native guest
matched the first source forecast without retuning.

Two independent raw-verification runs pass without CPU/compiler. An additional
verification explicitly forbids CPU/assembler imports and compiler subprocesses.
Thirty-four ROM-free tests cover arithmetic, byte/site ownership, saved pairs,
projection types, chronological replay and CLI contracts. Independent reviews
check the original source, new byte windows, mixed ISA and raw evidence.

Proven: documented C candidates, exact installed code/data, retained SDK binary
comparisons, full finite native scalar dependency under the declared memory
archive input and preserved ABI. Still open: original C compiler reconstruction,
full ROM compilation from C, natural game activation/CARD delivery, hardware
CP15/DTCM, Italian execution, PP-Up calculation and Mon setter integration.
This introduces no gameplay fix, memory saving, speedup or save-layout change.

The ignored I/O failures and assert-based malformed-input behavior inherited
from the NARC reader remain potential hardening work, requiring compatible
error semantics and valid/error-path regressions before any game change. The
neighboring MaxPP API needs separate multiplication/division qualification;
adjacent symbols do not provide that proof.

Discover this guide from a repository-only checkout with
`python3 -I -S source/attribution_cases.py show native-pp-memory-getter-source-rom-1.3.2 --json`.
The catalog supplies navigation, not an execution verdict. These public commands,
sources, tests, hashes and limits can be used by developers or coding assistants
with their own inputs; private assistant plans are not prerequisites.

The [complete native MaxPP path](native-maxpp-memory-source-rom-1.3.2.md) now joins the PP getter to its
actual clamp, multiplication, signed division and u8 return. A recovered MSL
assembly recipe compiles to the exact 524 installed division bytes. Declared
PP-Up and source-PP inputs exercise causal native results, with source-bound
raw verification; original Thumb compilation and natural CARD remain open.
