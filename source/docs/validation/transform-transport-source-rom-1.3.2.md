# Transform: native packet construction and PartyMon write requests

The [Rage repair](rage-source-rom-1.3.2.md) preserves Transform in status2.
This case follows that actual output word through the current native packet
emitter and receiving consumer. Eight positive chains and three counterexamples
per language distinguish state transport from the final move/PP decision.
The recorded SetMonData calls are requests; encrypted Pokémon mutation and
save persistence remain outside this case. No game code or save is changed.

See the [owner](../../features/type-consumers/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[existing battle audit](../bug-audit-1.3.1.md#battle-and-ai-repairs).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Follow the same status word from controller return to emitter load, packet
store, exact-byte delivery and consumer read. Do not recreate a packet from
the scenario name. Check both directions from the installed functions to the
source repair, inherited source correspondence, caller and resources.

Distinguish a native emission/decision from asynchronous protocol operation,
party ownership, encrypted data mutation and SAVE. Test the old Rage instruction,
a misplaced emitter store and a wrong consumer mask. A packet with wrong status
can still produce the correct final decision: intermediate state needs its own
oracle. Independent Sol6.1 review read all eight input-role images and separately
executed current and misplaced-store IT chains. The historical private HG-B03
consumer-only results retain their older input identities and are not rerun.

## Il materiale più grezzo da cui partire

Supply your own exact retail revision0, Plus1.1, V1.3 V4 and r4 images.
Complete identities and preparation are linked in the
[flags input section](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire),
[`baseline.py`](../../sgp131/baseline.py) and
[r4 contract](../../distribution/game-1.3.2-r4.json). Every CLI run authenticates
all four complete inputs for its language. This repository supplies no ROM,
BIOS, extracted retail data, personal save or private capture for this case.

The project recipe is the existing two-byte HG-B02 edit in
[`type_consumers.py`](../../sgp131/type_consumers.py), qualified by the Rage case.
The downstream wrapper, emitter and consumer are inherited native code with no
additional project payload or compilation here. At reference commit
`cb614ad23449d5852b40321dc409c4143872b35c`, the relevant functions are:

- `battle_util.c::CopyBattleMonToPartyMon`;
- `battle_controller.c::BattleController_EmitBattleMonToPartyMonCopy`;
- `battle_controller_opponent.c::BattleControllerOpponent_BattleMonToPartyMonCopy`.

Their signatures, data fields and branch behavior correspond to the raw native
functions below. That does not reconstruct the original C compilation, compiler
flags, objects or link map. The original native build provenance remains a gap.

## I metodi e gli strumenti da usare

Dependencies in the recorded run: Python3.14.7, ndspy4.2.0, Capstone5.0.9 and
Unicorn2.1.4. Reuse the qualified Rage CPU and independent overlay readers.
No compiler, full ROM build, runtime capture or save fixture is needed.
With private input/report variables, use your dependency environment's Python:

```sh
python3 source/features/type-consumers/tools/attribuisci_transform.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/transform-EN.json"
python3 source/features/type-consumers/tools/attribuisci_transform.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/transform-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentTransformTransport -v
```

Missing private unit inputs explicitly skip. The CLI cannot replace an input
with its report. Reports retain exact identities, regional comparisons, fixture
state, native reads/calls, packet hashes, requested fields/values/widths and
counterexamples without emitting retail instruction dumps.

### Installed code and insertion chain

| Material | Current RAM / size | Role and boundary |
| --- | --- | --- |
| PP-copy caller window | `0224B2E0`,80 B | Static BL `0224B31A`→wrapper; parent entry not executed |
| Copy wrapper | `02250C40`,48 B |44 B code +4 B item-offset literal; item99 skips TrainerAI clear |
| Packet emitter | `02263B4C`,356 B |314 B code +2 B alignment +40 B pool; frame80 B |
| FieldSide | `0223AB1C`,22 B | Native wrapper, frame8 B; calls battler-type getter |
| Battler type | `02261258`,12 B |6 B code +2 B alignment +4 B pool; byte at object+`0x195` |
| Receiving consumer | `022591F4`,220 B | Native Transform/Mimic decision, frame32 B |
| MaskOfFlagNo | `020726C0`,32 B | Actual ARM9 Thumb function, indices0–5 exercised |
| Clear command | `02259928`,8 B | Native write of zero to OpponentData+`0x94` |
| Client dispatch slot | `0226D0AC` | Static pointer `022591F5`; natural dispatch not exercised |

Wrapper48 SHA-256 is
`1417bf4618b5bfb876a0e3af5a3a59b527869372c6ff951cc120d0289b3f57a2`;
emitter356 is
`22f11a4696c951b40371c2918e4f31d8fe32726e77684e8f2e25aebaac5c7c2c`;
consumer220 is
`6385115c1c5cb9e7b17f043c5739e10581c7a0e84ca6e05ab4d489cfc1a0dca7`.
These bodies are unchanged across retail→base→V4→r4 EN/IT after a scoped retail
IT comparison: its consumer has ten BL fields targeting the same ARM9 addresses
(two Mask, seven SetMonData, one CalcStats). Each target and its32-byte entry
signature is verified before normalizing only those fields in a comparison copy.
The signature does not qualify the modeled SetMonData/CalcStats bodies. Runtime
bytes are never region-normalized. Other listed windows have identical raw bytes.

Current code is in BLZ overlay12, file12, base `022378C0`,226176 decoded bytes,
BSS0. The161600-byte streams occupy EN `08314200–0833B940` and IT
`08800000–08827740`. Raw y9/FAT and project decompression are checked against
ndspy, with stored/decoded identities retained. No linear physical offset is
assigned to an individual decoded instruction. The Rage case explains the
source edit and shared composition that produced the current image; unchanged
downstream bytes require no extra insertion, allocator or new ABI.

### Actual data path and declared services

The same Unicorn memory first executes Rage state1 and its native callees.
Additional synthetic item, HP, move, PP and action data are prepared afterward;
the resulting status2 word is left untouched. Wrapper arguments are r0=BS,
r1=context, r2=battler0. The item is99, so its separate zero-item AI-clear branch
does not execute. Form/recalculation flags are0 throughout this contract.

The emitter reads `ctx+0x2DB0` at `02263C18` and stores the word at local
SP+`0x2C`, which is packet+`0x1C`. The packet begins at SP+`0x10`, contains44 bytes
and uses command `0x27`. It carries party index in byte1's low nibble and Mimic
mask in its high nibble, HP at+2, status at+4, item at+`0x0C`, four16-bit moves
at+`0x0E`, and four8-bit PP at+`0x16`. Status's poison counter is masked by the
native emitter. BattleMon stride is`0xC0`; move, PP and status fields are frozen
through emission. FieldSide and its getter execute natively from initialized
BS/object pointers, exercising sides0/1.

At BL `02263C7E`→`02262240`, a declared EmitPacket service records r0=BS, r1=1,
r2=battler0, r3=packet pointer and fifth argument44 on SP. The bench copies those
exact44 bytes, including padding, to OpponentData+`0x94`. This is a synchronous
test bridge, not native asynchronous delivery, queue scheduling or a new probe.

The receiving consumer reads packet+`0x1C` at `02259214`. Its `2<<20` Transform
test branches at `0225921A` past all four move/PP pairs. Without Transform,
native MaskOfFlagNo checks each Mimic slot before requesting that pair.
Party index0 or5 has a separate native mask check for knocked-off items.
The fixture's knocked-off mask is0. Item/HP/status requests still occur.

PartyMon lookup, SetMonData and acknowledgement are declared models.
SetMonData records the actual field ID, data pointer, width and value, while
the nominal Pokémon buffer stays a canary. Native command clearing executes
after acknowledgement. CalcStats is explicitly outside the contract and rejects
entry. Thus neither encrypted data updates nor native stat calculation is
claimed. The consumer changes only the packet's command byte to0.

Actual PC/SP/Thumb returns, eight distinct saved-register cookies, native leaf
returns, masks, read sites, call order, write ranges, full context/BS/opponent
snapshots, Pokémon/stack/caller canaries and initialized code immutability are
checked. Tables, alignment and pools cannot execute. Observed stack maxima are
104 B for wrapper+emitter+FieldSide and48 B for consumer+Mask.

### Results and falsifiers

Eight positive chains per language cover leaving Rage with Transform/Substitute,
keeping Rage while transformed, Rage alone, each single Mimic bit and all four
Mimic bits. Mimic cases use party index5 and side1; others use index0 and side0.
Actual emitter/consumer reads and equal status words are checked separately
from the exact SetMonData request sequence.

Three RAM-only counterexamples per language are normally refused by constructor
identity checks; explicit variants admit only their specified changes:

- Restoring Rage's old AND yields status `0x00800000`, loses Transform and
  reaches eight move/PP requests. It fails the protection oracle.
- Moving the emitter's status store from packet+`0x1C` to+`0x24` leaves
  `0xA5A5A5A5` at+`0x1C` from the bench's stack paint. That value happens to
  contain Transform, so the same zero move/PP requests occur. The exact status
  transport oracle rejects it. The overwritten ability field is outside the
  form/recalculation paths exercised here.
- Testing bit20 instead of Transform's bit21 in the consumer preserves the
  correct packet word `0x01200000` but reaches eight move/PP requests. The
  independent protection oracle rejects it.

Four current-image unit methods and17 structural/domain negatives pass.
An initial misplaced-store fixture overwrote two PP bytes and was correctly
rejected by the packet-field oracle; the same-output counterexample above was
then scoped to the unexercised ability field. This is a bench experiment,
rather than an installed defect or a new game repair.

Provenance is documented for the Rage source repair and inherited downstream
code. Binary readback and scoped regional correspondence are established;
original native compilation is not reconstructed. Semantic transport and write
decisions are demonstrated for the finite controlled chains. Natural battle
dispatch, zero-item cleanup, form/stat recalculation, actual asynchronous
delivery, encrypted PartyMon changes, SAVE/cold restart, hardware and timing
remain open. The current HG-B03 evidence extends the causal chain without
claiming a second independent game fix or persistence proof.
