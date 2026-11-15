# Grounding: pointer provenance and actual native damage execution

Two source-owned pointer words reconstruct the complete180-byte helper in exact
r4 EN/IT. Seventeen positive and two counterexample parent entries per language
execute the native type-damage function, Grounding helper, multiplier and real
signed arithmetic. Five external queries remain models. The counterexample
keeps the same row index but reads the wrong column data and returns wrong damage.

See the [owner](../../features/type-consumers/README.md),
[Conversion2 case](conversion2-source-rom-1.3.2.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).
This is attribution of an existing repair, not a new game or policy change.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Trace the data recipe through actual PC-relative loads, row indices and reads,
then the native caller, boolean helper result, multiplier and damage/status
return. Distinguish an inherited modern chart pointer in the parent from the
new retargeting of its helper's two columns. Neither an unchanged index nor an
unchanged number of calls proves that the right data was consumed.

Derive ABI/write rules from actual code. The compiler legally reuses the incoming
damage argument's stack word; requiring it to remain unchanged would reject a
correct damage calculation. Independent Sol6.1 review read regional raw windows,
checked caller contexts and independently executed targeted IT cases. Its initial
caller-immutability note was corrected after a100→200 result also changed the
incoming damage homeword to200. The retained evidence records that correction.

## Il materiale più grezzo da cui partire

Use your own exact retail HeartGold revision0, Plus1.1, V1.3 V4 and r4 EN/IT.
Their full identities/preparation are linked in the
[flags input section](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire),
[`baseline.py`](../../sgp131/baseline.py) and
[r4 contract](../../distribution/game-1.3.2-r4.json). Every run authenticates the
four complete inputs per language. No save, BIOS, ROM, dump or extracted asset
is included or required inside the public repository.

The source recipe is `GROUNDING_PREIMAGE`/`GROUNDING_REPLACEMENT` in
[`type_consumers.py`](../../sgp131/type_consumers.py); the
[shared AI writer](../../sgp131/mechanics_stages.py) inserts those eight declared
bytes in decoded overlay12. This is a data replacement in inherited native code,
so no new C/assembly object or compiler invocation is involved. The original
native MW toolchain and the historical builder that installed the parent's
modern chart pointer are not reconstructed. Their input bytes are pinned and
compared, not claimed as a fresh source rebuild.

Native reference names come from `src/battle/battle_util.c` at pret/pokeheartgold
commit`cb614ad23449d5852b40321dc409c4143872b35c`:
`BattleSystem_IsTypeMatchupActive`, `BattleSystem_ApplyTypeEffectiveness`,
`ApplyTypeMultiplier` and `DamageDivide`. Source helps interpret signatures and
state; exact bytes and execution independently qualify the candidate.

## I metodi e gli strumenti da usare

Dependencies are the same qualified Python/ndspy/Capstone/Unicorn environment
as Conversion2 (recorded3.14.7/4.2.0/5.0.9/2.1.4). No compiler or retained ELF is
needed for this data-only owner. Set variables to your exact private inputs:

```sh
python3 source/features/type-consumers/tools/attribuisci_grounding.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/grounding-EN.json"
python3 source/features/type-consumers/tools/attribuisci_grounding.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/grounding-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_chart.CurrentCompositeGrounding -v
```

Use the Python environment containing those dependencies. Missing private unit
inputs explicitly skip. Report output cannot replace an input. JSON contains
hashes, mappings, synthetic state and executed/read ranges, not retail dumps.
All inputs are read-only; only own-source tooling/tests and reports are written.

### Recipe, insertion and native dependencies

| Component | RAM / extent | Qualification |
| --- | --- | --- |
| Grounding helper | `02251C74–02251D28`,180 B |172 B code plus two pointer words |
| Owned data words | `02251D20`, `02251D24` | Sparse columns → modern chart+1/+2 |
| Damage parent | `02251D28–02252054`,812 B | Native code plus six literal words |
| Multiplier | `022583B4–02258440`,140 B | Native136 B code plus battleStatus literal |
| DamageDivide | `02253178–02253194`,28 B | Native signed wrapper with minimum±1 clamp |
| Signed division | ARM`020F2998–020F2BA4`,524 B | Actual quotient/remainder, previously qualified path |

