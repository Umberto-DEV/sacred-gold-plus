# Trainer21 buffer to native move and PP fields

The actual native move loop consumes the edited trainer21 buffer and writes
its four move IDs and PP into a valid encrypted Pokémon fixture. In Plus,
slot1 becomes450 with20 PP; Normal keeps206 with40 PP. This verifies the
setter link at an initialized post-CreateMon boundary. The fixture has species22:
**this case does not construct Scyther or a complete trainer party.**

## Cosa farebbe un professionista di alto livello che non sto chiedendo

The [positive strategy hook](trainer-strategy-source-rom-1.3.2.md) proves buffer
edits and the level-hook return, but not final move consumption. Follow the
actual caller's four loads, four native setter calls and four raw-resource reads.
Check the encrypted output independently, every other decrypted byte and the
explicit transition from the preceding hook fixture.

Keep two facts separate: the same CPU retains the genuinely edited strategy
buffer, while a documented host boundary supplies a copied valid Mon and a
current-record pointer. The latter is not an executed CreateMon call. Require
its checkpoint and initialization ledger in the result so this limit cannot
disappear from a successful report.

A matching final Mon alone is insufficient. A preapplied fixture permits a
missing setter to produce identical encrypted output. Check complete native
call/return evidence even when a valid fixture has been explicitly redeclared.
A wrong PP can also have a valid checksum and the correct move ID.

## Il materiale più grezzo da cui partire

Use the exact inputs, retained strategy ELF and source recipe from the
[hook case](trainer-strategy-source-rom-1.3.2.md). No new compiler, ROM build,
activation byte or gameplay source change is involved.

| Input | SHA-256 |
| --- | --- |
| r4 EN,152786844B |`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`|
| r4 IT,159029760B |`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`|
| Retained strategy `teams.o` |`e2429f61c7ee16071d303f7ca55cbb1553508720c6fe97b77aead9ce56e499e1`|

The prior [complete-constructor report](rematch-complete-source-rom-1.3.2.md)
supplies a private fixture. The verifier checks its exact ROM identity and
schema, revalidates positive index0 with the current independent oracle, then
copies its first236-byte Mon. It records report SHA, original report source
hashes, trainer/seed, species and Mon hash. The original report and fixture are
never written. A later developer prepares this report using their own ROM.
The historical report's source hashes remain historical identities.

The current trainer21 source member has six18-byte records. Its final record
has species123 and moves at offsets98/100/102/104:

| Mode | Move IDs | Base PP |
| --- | --- | --- |
| Normal |228,206,97,17|20,40,30,35|
| Plus |228,450,97,17|20,20,30,35|

The strategy specification changes offset100 from206 to450. The actual PP
members are16-byte entries in`a/0/1/1`; PP is byte6. Raw FAT/FNT/NARC readers
produce member physical offsets and SHA-256 in the report. The original trainer
member is authenticated by the public specification's SHA. The strategy580B,
configuration192B and full2048-byte owner retain the preceding exact reconstruction.
The historical Plus compiler and original native MW compiler remain unavailable;
source correspondence is not a fresh original-native rebuild.

The native source correspondence is pinned to HGSS reference commit
`cb614ad23449d5852b40321dc409c4143872b35c`:
[pokemon.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pokemon.c)
contains `MonSetMoveInSlot`/`BoxMonSetMoveInSlot`, while
[move.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/move.c)
contains `GetMoveMaxPP`. The actual setter preserves PP-Ups and recomputes PP;
the separate reset-PP-Up function is not this caller's observed entry.

### Caller, veneer, ABI and explicit boundary

| Region | Loaded address | Physical offset in these r4 inputs |
| --- | --- | --- |
| Four-move caller32B |`02073A22`..`02073A42`|`00077A22`|
| Setter veneer/body76B |`020714E8`|`000754E8`|
| PP helper readback64B |`0207332C`|`0007732C`|

Raw ARM9 section reading independently confirms these windows against the loaded
image. The reused first-Mon qualification checks all executed code/data hashes,
ISA and instruction widths; this is not an offset formula for compressed overlays.
The veneer at`020714E8` loads its target from`020714EC` and branches to
Thumb`020714F1`, the native body at`020714F0`.

Six preceding strategy-hook invocations retain the real buffer in one CPU.
Before the new phase, a checkpoint records full registers, PC, RAM hash, the
untouched workspace hash and the previous four bytes at the future frame slot.
The two declared host writes copy the checked Mon to the workspace and set
`[SP+64h]` to buffer+90. SP is explicitly initialized to the152-byte native
frame; CPSR initialization is recorded. All other entry registers must derive
from the hook endpoint. This initialized frame is not evidence of executing
the omitted constructor/held-item code.

