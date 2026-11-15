# Post-KO selector: source bytes, scalar callers and retained scratch width

The exact current EN/IT selector reconstructs from its V4 image and the two
source scoring patches. It executes the actual scalar/Fairy/division/mask
chain qualified in the preceding cases. Nineteen isolated invocations per
language distinguish a32-bit best score from the deliberately retained8-bit
scratch value, and expose a same-choice false success in an integration test.

See the [owner guide](../../features/fairy-ai/README.md),
[scalar case](fairy-scalar-source-rom-1.3.2.md),
[flags case](fairy-flags-source-rom-1.3.2.md),
[historical scoring report](../ai-scoring-1.3.1.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).
No game code, chart policy, ROM, save or settings change is delivered here.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Reconstruct the entire selector window, not just its patch sites. Link its
upstream callers and two scalar calls from the actual decoded overlay. Follow
wide score, narrow scratch, exclusions, strict comparison and subsequent
fallback separately. A correct final slot can conceal a wrong move check or
stale value. Require intermediate outputs, order and actual native returns.

Keep modeled battle/party/mon/damage/RNG queries distinct from executed code.
Use the earlier qualified scalar and flags runners without silently replacing
the current shared composition with a historical V4 installation fixture.
Independent Sol6.1 review read all eight raw images, validated regional call
relocations and executed selected current/counterexample paths. Its finding of
a same-slot immunity false success led to a stricter per-move oracle.

## Il materiale più grezzo da cui partire

Use your own exact retail revision0, Plus1.1, V1.3 V4 and r4 EN/IT inputs.
The [flags input section](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire)
links full SHA-256/size contracts and preparation; this reader authenticates
all four whole files each run. No save, BIOS or extracted game data is supplied.

The source owner is [`sgp131/ai_scoring.py`](../../sgp131/ai_scoring.py),
`PATCHES`, `_function` and the guarded overlay recipe. The later shared
composition is in [`mechanics_stages.py`](../../sgp131/mechanics_stages.py).
Scoring changes existing native instructions; it does not compile a new C
selector. The resident Fairy helper is separately compiled and installed as
documented in the flags case. Its own-project ELF/payload/receipt are reused
in place, without a new compile or duplicate build tree.

Native source counterparts are in `src/battle/battle_controller_opponent.c`,
`src/battle/trainer_ai.c` and `src/battle/battle_util.c` at
pret/pokeheartgold commit `cb614ad23449d5852b40321dc409c4143872b35c`.
These explain signatures and intent, while binary readback establishes the
installed implementation. The original native MW toolchain is not reconstructed.

## I metodi e gli strumenti da usare

Dependencies and recorded versions match the scalar case: Python3.14.7,
ndspy4.2.0, Capstone5.0.9, Unicorn2.1.4. Compiler identity is recorded in the
reused canonical Fairy receipt; no compiler is invoked by this reader.
Set variables to your private exact inputs, matching Fairy build directory and
report directory, then use the dependency environment's Python:

```sh
python3 source/features/fairy-ai/tools/attribuisci_postko.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --build "$FAIRY_BUILD" --json "$CASE/postko-EN.json"
python3 source/features/fairy-ai/tools/attribuisci_postko.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --build "$FAIRY_BUILD" --json "$CASE/postko-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_ai_scoring_rom.CurrentCompositePostKO -v
```

`--build` verifies the canonical object, source/builder/loader hashes, compiler
record, relocations and payload correspondence. It reports compilationfalse
and reused-build-verifiedtrue. Alternatively `--readback-only` executes the
byte checks/scenes with that provenance claim explicitly absent; this mode is
separately exercised on EN. Report output cannot alias an input/build artifact.
Private unit inputs missing from the stated pattern explicitly skip.

### Native window, source recipe and regional readback