Eight bytes are declared; six values change. Full V4/base helper SHA-256 is
`63908aa186c999cc59ea0a1875ddfad458c4f1d9e25f044d81824c26069a6802`;
current180-byte SHA-256 is
`0c2f127b2687c82b6fd9b8d97a590011ccaa2f1e84021c956f76edda763f821f`.
Replacing only the two words reconstructs that entire current window.
Defender-column loads at`02251C9E/1CC4/1CE0/1D0A` reach pool`02251D20`;
effect-column loads at`02251CA6/1CE8/1D12` reach pool`02251D24`. The reader decodes
all seven actual PC-relative aliases. They now point to`021FBE61/62`.

Raw y9/FAT and independent project/ndspy BLZ decoders identify overlay12, file12,
RAM base`022378C0`,226176 B, BSS0. Encoded r4 spans are EN`08314200–0833B940` and
IT`08800000–08827740`,161600 B; hashes/footer are recorded and explained in the
flags case. Decoded instructions do not have simple linear physical offsets
inside that compressed stream. Overlay18, ARM9 and autoload maps are read and
hashed separately. Current dense chart replay reuses the two-byte Ghost recipe
from V4; it does not attribute the whole shared overlay18 or repeat the325-row
CPU campaign.

The parent is unchanged between base1.1/V4/r4, SHA-256
`3958c8527fe0b43de6b2514020eb8bc7de00a2a45761d59761f264e99ecfb443`.
It already used modern chart`021FBE60` while the helper still indexed sparse
columns`0226CC7D/7E`. Modern row72 is Ground/Flying/0; sparse row72 is
Grass/Dark/0. Mixing the same index across those representations caused the
already-repaired defect.

The multiplier140-byte SHA-256 is
`2f27bcc0bcbdfb64629327b5ecaa26623afe0c4d2401ab3ff578e60b6546b686`,
DamageDivide28-byte SHA-256 is
`f5cf038e36e912e23ea10bf74b1bb991fbc1eadb235f0c1be9f27e638de8bce5`.
They are inherited native code. The original full native compilation is not
reconstructed from those identities.

### Regional evidence and callers

Retail EN parent SHA-256 is
`e9e3b08228a8b8e4615b8cc0c8522088059eb49a86546e25e46809abb231f836`;
retail IT parent at`02251CC8` is
`bd3760f9abfb8f3aa1066ee3c5ed0969fc1345159597e3e73a66cad98509eeac`.
They do not share the Plus parent hash. Retail uses the sparse chart; Plus's
modern parent pointer was inherited before the new helper repair. Three actual
parent LDRs alias its chart pool; two actual BLXs still reach ARM`020F2998`.
Only after verifying those references and math identity do comparison copies
normalize the two BLX fields and chart pointer to the canonical Plus window.

Retail IT helper at`02251C14` has raw SHA-256
`f813e19582cd5890138241236ac1668d7c026317eaaeb4195da439212702390f`.
Its two words point to regional`0226CC1D/1E`; its seven LDR aliases are verified
before comparison-only pointer normalization. The172-byte body matches.
Retail IT DamageDivide differs only in the PC-dependent encoding of its BLX,
which reaches the same ARM target. The multiplier140 B agrees across all eight
inputs. No runtime bytes are normalized and no global regional-address rule
is assumed.

Two current parent BLs reach Grounding at`02251EC8/1F22`, two reach the multiplier
at`02251EE2/1F3C`, and its BL`022583D8` reaches DamageDivide. Twelve upstream BLs
are source-correlated in examined overlays10/12: eight trainer-AI callers and
four command/player/util/opponent-controller callers. All addresses and raw-BL
hashes are in the report. This is a bounded static link set, not twelve natural
observations or a global absence-of-indirect-callers proof. One is the post-KO
stage-two call at`02258B48`, previously an explicit model boundary; this case
qualifies the callee independently, not that entire combined decision state.

### ABI, state, writes and arithmetic

Parent entry takes BS/ctx/move/default type in r0–r3, with attacker, target,
damage and status pointer on the incoming stack. Its24-byte push and48 local
bytes make72 B. It rewrites incoming words at original SP+8/+12; the damage
homeword is mutable and must end equal to returned r0. Attacker/target/status
pointer and caller canaries remain intact. This differs from requiring all
stack arguments to be immutable.

