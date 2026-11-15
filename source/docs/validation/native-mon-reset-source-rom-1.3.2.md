# Native complete move and PP-Up Reset: source to exact ROM execution

`MonSetMoveInSlot_ResetPpUp(mon,310,0)` now has a complete host attribution,
including its four actual child calls in one uninterrupted context. This joins
the [Box move caller](native-box-move-caller-source-rom-1.3.2.md) and
[Mon setter](native-mon-ppup-setter-source-rom-1.3.2.md) without concatenating
separate CPU results or resetting memory between phases. Three original Reset
calls passed on their first attempt:105568 instructions total,32 transcript
falsifiers, three cached-input controls and observer OFF.

## Finite question and inputs

Does the installed Reset assign move310 to slot0, zero that slot's PP-Up,
recalculate PP with Up0 and publish the final PP through native setters,
including the separate party100/PID and Box128/checksum cipher transactions?
Two owned Mon236 inputs start with Up3 or0, PID`0x4000`, flags0, valid checksum,
currentPP15 and heldItem0. A third cell repeats Up3 with observation OFF.
These are generated cryptographic fixtures, not saves or legalized party records.

Use your own required ROMs and source references. The exact current inputs and
productive source/header hashes are those in the
[Mon setter input table](native-mon-ppup-setter-source-rom-1.3.2.md#inputs-provenance-and-compilation-limits):
EN152786844 bytes/SHA-256`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
IT159029760 bytes/`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both use IPKE/revision0 and plain ARM9 ROM`0x4000`, RAM`0x02000000`,
size`0x12B8E4`, entry`0x02000800`. Do not apply the plain mapping formula to
compressed historical inputs.

The productive HGSS fork is pinned at
[cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
The complete290-byte C definition is in`src/pokemon.c` at line3117, SHA-256
`e80f65e6bfd87861d55399c0bade3e8c3beabf840a4bcf563cebaa68f53101cd`.
Its signature is`void(Pokemon *,u16,u8)`. The definition is unchanged in PRET
HeartGold`6bf138d6035aa6b43d6f8f4132a12df70f86dcec`, as verified by the
[source-definition comparator](../../features/trainer-strategy/tools/confronta_box_move_pret.py).
Definition extents exclude trailing newline and are not callsite fragments.

This case executes retained native HGSS bytes. It authenticates the previously
recovered assembly recipes and30 SDK ELF objects plus the signed-DIV object;
no new compiler invocation or installer is involved. Original Metrowerks Thumb
C objects/maps and a matching original C rebuild remain unavailable. Source
provenance, installed bytes and finite semantic equivalence are demonstrated
separately; a matching original C compilation is not claimed.

## Locations, calls and observable behavior

The new caller is`0x020714B0..0x020714E8`,56 bytes/24 Thumb starts, current
plain ROM offset`0x754B0`, SHA-256
`3e8f6c199fa28d8ecedf54d8ec64dff4e87489670785ccf96e3d34c3de4e579f`.
The next4 bytes at`020714E8` are the LDR/BX Mon veneer; the4 bytes at`020714EC`
are its literal`020714F1`, not instructions. The resource union contains
1132 Thumb code bytes/512 starts, retained SDK code and the524-byte DIV body.
Data tables and pools have separate owners and are excluded from fetch admission.

| Reset BL | Target | Significant arguments | Child SP / LR |
| --- | --- | --- | --- |
|`020714BA`|`020714E8`→`020714F0`|Mon,310,0|T−24 /`020714BF`|
|`020714CA`|`0206EC40`|Mon,62,T−24|T−24 /`020714CF`|
|`020714D2`|`0207332C`|310,0|T−24 /`020714D7`|
|`020714E0`|`0206EC40`|Mon,58,T−20|T−24 /`020714E5`|

The Mon setter defaults directly to Box-internal`0206EDE8`; its row62 at
`0206EEB8` (`C602`) selects`0206F104`, and row58 at`0206EEB0` (`B602`) selects
`0206F0F4`, each relative to PC base`0206EE3E`. The Mon calls do not invoke
the outer Box API at`0206ED70`.

| Up3 stage | CurrentPP / PP-Up | Box checksum key |
| --- | --- | --- |
|Owned input|15 /3|`02AB`|
|First Box caller|24 /3|`02B4`|
|Mon62|24 /0|`02B1`|
|Second MaxPP then Mon58|15 /0|`02A8`|

The intermediate PP24/Up0 state is required by this caller. The standalone
Mon62 proof started with PP15 and cannot supply this phase's expected input.
Up0 remains PP15/Up0/key02A8, but its idempotent writers and both NARC reads
must still execute. Both whole Mon outputs have SHA-256
`02a5249820ab97db2799b0e18ee906b3154915a4f42a6084bce0be4a761c9beb`.

Owned entry: R0=Mon`022F0000`,R1=310,R2=0; R3..R12 distinct cookies,
T=SP`023FD000`, odd return LR`022F0181`, CPSR`6000003F`. Reset pushes16 bytes
and allocates8. Its two Value words start untouched: STR`020714C2` publishes
zero at T−24; STR`020714D8` publishes15 at T−20. Each setter reads one low
byte, while both Reset publications are native four-byte stores.

Leaf58 runs twice at the same PCs and Mon+80, with distinct live contexts:
Box Value=T−56/SP=T−176, then Mon Value=T−20/SP=T−152. Leaf62 uses
Value=T−24/SP=T−152 and Mon+84. The private cipher seed lives at T−80 for
the Box calls and T−48 for the Mon calls. Reset's live24-byte frame is fenced
before delegating to legacy SDK guards, preventing their old TOP fallback from
admitting arbitrary reads or writes into the live caller frame.

| MaxPP invocation | FILE client | Parser local | Buffer16 | Peak below T |
| --- | --- | --- | --- | ---: |
|Inside the first Box caller|T−208|T−232|T−96|712|
|Called by Reset|T−176|T−200|T−64|680|

The second FILE does not start as A5 fill. Its18 words before Init are derived
from preceding native writers:9 Box/Mon words, one untouched A5 word,6 saved
register words from the first NARC parser, then2 words from the first Box PP
cipher frame. The six saved words include the original Up3/Up0 value. Allocating
the Mon locals did not clear their unwritten bytes, and the second parser's
push starts just above this FILE. Independent instruction/lifetime review
confirmed this correction before original execution. Neither a host memset
nor copying a standalone FILE fixture is permitted.

The whole function returns to its real stop: R0=`2B9B`,R1=0,R2=`4AA02329`,
R3=`0206ECCD`; R4..R11 and SP retain entry values, IP=0, LR=`0201FF59`,
CPSR=`6000003F`. This is a void ABI residue, not a PP return value.

## Reproduce with your own inputs

Use the project Python environment: verified ndspy4.2.0, Capstone distribution
5.0.9/module5.0.7 and Unicorn2.1.4/CPU model17. Model17 establishes selected
instruction semantics, not ARM946 hardware timing. For source references,
objects JSON and the two recovered recipe directories, first follow the
[Box caller prerequisites](native-box-move-caller-source-rom-1.3.2.md#reproduction-and-success-criteria).
Reuse matching retained objects; do not recompile them without a new question.

From the repository root, use fresh private paths outside`source/`:

```sh
python3 source/features/trainer-strategy/tools/rileggi_mon_reset.py \
  --rom /path/to/plus-en.nds --it-rom /path/to/plus-it.nds \
  --json /path/to/private/resources-en-it.json
python3 source/features/trainer-strategy/tools/qualifica_mon_reset_limits.py \
  --json /path/to/private/owned64.json
python3 source/features/trainer-strategy/tools/congela_mon_reset.py \
  --rom /path/to/plus-en.nds --json /path/to/private/input.json
python3 source/features/trainer-strategy/tools/attribuisci_mon_reset.py \
  --mode prepare --rom /path/to/plus-en.nds \
  --reference /path/to/productive-hgss --objects /path/to/private/objects.json \
  --recipe-dir /path/to/private/sdk-recipe --div-recipe /path/to/private/div-recipe \
  --input-contract /path/to/private/input.json \
  --qualification /path/to/private/owned64.json --out-dir /path/to/private/prepared
```

The standalone EN+IT resource audit is supplemental. Freeze and prepare each
generate the same fresh **EN-only** receipt and bind its exact serialized hash.
An EN+IT audit has additional IT fields and intentionally a different whole
receipt hash; it is not silently substituted as the frozen input authority.

Change`--mode prepare` to`--mode matrix` with a new output directory to run the
three top-level Reset cells. Each contains four child calls: there are three
Reset executions, not four. One Uc and one `emu_start` per Reset, timeout1s,
cap65536; no runtime host write or callee service model. Raw is saved before
acceptance. Then run`--mode verify --raw-dir /path/to/private/matrix` with
another fresh`--out-dir` to rejudge the saved records without CPU/compiler.
ndspy/Capstone remain required; this verifier is not stdlib-only.

The new cap is justified by the35199-step finite path. Its predictor differs
from the qualified32k parent only in the outer default/maximum; its producer
only in two cap literals. Complete AST comparison guards those deltas.
The per-ARM limit remains`min(8192,remaining)` and completion uses the new local
CAP65536. A complete path must leave room for the return callback:65535 passes;
65536 reaching the endpoint without that callback is rejected. Six owned tests
cover40001 steps ON/OFF, tiny ARM with a large residual, both boundaries and an
infinite capped loop. These tests load no ROM; their OFF hashes label source
forecasts separately from absent native per-instruction observations.

[`rileggi_mon_reset_lineage.py`](../../features/trainer-strategy/tools/rileggi_mon_reset_lineage.py)
accepts`--retail RETAIL --base BASE11 --v4 V4 --rom CURRENT --language EN`
(or IT) and`--json FRESH_PRIVATE_JSON`. It locates only the newly added56-byte
caller and decodes its four BL targets. Earlier callee-lineage coverage stays
separate. Across eight exact inputs those56 bytes agree: two retail owners
are BLZ with null plaintext physical offsets; six plain owners have independent
direct reads. This is bounded equality, not whole-ROM build equivalence.

ROM-free checks, including the live-frame and shared-PC counterexamples:

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_mon_reset_*.py'
```

## Results, counterproofs and limits

| Cell | Total instructions | Thumb / ARM | Unique starts |
| --- | ---: | --- | ---: |
|Up3|35199|22818 /12381|1343|
|Up0|35170|22818 /12352|1314|
|Up3 OFF|35199|22818 /12381|1343|

Each has7808 reads,4624 stores,712-byte peak stack and26 pages/106496 bytes.
The same complete final maps converge to
`19418cef396fc8a5f9382c6f7943376d8a3b8ec000fa4746ff8ef832c1b04573`;
the first DIV's different branch still requires29 extra original instructions.
The verifier checks840 local-seed stores and840 payload halfword stores,
including200 party stores,576 checksum reads,20 block selectors, two complete
SDK callgraphs and14 actual memory-read callbacks. Both PP15 members come
from the unchanged ROM-derived archive, without a constant-return model.

All observed full16/next-PC states, reads, store preimages, final pages and
inverse replay agree with the frozen source forecast. OFF has the same
endpoint/counters and no observation journals. Thirty-two raw transcript
mutations are rejected, including a counter with matching endpoints and forged
counts, skipped idempotent Mon62, missing party/NARC phases, wrong Value/seed/
SP/key/width, A5-normalized FILE preimages and injected host writes. Three
canonical-relative FAT/FNT/ROOT mutations fail before the source loop.

Independent mixed-ISA review, without the benchmark predictor or Unicorn,
confirmed70369 full16/next-PC states,15616 reads,9248 stores, all26 pages in
forward/inverse replay,81 current/frozen runtime sources and all32 mutations.
No original API was rerun to tune an expectation. First matrix7.038s/503742464
bytes peak RSS; rejudgment5.252s/521043968 bytes; CPU/assembler/compiler-denied
rejudgment5.304s/518619136 bytes. These are host validation costs, not game speed
or DS heap measurements. The case budget was reduced after serialization
measurement to48MiB output/256MiB disk peak, with at least10GiB free afterward.

The public additions are the bounded64k derivative, owned qualification/cache,
Reset reader, two-key fixture, contextual math/journal views, access owners and
prepare/matrix/verify CLI. Source fragments and raw endpoints are not enough
without the proven lifetime and intermediate conditions. Scope excludes other
moves, slots, PIDs, flags, checksum errors, Rotom/form callers, the full trainer,
natural CARD/gameplay, Italian guest execution, saves/hardware and original
MWC/full-ROM C reconstruction. No game behavior, ROM, ABI, ID or save changed;
no game optimization or recovered DS memory is claimed.
