# Trainer31 caller preparation up to constructor entry

This case executes the native caller that prepares trainer31's BattleSetup slot
from raw header and packed name inputs, then stops at the first constructor entry
fetch. It closes the preparation boundary of the
[trainer31 constructor case](strategy-31-source-rom-1.3.2.md). Those two runs are
separate qualifications: no combined full caller/constructor execution is claimed.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Require provenance of all52 copied bytes, rather than filling the destination
with an expected header. Separate the20B archive header from32B of local stack
content, retain packed name representation and observe actual copy/destructor
calls. Distinguish a nested constructor entry from an API return, and live
message-loader ownership from a completed caller lifetime. Independently review
raw offsets, instruction starts, ABI, branch conditions and counterproofs.

## Il materiale più grezzo da cui partire

Use your own exact r4 images identified in the
[packed-name case](trainer-name-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire):
EN152786844B SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
IT159029760B SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Input identification uses whole-image hashes. Reports/raw fixtures stay private;
no ROM, message text, save or extracted data is shipped.

The source correspondence is the pinned HGSS reference
`cb614ad23449d5852b40321dc409c4143872b35c`:
[trainer_data.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/trainer_data.c),
[save.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/save.c),
[save_misc.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/save_misc.c),
[pm_string.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pm_string.c).
This is native HGSS code with source/byte correspondence, not a reconstruction
using the unavailable original compiler/linker objects. Existing Plus source,
composition, ELF and constructor attribution remain in the linked owner cases.
No compiler or new ROM build is used here.

`EnemyTrainerSet_Init` has entry`020733C0` (physical`000773C0`), arguments
r0=BattleSetup*, r1=SaveData*, r2=heap. Its176B span including alignment/pool
has SHA-256`76912054c0a5f1183697cc83d7fa853fffd712b1620b9b6054e06314968e867b`.
It pushes24B and reserves72B: caller frame96B. Heap11 and IDs[0,31,0,0]
exercise one zero-ID skip followed by ordinary trainer31. The zero-ID branch
executes`02073444..02073452` before processing index1; these instruction starts
must remain in the preparation map despite being located after the constructor BL.
Rival-class23, multiple active trainers and allocation failures are excluded.

Native `TrainerData_ReadTrData` at`020735D8` forwards to the raw archive reader
with destination=local SP+`14`, NARC55/member31. The20B member at physical
`01F933B0` in both r4 inputs has SHA-256
`db2e0fa9e4d0b97a0d1721e878001bcddafe1e379827adccc37844cdbce13fff`.
It describes class72/type3/count6; full party/strategy attribution is in the
constructor case. Native instructions at`02073404..0207340E` copy52B from the
local Trainer to BattleSetup+`5C`. Only20B came from the archive; the remaining
32B are incoming stack content, verified against the pre-entry fixture and
raw reader's exact write extent. They are not silently initialized to zero.

Name31 uses NARC27/bank729, independently decoded as **packed** words:
EN5 words/size4/raw SHA-256
`d8cb717866c2ed6e5d14f65c6b1009f92888047d477ee968f054ea80daf38737`;
IT6 words/size5/raw SHA-256
`59d7d29f69edcaf78428fa3080f1d0d576f41fd4d7a257910d7f1b87e18596e5`.
`CopyStringToU16Array` at`02026A68` receives capacity8 and destination
BattleSetup+`70`, copies10B EN/12B IT with native ARM memcpy, including outer EOS.
The rest of the16B name field and16B mail fields retain their stack-derived bytes.
The [packed-name case](trainer-name-source-rom-1.3.2.md) explains source loading,
allocation ABI, encoding and earlier/later image lineage.

Native Save_Misc_Const_Get`0202A960`→`020272EC`→SaveArray_Get`020272C8`
reads SaveData+`230AC`, the offset of array9, and returns SaveData+`10`+offset.
RivalName getter`0202A9A8` returns Misc+`270`, even on this non-rival path.
The fixture supplies a readonly table word and sparse addresses; it is not a
real save and performs no save-system, Continue or compatibility validation.