The16-byte Grounding frame takes ctx/attacker/target/index, returns a boolean
and preserves its live callee state. Attacker is unused by its observed body.
Native predicates read:

- Iron Ball effect106 or Ingrain: Flying row with multiplier0 becomes inactive.
- Roost: every matching Flying row becomes inactive.
- Gravity mask`0x7000`: Flying/multiplier0 becomes inactive.
- Miracle Eye: Dark/multiplier0 becomes inactive.

Raw fields are word ctx+`2DC0+target*C0`, bits`0x400`/`0x400000` for
Ingrain/Miracle Eye; word ctx+`1D4+target*40`, bit6 for Roost; word ctx+`180`
for Gravity. Offsets/masks are hexadecimal. The fixture uses target1 and one
repeated defender type. Five item/ability/type queries are models; actual item
lookup, abilities, context allocation and dual-type behavior are not qualified.

The multiplier receives ctx, attacker, multiplier, damage, then move power and
status pointer on its stack. Move1 power comes from the independently verified
parent literal`0x3E1`, at ctx+`3F1`; type's literal is`0x3E2`. Historical fixtures
use power0, so weakness/resistance do not set their status bits even when damage
changes. Explicit power50 cases verify flags2/4. This state difference must not
be hidden behind a generic expected-damage oracle.

DamageDivide executes its actual28-byte wrapper and signed ARM dependency.
For positive5/10, ARM returns quotient0/remainder5, then the wrapper returns
minimum damage1. Python floor division alone would return0. This new low-damage
case does not invalidate the historical100-damage fixture, whose divisions
were exact. Math return ISA/callee registers, actual PC/SP/Thumb, eight unique
cookies, pending calls and read/write closure are checked. Only bounded stack,
the two stated incoming words and four-byte status output admit guest writes;
other context, initialized code/data and canaries remain unchanged. Maximum
observed stack depth is96 B, not a global game requirement.

### Results and counterproofs

Seventeen positive cases per language cover Ground/Flying with no effect,
Iron Ball, Gravity, both and another item; Ground/Poison, Fire/Flying,
Electric/Ground, Fairy/Dragon and Ghost/Steel controls; Ingrain, Roost and
Miracle Eye; powered weakness/resistance and minimum damage1. Attacker types
are modeled Normal, abilities0; move1, base damage100 or1, power0 or50, initial
status0. All other combinations and gameplay timing remain outside the scope.

Iron Ball and Gravity positives observe index72, actual column reads2/0,
inactive helper, no immunity multiplier, damage100/status0. Two named RAM-only
counterexamples restore the old two pointer words. They still observe index72
but read defender17, keep the helper active, apply multiplier0 and return
0/status8. The semantic oracle rejects them. Inputs and candidate bytes are
never overwritten. The proof does not claim that the two words are individually
load-bearing for every fixture.

Three current-image methods pass in both languages with no skips. Nine negative
checks reject dependency/chart/math mutations, wrong PC alias, power/type field
confusion and a regional BLX-target mutation. Independent reviews verify raw
regions, caller contexts and selected positive/counter cases. No historical
campaign is repeated.

Final EN/IT readers exit0 in1.828/1.854s, OS peak RSS204,079,104/210,321,408 B,
under1GiB. Logs are bounded2MiB, case output16MiB; no ROM build, compilation or
capture. These host proof costs do not measure game speed or device behavior.

- **Documented provenance:** input/recipe/shared-writer identities and native
  source correspondence; inherited modern-parent adoption explicitly separated.
- **Reconstructed binary correspondence:** full180-byte helper from source data,
  native dependencies, current caller links and bounded regional aliases.
- **Demonstrated semantics:** declared parent entries with actual helper/multiplier/
  math, finite states, caller-homeword rules and wrong-column falsifiers.
- **Observed activation:** isolated parent entries under five declared queries.
- **Unattributed or untested links:** original native toolchain/historical chart
  builder, natural upstream state, full type/ability/item/status domain, SAVE,
  hardware, cross-session state and game performance.

No new game repair or optimization is delivered. The reusable result is a method
for attributing pointer data through its executed consumer while preserving
compiler-owned caller words and stating the fixture's power-dependent flags.
The separate Wonder Guard charge gate remains executable attribution work;
this case leaves that ability branch disabled rather than qualifying it.