At`02073A22`, the native caller initializes its record cursor. Four
`LDRH` at`02073A2C` read offsets98/100/102/104. Each BL at`02073A32`
passes workspace/move/slot to`020714E8`; all four returns at`02073A36`
check SP and R4–R11. The loop stops at`02073A42` before capsule handling.
R7 is now4; the other live caller registers, seed, strategy counter and buffer
remain unchanged. Capsule/form/post-form/PartyAdd are outside this case.

The qualified first-Mon bench supplies instruction/resource guards and the
existing model for four exact16-byte archive copies. No heap or filesystem
implementation executes here. The void return site`02073320` is the same raw
caller window qualified by the [SDK return case](sdk-void-return-source-rom-1.3.2.md);
that finite qualification is reused rather than repeated. Native guest code performs the move writes, PP
calculation, checksum and encryption. All other4MiB RAM is frozen except the
bounded stack and236-byte workspace.

## I metodi e gli strumenti da usare

Use the [pinned dependencies](../../requirements.txt), your own exact ROMs,
the retained strategy object and the private fixture report. From repository root:

```sh
python source/features/trainer-strategy/tools/attribuisci_mosse.py \
  --rom /private-inputs/r4-EN.nds --language EN \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --fixture-report /private-results/complete-EN.json.gz \
  --json /private-results/strategy-moves-EN.json.gz

SGP_R4_ROM_DIR=/private-inputs \
  SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
  SGP_COMPLETE_REPORT_DIR=/private-results \
  python source/features/trainer-strategy/test/test_move_attribution.py
```

Repeat the CLI for IT. Default ROM names are`r4-EN.nds`/`r4-IT.nds` and fixture
reports`complete-EN.json.gz`/`complete-IT.json.gz`. Override the respective `%s`
patterns with`SGP_R4_ROM_NOME`/`SGP_COMPLETE_REPORT_NOME`. Missing private inputs
produce explicit test skips. The CLI refuses existing outputs, input aliases,
source paths and retained-object directories. Compressed and expanded fixture
input and expanded report output are bounded to16MiB. Keep output private:
it contains copied Pokémon and extracted trainer/member data.

The [verifier](../../features/trainer-strategy/tools/attribuisci_mosse.py)
checks source/ELF/configuration, fixture provenance, raw readback, the boundary
ledger, native calls and independent output. The
[tests](../../features/trainer-strategy/test/test_move_attribution.py) cover:

- Normal and Plus: four exact buffer reads/calls/raw member copies, correct
  move/PP fields, checksum/quiescent flags and all other decrypted bytes.
- SDK volatile-register/NZCV poisoning with identical encrypted output.
- A named copied fixture with slot1 PP-Up2: native setters preserve2 and
  compute56 PP for206 or28 PP for450. This is a controlled state test.
- Wrong move argument, a PP byte changed only in RAM after authenticated member
  copy, and an explicitly preapplied fixture with slot1's call skipped.
- Missing boundary/caller/resource evidence, altered data beyond decoder fields,
  fixture expansion/identity refusals and output protection.

The last counter has exactly the baseline encrypted output and valid checksum,
but only three setter calls. Redeclaring its preapplied fixture still fails the
four-call requirement. The wrong-PP counter retains the intended move IDs and a
valid native checksum, so an ID/checksum-only check would miss it.

Capture argv, exit codes, input/source hashes and OS resource receipts. Budgets
are180s/1GiB RSS/2MiB logs/16MiB case output,500000 guest instructions and512B
stack, with10GiB free after a planned1GiB disk peak. Observed stack320B is a
verification result, not a hardware performance measurement.

### Result and remaining links

Both languages pass two ordinary modes, three guards and three counterproofs.
Eight test methods pass without skips. The byte link and finite native setter
semantics are demonstrated; the owner reconstruction is reattested from the
preceding case. Observed activation is initialized fixture state.

The report explicitly retains its hybrid boundary, copied species22 Mon and
modeled raw-member copies. Complete Scyther/trainer construction, a naturally
produced constructor frame, the remaining trainer IDs/formats, battle balance,
SDK failures and hardware/save checks remain unqualified. The next vertical
case must produce the positive trainer through an actual native constructor;
this setter result cannot substitute for that proof.