| Material | RAM / extent | Proof |
| --- | --- | --- |
| Selector | `02258800–02258BA0`,928 B | Complete V4 window plus source scoring sites equals current |
| Scoring sites | `02258938`,6 B; `02258944`,2 B | Eight declared bytes, five changed values |
| Scalar calls | `02258920`, `02258930` | Actual BLs to `0225264C`; real nested tail returns |
| MaskOfFlagNo | `020726C0–020726E0`,32 B | Actual Thumb loop; tested party indices0–5 |
| Native math | `020F2998–020F2BA4`,524 B | Actual ARM division reached through the scalar |
| Current Fairy helper | `023D746C`,148 B | Canonical verified payload/ELF reused from flags case |

Current selector SHA-256 is
`d2cfa7a4d31541559846b971bce5ad0547b0118cf12544d7ca52cdfe617369c2`;
common retail EN/base11/V4 preimage is
`45b8c7da8e9c25d38616d0524c824098182e48d807fde80da59a4e082569da84`.
Changed addresses are `02258938`, `0225893A`, `0225893D`, `02258944`, `02258945`.
The HG-B13 flag-mask change is outside this928-byte window and remains a
separate source dependency already qualified by the flags case.

Raw y9/FAT and independent project/ndspy BLZ readers identify overlay12,
file12, RAM base`022378C0`, decoded226176 bytes, BSS0. Current encoded spans are
EN`08314200–0833B940`, IT`08800000–08827740`. Current compressed and decoded
hashes/footer are the same documented in the flags case and are recorded again.
There is no direct encoded physical position for a decoded instruction. The
resident148-byte owner is physical`00126D2C`; ARM9/header/autoload mappings are
recorded independently. Only hashes, addresses and synthetic fixture observations
are emitted, not retail code/chart dumps.

Retail IT instead starts this function at`022587A0`, raw SHA-256
`ed351f39b3793abe77c0f1069fc77bff022194e421c8e696a9ce31197ef023ef`.
Twelve Thumb BL fields differ because the caller shifted while their ARM9
targets did not: nine calls to `GetMonData` at`0206E540`, three to mask`020726C0`.
Each actual target is decoded and checked before comparison copies normalize
those fields. The bounded120-byte GetMonData body is identical across inputs,
SHA-256 `7d88f5974d9ca615e5602e1e9b89a594f6fc8e78d4c36cf5660f7cc9f12f02b0`;
its downstream encrypted-mon implementation is not executed here. The complete
32-byte mask SHA-256 is
`da266f8eefce9cbb52a195196c3e0897cbc84b5af29871c7bd834fa3e8992a78`.
After those verified fields, the entire old parent matches. This establishes
bounded regional correspondence, not a universal address translation.

Two current upstream BLs are verified: overlay10`022205FE`, overlay12`0225F8E8`.
They correspond to trainer AI and opponent-controller use. This case checks
those static links, not every possible indirect caller or natural activation.

### ABI, models and state flow

The entry takes BattleSystem pointer in r0 and battler ID in r1. It pushes
five registers (20 B) and allocates`0x94` (148 B), a168-byte parent frame.
Synthetic current/pending party indices live at ctx+`219C`/`21A4`; party slots
model species, HP, types and moves. Each candidate calls the real scalar twice,
returns to`02258924`/`02258934` and retains the full sum for the unsigned best
comparison. `[sp+0x48]` holds best; `[sp+0x4C]` still receives only the low byte.
Strict `best < score` preserves the first candidate on a tie.

A high type score still needs a super-effective move; otherwise the candidate
is excluded and the scan repeats. Eventually stage two uses modeled damage
and may reuse the last narrow scratch word. Correcting overflow can change
elimination order and therefore which candidate supplied that word. This is
not a claim that every stage-two outcome is unchanged. Stage-two damage
truncation itself remains outside this patch and this case's acceptance.

The runner subclasses the existing
[`test_ai_scoring_rom.Native`](../../sgp131/test_ai_scoring_rom.py) scenario/query
bench. Its default historical V4 behavior is unchanged. The current subclass
loads only verified ARM9 segments and decoded overlay, uses eight distinct
callee-register cookies, requires actual PC/SP/Thumb return, checks carry,
stack canaries, unchanged battle context and all initialized code/data. Guest
writes stay within a4KiB stack fixture; modeled outputs are separately bounded
to stack words. Executed/read ranges and model arguments are recorded.

