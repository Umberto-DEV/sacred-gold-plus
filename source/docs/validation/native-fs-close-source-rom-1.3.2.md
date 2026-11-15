# Native Close cleanup and residual return state

This extends the [OpenFast case](native-fs-fast-source-rom-1.3.2.md) through
installed `FS_CloseFile`, completing the selected file's native wrapper lifetime.
FindPath, SendCommand, Seek and Read remain explicit models. Two Send calls use
the same address with distinct commands and state. No game, ROM or save changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate host closure from native field cleanup. Follow source/recipe→ELF→ROM
readback and ROM→function→caller→source. Distinguish repeated dispatcher calls
by command, frame, ABI and lifetime. Trace residual LR, R1 and flags through
actual return instructions. Reconstruct stack reuse at each checkpoint and
require a store transcript even when a value is unchanged. Seek a counter with
correct final output but missing archive cleanup; review raw evidence and
record original compiler, native filesystem and activation gaps explicitly.

## Il materiale più grezzo da cui partire

Use developer-owned inputs and project objects from the
[parent input guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Current EN:152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both headers are `IPKE`, revision0, including text-localized IT. ARM9 loads
from ROM `0x4000` at `0x02000000`. This main-section body has no overlay,
compression or autoload lifetime. ARM7/full boot are outside this initialized
ARM9 contract. ROMs, extracted retail data, RAM, packets, saves and BIOS stay
private and are not supplied by the repository.

Close occupies `[0x020D82C0,0x020D82FC)`, physical ROM `0x000DC2C0`,60 bytes,
15 ARM starts, SHA-256
`b6264f39c82988fab2b720bff3277219d7d9bb14d4ed0abe768d4f1f561b2e26`.
The exclusive end starts WaitAsync and is excluded. There is no literal pool
or embedded data in the60-byte body. BL at `0x020D82CC` calls SendCommand
`0x020D7788`, ARM return LR=`0x020D82D0`.

The counterpart is `lib/NitroSDK/src/fs/FS_file.c::FS_CloseFile` at
[ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
pin `cb614ad23449d5852b40321dc409c4143872b35c`, source SHA-256
`7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f`.
It sends CLOSEFILE, then clears `arc`, assigns INVALID and clears IS_FILE/IS_DIR
on success. ARM32 header assertions verify FSFile72, arc offset8, stat12,
command16, CLOSEFILE8, INVALID14 and status bits16/32. Original compiler/object
provenance is unavailable.

The selected resource remains [custom move310 PP15](native-pp-caller-source-rom-1.3.2.md):
NARC11/FNT `a/0/1/1`, FAT140,16-byte member310, byte6. Raw FAT/FNT/NARC and
ndspy authenticate selection. The model exposes a whole archive; native parser
instructions choose and read the member before Close.

## I metodi e gli strumenti da usare

The [assembly recipe](../../features/trainer-strategy/sorgenti/fs-close.S)
and [builder](../../features/trainer-strategy/tools/compila_fs_close.py)
reconstruct60 exact bytes. The single BL uses explicit PC+8 and signed24-bit
arithmetic: word `EBFFFD2D`, displacement−723 instructions, target `0x020D7788`.
The qualified project ELF loader remains unchanged, with no external ARM linker
or new relocation handling. Apple Clang21 `clang-2100.4.1.1` was authenticated
by SHA-256 `fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
target `armv5te-none-eabi -mcpu=arm946e-s -marm`. Optional layout compilation
records18 original header dependencies and the added CLOSEFILE8 assertion.
This recovered assembly match does not reconstruct the original SDK compiler.

From repository root, with Python3 dependencies in `source/requirements.txt`
and a compatible Clang, define private input paths as in the parent guide:

```sh
python3 source/features/trainer-strategy/tools/compila_fs_close.py \
  --uscita "$PRIVATE/fs-close-recipe" --cc clang --reference "$REFERENCE"
python3 source/features/trainer-strategy/tools/rileggi_fs_close.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" \
  --language EN --recipe-object "$PRIVATE/fs-close-recipe/fs-close.o" \
  --json "$PRIVATE/fs-close-history.json"
python3 source/features/trainer-strategy/tools/attribuisci_fs_close.py \
  --rom "$R4" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$TEAMS_OBJECT" --json "$PRIVATE/fs-close-EN.json.gz"
```

Use corresponding IT inputs and fresh private outputs. Generated manifests
contain local paths and stay private. `--readback-only` verifies current-code/
object composition without CPU execution. The
[lineage reader](../../features/trainer-strategy/tools/rileggi_fs_close.py)
parses ELF independently and compares only this new60-byte question across
retail→base1.1→V4→r4. Decoded legacy sections do not imply a direct physical
offset, whole-ROM equivalence or historical activation.

The [verifier](../../features/trainer-strategy/tools/attribuisci_fs_close.py)
and [adapter](../../features/trainer-strategy/test/fs_close_bench.py) authenticate
45 source identities. Three source recipes derive the run, native oracle and
parent case; two namespace bindings retain unchanged code with declared
dependencies. Immutable parents retain earlier source recipes and contracts.
Source identities are checked again at campaign completion.

```text
native custom PP caller → parser/Init/Open/Convert/Fast
 → modeled FindPath and SendCommand6 open the selected raw archive
 → modeled Seek/Read with native member parsing
 → native Close PUSH saves parser R4 and Thumb return PC
   → modeled SendCommand8 closes only the host ledger
   → native arc=0, command=14, stat&=~48
   → native POP PC returns Thumb; LR remains020D82D0
 → native parser/wrapper returns with real R1/flags/LR
 → PP checkpoint → getter/setter → complete six-Mon caller
```

TOP=`0x023BEEC0`, FILE=TOP−112. Close enters from the Thumb BLX at
`0x02007404` with SP=TOP−136 and saved return `0x02007409`. In the normal
fixture R0=FILE,R1=TOP,R2=16,R3=0,R4=BTAF+12=28,R5=310,R6=BTNF3796,R7=16,
followed by high-register cookies. The inherited clobber control changes
R1/R2/R3/IP and flags according to its declared backend policy.

Close PUSH8 writes `[28,0x02007409]` to `[TOP−144,TOP−136)`, reusing Open's
dead saved pair `[path,0x02007353]`. It assigns R1=command8 and R4=FILE.
SendClose receives SP=TOP−144, LR=`0x020D82D0`, R0=FILE,R1=8; R2/R3 are
actual volatile residues, not new formal dispatcher arguments. The opening
Send at the same address instead uses command6, a different SP/LR and open state.

The closing model requires the actual native Fast fields, open ledger, seven
reads and final raw cursor8796. It closes only that ledger, preserving archive,
path and cursor. It does not clear guest fields or reconstruct a native queue,
FSArchive, card or scheduler. Native stores alone clear arc8, write command16=14
and clear status12. The other60 bytes, including argument identity48/52, remain
preserved. Command14 was already present in this fixture: its actual store
still appears in the transcript. Identical before/after bytes do not prove a
store occurred.

Send success1 or declared truthy2 is compared at `0x020D82D0`. The following
unconditional MOV sets R0=0 without changing flags. Thus the EQ POP at
`0x020D82D8` remains false despite R0 being zero. On qualified Unicorn2.1.4,
CPU model17, this false location yields a hook with full16-register state
identical to the next instruction; it does not restore R4/SP/PC. Native code
then performs the three stores and returns R0=1.

The final POP loads saved PC and returns to Thumb `0x02007408`, restoring parser
R4 and SP. LR itself remains `0x020D82D0`. Parser ADD/POP and wrapper ADD/POP
also leave LR untouched. Reader end therefore has R1=0, LR=`0x020D82D0` and
CPSR=`0x2000003F`, including under backend clobber; R2/IP retain their declared
policy and R3 is restored from the caller's saved word. The actual PP checkpoint
at `0x02073320` sees this return. The subsequent BL at `0x02073324` replaces LR
with `0x02073329`, so later getter checkpoints retain their prior contract.
No register bridge normalizes the native return to the former Close model.

The reader has212 hooks,187 unique starts,52 native stores and15 modeled events
in four categories: Find, Send, Seek and Read. Send appears twice with distinct
roles. Close adds15 starts and five stores (PUSH2 and field stores3). Its8-byte
frame does not increase the existing240-byte peak/global560, guard56 or full608
projection. The guard's extra8 readonly bytes stay outside that final projection.
Earlier Open/Fast snapshots retain their earlier lifetimes; the final240/152/136
views contain Close's saved pair and cleanup. No new memory mask is added.

The counter changes only R0 from0 to the original archive token just before
`STR FILE.arc` at `0x020D82DC`, after a successful modeled close. Full SP/LR/R4
and closed state identify the invocation. `0x020D82E0` sees that token before
MOV14 absorbs the register change. Return ABI, all model events and complete
PP flow remain identical; one archive word differs in three final frame views,
and phase RAM digests differ. All names, party/PP, seed and whole final RAM stay
exact without new projections. The disguised counter fails the positive native
flow oracle. This proves the finite cleanup distinction, not an actual native
Send failure policy. The true failure exit remains statically attributed here.

Portable tests need no ROM:

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_close_bench.py -v
```

For [pure receipt replay](../../features/trainer-strategy/test/test_fs_close_attribution.py),
set `SGP_FS_CLOSE_ROM_DIR` to authenticated `r4-EN.nds`/`r4-IT.nds` and
`SGP_FS_CLOSE_REPORT_DIR` to generated `fs-close-EN.json.gz`/`fs-close-IT.json.gz`.
Set `SGP_REMATCH_OBJECT_DIR` and `SGP_STRATEGY_OBJECT_DIR` as in the parent guide;
run discovery with `-p 'test_fs_close*.py'`. Missing private inputs yield explicit
skips, not exact-ROM verification.

Documented provenance covers the SDK counterpart and recovered recipe; binary
correspondence covers60 installed bytes. Finite activation covers the selected
initialized file lifetime in the complete caller. Original compiler provenance,
native Find/Send/Seek/Read and archive/card/thread/error state, natural encounters,
full battle, UI, SAVE/cold restart and hardware remain outside. No gameplay fix,
speedup or reclaimed memory follows from this attribution.


The final matrix passed20 complete runs,10 per language: four Normal/Plus and
seed positives, one alternate fill, two backend controls, two OFF runs and the
uncleared-archive counter. EN106.283s/604274688 bytes OS peak RSS;
IT109.015s/567705600 bytes. Thirteen portable/replay tests passed with zero skips,
8.112s/722026496 bytes OS peak. These are host verification costs, not game timings.
Independent reviews covered source/raw/recipe, ABI, observer, OFF, counter,
both final languages and public CLI/documentation.

All eight positives preserve the Fast-parent six packets, Trainer data, seed,
all names, PP store/checkpoint and whole final4MiB RAM hash, with15 extra hooks.
The PP flow has exactly one changed checkpoint at index8/`0x02073320`: R1 changes
from destination to0 and LR from`0x02007409` to`0x020D82D0`; the other21 checkpoints
remain exact. This actual ABI difference must not be described as identical PP
flow. All eight retail/base1.1/V4/r4 bodies match the60-byte recovered recipe
and signed BL target, using independent ELF readback without CPU execution.
Previously closed provider campaigns were not repeated.