Native String_Delete`02026380` changes magic to the invalid marker before
calling modeled Heap_Free`0201AB0C`. The message loader remains live when
BL`02073440` (physical`00077440`) reaches constructor`02073604` with
r0=setup, r1=1, r2=11, LR=`02073445`, SP=outerSP−96. R4–R7 are the caller's
actual live values, not injected constructor cookies. The constructor's first
`PUSH {r3,r4,r5,r6,r7,lr}` is fetched but **not executed** at this endpoint.

## I metodi e gli strumenti da usare

Use the [owner](../../features/trainer-strategy/README.md),
[verifier](../../features/trainer-strategy/tools/attribuisci_preparazione.py),
[replay tests](../../features/trainer-strategy/test/test_preparation_attribution.py)
and Python/dependencies from the
[test bench](../test-bench.md#linking-source-to-an-exact-rom).
From the repository root, with ndspy, Capstone and Unicorn available:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_preparazione.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --json /path/to/private/fresh-prep-EN.json
```

Repeat for IT. Existing output paths/aliases and outputs under source are refused.
Reports are bounded2MiB. Independent FAT/FNT/NARC and ndspy resource readback,
ARM9 logical/physical readback, fixed hashes, Capstone instruction starts and
separate literal pools precede execution. The map contains128 starts:100 for
caller/header/save/deletion paths,28 for native name copy/ARM memcpy. All128
must be observed in each positive path; no observed-PC auto-admission exists.

Four SDK boundaries are modeled: NewMsgDataFromNarc, NewString_ReadMsgData,
ReadWholeNarcMemberByIdPair and Heap_Free. Their exact arguments/order/results
and writes are recorded. Message/String allocation/decryption stay host work;
String_New/lazy loader bodies are not executed. A separate test arena prevents
message allocations from moving the constructor's existing fixture arena.
The raw header model writes exactly20B to the native local pointer. Caller
structure stores, packed name copy and invalidation execute native instructions.

Each language runs two initial stack poisons and paired observer OFF/ON. The
functional RAM/register endpoints agree OFF/ON. Header/name prefixes are stable
across poisons; unused name/mail bytes follow their declared stack provenance.
Six native helpers have matched entry/return SP and R4–R11, with pointer results
checked only where defined; void R0 is not a status code. Strict reads/writes,
canaries, frozen unrelated RAM and128B stack/10k step limits check ownership.
Observed peak stack is112B;192 EN/200 IT code-hook steps include modeled entries
and the endpoint fetch, not hardware timing or a speedup measurement.

Eight executed negative calibrations per language reject expanded-name
substitution, a short raw-header write, missing modeled free, skipped native
deletion, skipped52B copy, wrong name destination, wrong capacity and wrong
constructor return address. They supplement byte and event checks. The first
static precheck caught a mistyped constructor opcode; raw readback corrected
`f0b5` to`f8b5` before any guest execution. An independent review initially
questioned the post-BL instruction map, then the zero-ID skip falsified that
concern; no map expansion was needed. Producer snapshots and receipts are
retained privately without rewriting earlier reports.

For reports named `prep-EN.json`/`prep-IT.json` and private exact-ROM symlinks
`r4-EN.nds`/`r4-IT.nds`:

```sh
SGP_PREP_ROM_DIR=/path/to/private/rom-links \
SGP_PREP_REPORT_DIR=/path/to/private/reports \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_preparation_attribution.py
```

`SGP_PREP_REPORT_NAME` can select another `%s` language filename pattern.
Nine test methods passed with both exact inputs and no skips, including replay
counterproofs against same-output missing calls/writes/PCs and lifecycle errors.
Independent review checks source, raw bytes, ABI and limits. This demonstrates
finite native preparation and entry activation; no constructor instruction,
caller return, final battleType OR, message destruction, natural encounter,
full battle, rendering, save or hardware path is covered. No game behavior,
ROM, ABI, IDs or save layout changed. A future combined run must continue this
same RAM/context through the constructor and caller suffix, including the live
message resource, before claiming the complete caller lifecycle.
