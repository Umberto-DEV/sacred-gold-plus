# Rage: source bit clear, exact controller and native leaf calls

The existing HG-B02 two-byte repair reconstructs the complete 340-byte pre-turn
controller in exact r4 EN/IT. Forty positive entries and two RAM-only
counterexamples per language execute the controller and all three reached leaf
functions. Leaving Rage clears bit23 and preserves the other status2 bits.
This case attributes the installed repair and changes no game code or saves.

See the [owner](../../features/type-consumers/README.md),
[Wonder Guard case](wonder-guard-source-rom-1.3.2.md),
[native RNG qualification](conversion2-source-rom-1.3.2.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Follow the source edit through its guarded insertion, entire native body,
literal aliases, selected-move data, actual load/store and return ABI. Separate
legitimate controller changes from damage to another volatile status bit.
Check the reverse direction from the ROM body to the recipe and distinguish
inherited native code from project assembly or an original native C rebuild.

Seek counterexamples that retain Rage or clear another bit. Include Rage still
selected, Rage absent, non-Fight action, empty selection and nonparticipating
battlers. An independent Sol6.1 review read all eight input-role images, checked
addresses and ABI, and separately exercised selected IT cases and a jump-table
PC rejection. The historical private campaign of464 executions on eight older
Plus images remains attached to those older inputs; it is not rerun or labelled
as current r4 coverage.

## Il materiale più grezzo da cui partire

Use your own exact revision0 retail, Plus1.1, V1.3 V4 and r4 images for each
language. Preparation and complete identities are in the
[flags input section](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire),
[`baseline.py`](../../sgp131/baseline.py) and
[r4 contract](../../distribution/game-1.3.2-r4.json). The reader authenticates
size and SHA-256 of every complete input. No BIOS, save, ROM, extracted retail
data or private capture is supplied by this case.

The recipe is [`type_consumers.py`](../../sgp131/type_consumers.py):
`RAGE_PREIMAGE`, `RAGE_REPLACEMENT`, guarded context, `edits()` and
`patch_overlay()`. At `022493FC`, Thumb `ands r1,r0` becomes `bics r1,r0`.
Both bytes of the halfword differ. This is an in-place instruction repair in
inherited native code; it compiles no new Rage payload.

At reference commit `cb614ad23449d5852b40321dc409c4143872b35c`,
`src/battle/battle_controller_player.c::BattleControllerPlayer_BeforeTurn`
contains the historical positive AND. It explains the defect, signature and
state machine, rather than supplying a corrected native compilation.
`battle_util.c::GetBattlerSelectedMove` explains the action/slot layout.
Raw code and data independently establish the correspondence. The original
native compiler, flags, original object and link map remain unavailable.

## I metodi e gli strumenti da usare

The recorded environment is Python3.14.7, ndspy4.2.0, Capstone5.0.9 and
Unicorn2.1.4. Reuse the preceding qualified input/overlay readers and native
RNG definition. No compiler, full ROM build, runtime capture or save is needed.
Set private input/report variables and use your dependency environment's Python:

```sh
python3 source/features/type-consumers/tools/attribuisci_rage.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/rage-EN.json"
python3 source/features/type-consumers/tools/attribuisci_rage.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/rage-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentCompositeRage -v
```

Missing private unit inputs explicitly skip. The CLI report cannot replace an
input. Reports retain hashes, mappings, bounded fixture state, executed PCs,
native call/return observations and counterexamples without exporting ROM code.

### Recipe, placement and independent readback

| Material | RAM / extent | Verified role |
| --- | --- | --- |
| Controller | `0224930C–02249460`,340 B |320 B instruction extent containing an8 B jump table, then20 B pool |
| Jump table | `02249332–0224933A` | Four state destinations; data excluded from executable PCs |
| Rage edit | `022493FC`,2 B | AND→BIC; mask built as `2<<22` |
| Status aliases | LDRs `022493DC`, `022493F4`, `022493FE` | All reach pool `02249458` = `0x2DB0` |
| Load/store | `022493F6`, `02249400` | Same `ctx+0x2DB0+battler*0xC0` word |
| Static caller link | Slot `0226CAAC` | Thumb pointer `0224930D`; natural dispatcher entry not exercised |
| MaxBattlers | `0223A7F0–0223A7F4`,4 B | Native read of BattleSystem+`0x44` |
| SelectedMove | `022522F0–02252324`,52 B |44 B code,8 B pool; no service model |
| Random | `0223BD98–0223BDC4`,44 B | Native LCG, seed at BattleSystem+`0x2448` |

The old canonical340-byte SHA-256 is
`6b1cc1e0aed12d29a592a6ec41d80c942bceb37c3dc68dfe09b1b82fe79a2de0`;
the current r4 SHA-256 is
`b4c1fc5c7df7d0f3f0afdf2c9b7561d41c96c3d7974082108fabfc5930429be4`.
The complete source recipe is reapplied to decoded V4 using the installed,
previously qualified Conversion2 payload. Its Rage result and the separate
two-byte reconstruction both match all340 current bytes. This reuses that
payload's identity without claiming a new compilation. Other owner edits are
outside this controller's interval.

Retail IT's controller is at `022492AC`, SHA-256
`9a8f7305065f91a46e40b7fd1f425b59b3749b5e82d7ec232e3d4015401c90ba`.
Only the BL field at function+`0x40` needs comparison normalization: its actual
target is the same ARM9 Thumb `020726C0`. The reader verifies that target and
the32-byte MaskOfFlagNo body before normalizing a comparison copy. Runtime
bytes remain unchanged. The three reached leaf bodies are byte-identical
across all eight inputs, at their actual regional addresses.

Current overlay12 is file12, base `022378C0`,226176 decoded bytes, BSS0.
Its BLZ stream is161600 bytes at EN `08314200–0833B940` or IT
`08800000–08827740`. Raw y9/FAT and project BLZ are checked against ndspy;
reports include encoded/decoded hashes and footer. A decoded instruction has
no simple `physical FAT start + RAM displacement` offset. The shared
[`fairy_ai.py`](../../sgp131/fairy_ai.py) composer combines this edit with
other disjoint edits, performs the one canonical overlay rewrite and reconciles
the derived UI seed. [`mechanics_stages.py`](../../sgp131/mechanics_stages.py)
checks its container/region invariants. This small case replays the decoded
recipe and independently reads the final compressed output; it does not rebuild
the whole image or claim that Rage alone explains every overlay difference.

### ABI, actual activation and resources

Controller inputs are r0=BattleSystem, r1=context, with `stateBeforeTurn=1`
(Rage). The frame is32 B. With a Rage bit present, BL `022493EC` queries the
actual selected-move leaf; move99 bypasses the clear. Without Rage, the query
and store are skipped. The loop advances by `0xC0` through the active battlers.

SelectedMove checks action `ctx+0x21B4+16*battler==1` and nonzero slot position
at `ctx+0x21B0+16*battler`. Positions1–4 select the halfword at
`ctx+0x2D4A+2*position+0xC0*battler`. Position0 or another action returns0;
both therefore leave Rage when the bit is present, even if a fixture's stored
move was99. These initialized action and move words are controlled inputs,
rather than a natural UI selection or an NARC-cache activation claim.

The controller continues through Quick Claw and its end state: four actual
RNG calls write four halfwords at `ctx+0x310C`, reset state to0 and set command8.
Each seed transition, high16 return, final seed, call order and stored sequence
is checked. No Python service stub runs. Context/action data and inactive
battlers are frozen outside the explicitly allowed status, command, state and
Quick Claw writes; BattleSystem is frozen except its seed word.

The runner checks actual PC/SP/Thumb returns, eight distinct callee-register
cookies, pending leaf calls, stack/caller canaries, admitted instructions,
write ranges and initialized code/data immutability. Controller tables/pools
and leaf alignment/pools cannot execute. Maximum observed stack depth is40 B,
including the SelectedMove frame; this is a bound for the exercised path.

### Results, falsifiers and remaining links

Forty positive entries per language cover Rage combined with each of32 bit
positions, all bits, retained Rage move99, Rage absent, empty position,
non-Fight selection and mixed two/three/four-battler fixtures. All32 bit inputs
are a basis for the bound BIC operation: with the verified mask and same-word
load/store, it clears bit23 and preserves all other bits for any32-bit word.
The full-controller executions remain finite state1 observations.

Two named RAM-only variants per language restore the old AND or clear bit22
instead. Both return with valid ABI but fail the preservation oracle. For an
all-ones input the old AND returns status `0x00800000`; the correct result is
`0xFF7FFFFF`. Ordinary construction rejects either mutant. Four current-image
unit methods pass, covering bit/state behavior, controls, counterexamples,
leaf identity and actual entry into embedded data being rejected.

Provenance is documented for the project repair and inherited body; binary
recipe reconstruction and the bit-clear semantic property are established.
Activation is observed for the controlled state1 path and its native callees.
The static dispatch pointer is linked, but natural dispatch, Focus Punch,
rendered battle, other state histories, encrypted PartyMon updates, persistence,
SAVE/cold restart, timing and physical hardware remain unqualified. Transform's
bit is preserved here; its later client/party transport needs its own current
case. No new optimization or game correction is proposed by this evidence.

The subsequent [Transform transport case](transform-transport-source-rom-1.3.2.md)
extends that status word through native packet construction and receiving
write decisions, with an explicit transport/PartyMon service boundary.
