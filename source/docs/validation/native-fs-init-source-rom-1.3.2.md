# Native SDK file initialization inside the PP caller

This case extends the [custom move PP caller](native-pp-caller-source-rom-1.3.2.md)
by executing the installed `FS_InitFile` ARM leaf in the same CPU. The remaining
Open, Seek, Read and Close services stay explicit models. The ROM, game source,
save layout and installation are unchanged.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Derive the container from actual types and caller instructions, rather than a
`sizeof` comment. Verify source→compiled recipe→installed readback and
ROM→leaf→caller→source. Record selective initialization, preserved bytes,
volatile registers, interworking and the exact lifetime of borrowed stack data.
Seek counterproofs where the final PP or party is correct despite missing
initialization. Review addresses, ABI and the rejection oracle independently.

## Il materiale più grezzo da cui partire

Use your own exact r4 inputs and retained project ELF objects from the
[parent input guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
EN is152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT is159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both have the same installed leaf at RAM`0x020D7F98..0x020D7FC0`, physical
ROM`0x000DBF98`,40 bytes, SHA-256
`131f15b7db06da746cb03744ffda8f5453b1c6c2fbdf8f0dacab41326e10421f`.
The instruction at the exclusive end belongs to the next function.
Keep ROMs, extracted bytes, full RAM, Pokémon packets, saves and BIOS private.

The source counterpart is `lib/NitroSDK/src/fs/FS_file.c::FS_InitFile` in
[ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
pin`cb614ad23449d5852b40321dc409c4143872b35c`. Source file SHA-256 is
`7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f`.
Modern header`lib/include/nitro/fs/file.h` SHA-256 is
`4e874cfbaa77f546b6f69473ef8bd24afdaab082c5a99f0bb16c37d41f24598f`.
The builder checks a clean reference checkout and records the actual dependency
headers and hashes. It does not copy these headers into the public repository.

Under ARM32, pointers/u32/BOOL/enums are4 bytes. FSFile is72 bytes, alignment4:

| Fields | Offset | Bytes |
| --- | --- | --- |
| link.prev, link.next | 0,4 | 8 |
| archive, status, command, error | 8,12,16,20 | 16 |
| queue head, tail | 24,28 | 8 |
| property union | 32 | 16 |
| argument union | 48 | 24 |

The largest argument is `FSFindPathInfo`: position12,path pointer4,BOOL4,result
pointer4. Compiled assertions against the original headers verify these sizes,
field offsets, queue, unions and `FS_COMMAND_INVALID=14`. The header's size0x50
comment does not describe those declarations. A host macOS`sizeof(u32)` would
give the wrong ABI because the reference typedef uses`unsigned long`.

The installed leaf is ten ARM instructions: zeroR2; store zero at file offsets
0,4,28,24,8; loadR1=14; store it at16; store zero at12; `BX LR`.
Thus it assigns28 bytes and preserves44 bytes, including error, property and
argument storage. It has no load, literal pool, branch call, global access or
stack allocation. `OS_InitThreadQueue` is inline here; this leaf does not
establish scheduler, filesystem availability or native Open behavior.

## I metodi e gli strumenti da usare

The [recovered assembly recipe](../../features/trainer-strategy/sorgenti/fs-init.S)
and [builder](../../features/trainer-strategy/tools/compila_fs_init.py) emit the
exact40 bytes with Clang targeting ARMv5TE/ARM946E-S in ARM mode. This recipe is
an attribution artifact with no installer. It reconstructs the byte sequence,
not the original compiler invocation. The authenticated local compiler was
Apple Clang21`clang-2100.4.1.1`, executable SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
Use an available compatible Clang; the body hash is the success criterion.

The optional C counterpart is the unmodified function body extracted from the
pinned source and compiled against the original headers at`-O2`. That Clang
emission is also40 bytes but SHA-256
`ec6cac6c726eb1e41384d672a447428823e1036a70675c2b872278b17cbfdd6b`.
It assigns the same seven fields but changes store order and volatile residues
(R1=0,R2=14). It is not a binary match or a replacement for the installed leaf:
the surrounding caller exposes R2 at the next modeled boundary. The builder
reports the difference and does not infer semantic equivalence automatically.

From the repository root, with Python3 and the project's ndspy, Capstone and
Unicorn dependencies available:

```sh
python3 source/features/trainer-strategy/tools/compila_fs_init.py \
  --uscita "$PRIVATE/fs-init-recipe" --cc clang --reference "$REFERENCE"

python3 source/features/trainer-strategy/tools/rileggi_fs_init.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" \
  --language EN --recipe-object "$PRIVATE/fs-init-recipe/fs-init.o" \
  --json "$PRIVATE/fs-init-history.json"

python3 source/features/trainer-strategy/tools/attribuisci_fs_init.py \
  --rom "$R4" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$TEAMS_OBJECT" --json "$PRIVATE/fs-init-EN.json.gz"
```

Set the variables to your local inputs. Output paths must be fresh and outside
`source`; generated ELF/manifests contain local paths and remain private.
`--readback-only` verifies the composed exact-code/object identity without
executing a CPU. Repeat with IT and its corresponding input objects. The
lineage reader authenticates four inputs separately, compares only this40-byte
leaf and independently reads ELF section arithmetic. Legacy compressed/autoload
images use decoded sections without an invented physical offset. All eight
tested retail/base1.1/V4/r4 leaves match the current body; this does not prove
historical activation or whole-image equivalence.

The [caller verifier](../../features/trainer-strategy/tools/attribuisci_fs_init.py)
and [adapter](../../features/trainer-strategy/test/fs_init_bench.py) authenticate
the immutable PP parent and exact source edits. Earlier native readers and
their raw providers retain their qualified contracts. Only the selected custom
move310 PP read after CreateMon returns receives native Init.
Execution retains the parent's qualified Unicorn CPU model17. The assembler's
ARM946E-S target does not establish ARM946 hardware timing or microarchitecture
coverage in that emulator model.

For this occurrence, PP destination/TOP=`0x023BEEC0`, parserSP=TOP−136,
file=SP+24=`0x023BEE50`. The file72 ends atTOP−40, exactly where the parser's
saved24-byte PUSH area begins. Its local96 bytes are metadata24+file72;
the wrapper adds16 bytes. Treating the file as80 would overlap two saved words.
No new guest buffer or stack projection is introduced.

The Thumb BLX at`0x02007346` calls`0x020D7F98` with LR`0x0200734B`; `BX LR` returns
to Thumb`0x0200734A`. The full entry/return vectors are checked. R0 remains the
file pointer as a void residue; R1 becomes14,R2 becomes0; R3–R12,SP,LR and NZCV
are preserved. The caller restores R0/R1 for Open but leaves R2=0. R2 is an
observed volatile residue, not a third Open API argument. The previous
Init model preserved310, so accepting its old register transcript would be wrong.

The observer borrows the same CPU without a guest write. Host handle bookkeeping
occurs only at the actual native return; no fake Init event or initialization
backend remains. Native parser instructions plus Init give113 native fetch
locations and14 modeled FS boundaries,127 hooks total. Ordered native writes
increase17→24. Init adds no stack depth: reader136/global456,guard56/global512;
the complete caller remains within its608-byte bound.

The oracle derives the Init frame from the reader's actual preimage plus the
sixteen prefix stores, then applies the seven actual assignments. It checks
both full136-byte frames, all44 preserved file bytes, instruction/register
sequence, store PC/width/address/before/value/full registers, and the actual
Open R2. Self-consistent snapshots alone are insufficient: changing the same
unused frame byte before and after is a tested rejection. Guard and borrowed
output16/upper16 checks remain inherited from the PP caller.

OFF runs still execute Init and all28 guest bytes. Only its store log is
disabled. No file or stack bytes enter a new mask; the inherited1124-byte
canary/dead-heap projection remains exact. Native output, ABI and file effects
must agree OFF/ON.

Two synthetic counterproofs act only at the command store: skip the ARM STR by
a legal PC change, or change R1 from14 to0 immediately before it. Both keep the
raw code and resource unchanged. The code-hook count can stay127 even when a
store is skipped: fetching a hook is not proof that the instruction ran. The
store transcript and file postimage must reject the disguised counter despite
correct PP and party output. The four opaque FS models do not prove what native
Open would do with this malformed file.

Portable checks need no ROM:

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_init_bench.py -v
```

For the [pure receipt replay](../../features/trainer-strategy/test/test_fs_init_attribution.py),
set`SGP_FS_INIT_ROM_DIR` to a directory containing your authenticated
`r4-EN.nds`/`r4-IT.nds`, and`SGP_FS_INIT_REPORT_DIR` to the generated
`fs-init-EN.json.gz`/`fs-init-IT.json.gz` reports. Set`SGP_REMATCH_OBJECT_DIR`
and`SGP_STRATEGY_OBJECT_DIR` as described in the parent input guide (subdirectories
`public-build-EN`/`public-build-IT` and`build-EN`/`build-IT` respectively).
Then run discovery with`-p 'test_fs_init*.py'`. Without private inputs, receipt
tests explicitly skip; this does not count as an exact-ROM verification.

The final matrix has20 complete executions,10 per language: four Normal/Plus
and seed positives, one alternate stack fill, one remaining-FS volatile-clobber
control, two OFF pairs and both counters. EN completed in106.536s with OS peak
RSS597114880 bytes; IT108.308s/584122368 bytes. These are host verification
costs, not game timings. Ten portable/replay tests passed without skips,
8.670s/719962112 bytes OS peak. Separate independent reviews checked raw bytes,
layout/recipe, caller ABI, counters and captured final observations.

Across all eight final positives, party packets, Trainer data, seed and full
final4MiB RAM hashes match the corresponding parent PP observation, with nine
additional hooks. The Init phase RAM hash changes because the native leaf now
writes real fields. The command counters also retain correct PP/party output
but fail the source-bound initialization oracle. Equality at caller return
does not erase the distinct execution and lifetime evidence.

The case remains a finite initialized-host observation. Original SDK build
provenance, native Open/Seek/Read/Close and their globals/card/error paths,
natural activation, whole battle, UI, SAVE/cold restart and hardware are separate
questions. No gameplay correction, speedup or memory recovery is claimed.
