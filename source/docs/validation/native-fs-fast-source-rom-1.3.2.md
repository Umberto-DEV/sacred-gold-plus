# Native OpenFast fields and aggregate lifetime

This continues the [Convert case](native-fs-convert-source-rom-1.3.2.md) through
installed `FS_OpenFileFast`. Native code spills the by-value file identity,
writes three file fields, calls a declared SendCommand backend and sets file
status. FindPath, SendCommand and Seek/Read/Close remain modeled. The game,
ROMs, saves and ABI are unchanged.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Trace the aggregate through caller LDM, callee spill and actual loads. Separate
native file writes from host archive state. Reconstruct each stack interval at
its actual lifetime: the same bytes may hold a dead directory and then new
saved arguments. Verify source/recipe→ELF→installed bytes and ROM→caller→source.
Check flags, conditional effects and restored LR independently. Seek a counter
with correct output but incorrect native status, review raw evidence and record
missing original compiler/state before generalizing the result.

## Il materiale più grezzo da cui partire

Use developer-owned exact inputs and project objects from the
[parent input guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Current EN:152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both headers are `IPKE`, revision0; IT is text-localized. ARM9 loads from ROM
`0x4000` at `0x02000000`. This main-section window has no overlay, compression
or autoload lifetime; initialized ARM9 execution does not establish ARM7/full boot.

Fast occupies `[0x020D8208,0x020D8278)`, physical ROM `0x000DC208`,112 bytes,
28 ARM starts, SHA-256
`465013782ef4760fff5100c626a4ddc63e8611d1517a1b9bc105b23092638bd9`.
The exclusive end starts Open and is excluded. The single BL at `0x020D8240`
targets `FSi_SendCommand` at `0x020D7788`, ARM return `0x020D8244`. There is no
literal pool or embedded data in this body.

The counterpart is `lib/NitroSDK/src/fs/FS_file.c::FS_OpenFileFast` at
[ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
pin `cb614ad23449d5852b40321dc409c4143872b35c`, source SHA-256
`7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f`.
It rejects a NULL archive, assigns `arc` and the fast-open identity, sends
OPENFILEFAST, then sets IS_FILE and clears IS_DIR on success. Original ARM32
headers verify FSFile72, FSFileID8, arc offset8, stat12, argument identity48/52,
command enum6 and status bits16/32. The original SDK compiler/object is missing.

The selected resource remains [custom move310 PP15](native-pp-caller-source-rom-1.3.2.md):
NARC11/FNT `a/0/1/1`, FAT140,16-byte member310, byte6. Raw FAT/FNT/NARC and
ndspy authenticate it. ROMs, extracted retail data, packets, RAM, saves and
BIOS stay private and are not included here.

## I metodi e gli strumenti da usare

The [assembly recipe](../../features/trainer-strategy/sorgenti/fs-fast.S)
and [builder](../../features/trainer-strategy/tools/compila_fs_fast.py)
reconstruct112 exact bytes. The BL uses explicit PC+8 and signed24-bit arithmetic;
independent decoding verifies word `EBFFFD50`, displacement−688 instructions,
target `0x020D7788`. The project ELF loader is unchanged; no external ARM linker
or relocation support is added. Apple Clang21 `clang-2100.4.1.1` was authenticated
by SHA-256 `fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
target `armv5te-none-eabi -mcpu=arm946e-s -marm`. Optional original-header checks
record18 dependencies and the added field/enum assertions. Recovered assembly
identity does not reconstruct the original C compiler invocation.

From repository root, with Python3 dependencies from `source/requirements.txt`
and a compatible Clang, define private input paths as in the parent guide:

```sh
python3 source/features/trainer-strategy/tools/compila_fs_fast.py \
  --uscita "$PRIVATE/fs-fast-recipe" --cc clang --reference "$REFERENCE"
python3 source/features/trainer-strategy/tools/rileggi_fs_fast.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" \
  --language EN --recipe-object "$PRIVATE/fs-fast-recipe/fs-fast.o" \
  --json "$PRIVATE/fs-fast-history.json"
python3 source/features/trainer-strategy/tools/attribuisci_fs_fast.py \
  --rom "$R4" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$TEAMS_OBJECT" --json "$PRIVATE/fs-fast-EN.json.gz"
```

Use corresponding IT inputs and fresh private outputs. Generated manifests
include local paths and stay private. `--readback-only` checks current-code/
object composition without CPU execution. The
[lineage reader](../../features/trainer-strategy/tools/rileggi_fs_fast.py)
parses ELF independently and compares only this new112-byte question across
retail→base1.1→V4→r4. Decoded legacy sections do not imply direct physical offsets,
historical activation or whole-ROM equivalence.

The [verifier](../../features/trainer-strategy/tools/attribuisci_fs_fast.py)
and [adapter](../../features/trainer-strategy/test/fs_fast_bench.py) retain
43 hash-checked source identities. Five new source recipes derive the run,
two context oracles, native oracle and parent case. Four namespace bindings
reuse unchanged code with declared dependencies; parent source pins authenticate
the inherited compositions. End-of-campaign source identity checks reject drift.

```text
custom PP caller → native parser/Init/Open/Convert → modeled FindPath produces ID8
 → native Open LDM passes archive/file ID in R1/R2
 → native Fast spills R0..R3 and R4/LR
   → native loads consume spilled archive and ID
   → native stores FILE.arc and argument identity
   → modeled SendCommand(FILE,6): validates actual native fields, opens host ledger
   → native status read / ORR16 / BIC32 / STR
   → native POP restores LR82A4; BX returns ARM to Open
 → Thumb parser / modeled Seek/Read/Close → native PP setter → complete caller
```

TOP=`0x023BEEC0`; Open ID/SP=`TOP−152`, FILE=`TOP−112`. Fast uses24 bytes:
R0..R3 at `[TOP−168,TOP−152)`, R4/LR at `[TOP−176,TOP−168)`.
These overwrite the dead Convert directory's last8 bytes and its saved16 bytes.
Convert's captured return frame remains exact at its earlier checkpoint; the
later240-byte phase frame includes Fast's reuse. Guest peak stays240/global560
within608; the56-byte actual guard and its8 readonly bytes outside the final608
projection stay unchanged. No new stack, file or name mask is introduced.

Fast receives R0=FILE,R1=opaque archive token `0x021E3654`,R2=file140,R3=0,
SP=ID,LR=`0x020D82A4`. Its two LDRs read the spilled aggregate at SP+12/+16
of the new frame. Native stores write FILE+8=archive, FILE+48=archive,
FILE+52=file140. Send receives R0=FILE,R1=6,R2=140,R3=0,SP=TOP−176,
LR=`0x020D8244`; its declared volatile policy may clobber R1/R2/R3/IP and flags.
It validates the actual three native fields and raw archive identity, then opens
only the host ledger. It writes no guest FSFile or FSArchive bytes.

Native Fast subsequently reads stat, sets bit16, clears bit32 and stores16.
Other56 bytes of the file are preserved. R0 becomes1; R1 becomes native status16
even under backend clobber. R2/R3/IP retain the declared volatile policy. POP
restores R4 and LR=`0x020D82A4`; LR does not retain Send's `0x020D8244`.
SP returns to ID and BX remains ARM. Open then returns to its Thumb continuation.

Command6 is a register argument to the modeled backend. This does not execute
the real command dispatcher or establish its guest command/queue/error fields,
archive object, scheduler or card state. The opaque archive token is never
dereferenced. Native fields and host ledger remain separate evidence categories.

There are197 reader hooks,172 unique native starts,47 native stores and15
modeled boundaries in five categories. Fast adds28 starts and ten stores
(six saved words, four file words). On qualified Unicorn2.1.4 CPU model17,
eight false EQ locations still yield hooks with full16-register state identical
to the next instruction. Their conditional effects are suppressed. This is
verified separately from the parent's false EQ hook and is not hardware timing.
A declared Send BOOL2 control normalizes natively to1; it is not an observed SDK
result2. NULL-archive and true Send-failure branches are attributed statically,
without execution claims in this contract.

The counter shadows only R1 from16 to0 at `0x020D8268`, after actual ORR/BIC,
requiring R0=1,R4=FILE,SP and LR to identify that invocation. Send remains successful
and the host archive stays open. The same STR writes status0; exact240/152/136-byte
views differ in that single word. Model events remain identical, while phase
RAM digests differ. All names, PP/party, seed and whole final RAM remain exact,
with no added name projection. The positive oracle rejects the disguised counter
at the complete native Fast flow. Correct final output therefore does not prove
correct status initialization. This is not an observed SDK failure policy.

Portable tests need no ROM:

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_fast_bench.py -v
```

For [pure receipt replay](../../features/trainer-strategy/test/test_fs_fast_attribution.py),
set `SGP_FS_FAST_ROM_DIR` to authenticated `r4-EN.nds`/`r4-IT.nds` and
`SGP_FS_FAST_REPORT_DIR` to generated `fs-fast-EN.json.gz`/`fs-fast-IT.json.gz`.
Set `SGP_REMATCH_OBJECT_DIR` and `SGP_STRATEGY_OBJECT_DIR` as in the parent guide;
run discovery with `-p 'test_fs_fast*.py'`. Missing private inputs produce
explicit skips, not an exact-ROM verification result.

Documented provenance covers the SDK counterpart and recovered recipe. Binary
correspondence covers112 installed bytes. Finite activation covers the initialized
selected caller with declared lower backends. Native Find/Send/Seek/Read/Close,
original compiler provenance, full archive/card/thread/error state, natural
encounters, full battle, UI, SAVE/cold restart and hardware remain outside.
No gameplay fix, speedup or reclaimed memory is inferred from this attribution.


The final matrix passed20 complete runs,10 per language: four Normal/Plus and
seed positives, one alternate fill, two backend controls, two OFF runs and the
status counter. EN106.845s/553975808 bytes OS peak RSS;
IT109.055s/612646912 bytes. Thirteen portable/replay tests passed with zero skips,
7.832s/721616896 bytes OS peak. These are host validation costs, not game timings.
Independent reviews covered raw/source/recipe, ABI, observer, OFF, counter,
both final languages and public CLI/documentation.

All eight positives preserve the Convert-parent six packets, Trainer data,
seed, PP checkpoints and whole final4MiB RAM hash, with28 extra hooks. Only five
RAM digest fields in the second name's transitions differ; all other name data
remain exact. A digest difference alone does not locate changed bytes. All eight
retail/base1.1/V4/r4 bodies also match the112-byte recovered recipe and the
same signed BL target, using independent ELF readback without CPU execution.
The already closed provider campaigns were not repeated.