The configured15 query models cover battle/context, partner/target selector,
party/mon queries, battler type/ability/item, move type, effectiveness flags,
field side, damage and modifiers. Names/native entry addresses appear in the
JSON model registry. No model replaces scalar, division or mask. The target
selector updates a declared deterministic RNG model: comparing its call/order/
seed is not execution of the game's RNG. The subclass explicitly supplies
ability0; no abilities/items are exercised. Scenario species/types are synthetic,
not read from the personal NARC or a trainer fixture.

Two additional scenes remove the effectiveness-flags model, leaving14 configured
query models (eleven distinct model names actually reached in those scenes).
The actual flags function and resident helper execute and return to`02258A00`.
Per-call records capture move/type, flag pointer/output and nested ABI. The
first scene requires Fairy→Dragon flags2. The second requires Dragon→Fairy/Dragon
flags8, then Ice→Fairy/Dragon flags2, in that exact order. The slot is1 in both.
These are isolated integrations, not two natural encounters.

### Results and falsifiers

Per language:13 default scenes cover180-vs320, ordinary non-overflow, first-on-tie,
narrow stale fallback, changed elimination order, rejected high candidate,
four battle shapes with excluded slots, empty/current-only and one reserve.
Two scenes connect native flags. Four further invocations exercise wrapping,
an ordinary differential, the superseded wide-scratch variant and old flags
mask:19 invocations total.

For180/320, current picks slot4, scratch values180/64; wrapping picks slot2 with
compared values180/64. With two320 candidates and no effective moves, current
scratch64 leads to slot4. The old two-NOP variant stores320 and picks slot2;
the narrow-scratch oracle rejects it even though return/ABI are valid. An
ordinary non-overflow control preserves choice, comparisons, scratch, recorded
query log and modeled RNG seed against the wrapping variant.

Independent review found that final slot alone missed an old-mask regression.
A RAM-only mask12→4 still picks slot1 but returns Dragon flags10, accepting the
immune move and skipping Ice. The earlier same-slot oracle passed it. The
strengthened oracle requires outputs8→2 and exact call order/count, rejects the
mutant, and the normal constructor also pins the full current flags window.
Only an explicitly labelled counterexample fixture can bypass that pin.
Four public unittest methods cover current arithmetic, scratch counterexample,
native flag connection and this same-choice falsifier in both languages.
Nine structural negatives reject parent/dependency, regional-call/body and chart/
flags mutations. Original ROMs, assembly and canonical artifacts are untouched.

Maximum observed stack depth is192 B with modeled flags and216 B with native
flags; these are scenario bounds, not global game stack requirements. Native
mask indices remain0–5; its assert path for indices≥32 is not entered.
Final EN/IT runs exit0 in1.475/1.617s with OS peak RSS203,505,664/209,731,584 B,
under1GiB. These are host proof costs, not device decision timings. Logs are
bounded2MiB, no ROM build or capture. Historical random campaigns are not repeated.

- **Documented provenance:** exact inputs, scoring source recipe, composition,
  native reference and reused resident build receipt.
- **Reconstructed binary correspondence:**928-byte parent, eight declared patch
  bytes, current scalar/upstream calls and verified regional references/bodies.
- **Demonstrated semantics:** declared isolated decisions, actual scalar/math/
  mask and two native flags integrations, with outcome and intermediate falsifiers.
- **Observed activation:** explicit native entry under modeled external state.
- **Unattributed or untested links:** original native compiler, encrypted-mon/
  party implementation, natural trainer/controller entry, actual RNG/damage,
  general AI decisions, full ability/item/type domain, timing, SAVE and hardware.

The reusable result is stricter intermediate-state attribution of a caller,
including a same-output counterexample that final-choice tests conceal. There
is no supported game optimization or new AI patch. Another independent gap is
the Conversion2 consumer's compiled replacement, row domain and RNG transport;
this post-KO case does not qualify that different path.
