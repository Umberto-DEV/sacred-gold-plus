# Native move getters outside the Party cache

The [Party attribution case](party-source-rom-1.3.2.md) recorded 36 native
getter spans outside its cache constructor. They belong to two existing HGSS
consumers and a nested PP lookup. They are not 36 observed Party-cache fallbacks.
The same raw observation resolves this question without another gameplay run,
ROM build, performance campaign or game change.

## Inputs and professional checks

Use your own exact r4 EN/IT image from the
[game contract](../../distribution/game-1.3.2-r4.json). The standalone
[verifier](../../features/native-core/tools/attribuisci_getter_mosse.py)
authenticates complete SHA-256 and size before assigning addresses. P01 records
those identities, the E8 observer identity, route, controls and raw provenance.
The optional trace must already have that provenance or an independently
qualified equivalent. Keep all ROMs, extracted data, saves and raw traces private.

The checks distinguish inherited native code from compiled Plus payloads,
follow both caller→callee and observed LR→instruction paths, and test cases
that can contradict the source attribution. An independent Sol 6.1 review
examined the actual code, source and parent/argument records. Missing original
compiler/object provenance remains a named limitation, not an inferred match.

The raw starting material is the exact overlay 12 image, header/y9/FAT and ARM9
sections; the three caller LRs; complete register-span records; source at pinned
revisions; and move records from the owner's NARC. Reports are an index to these
materials, not a substitute for inspecting them.

Methods are incremental retail→inherited base→r4 comparison, Thumb branch and
switch-table decoding, source/layout triangulation, isolated execution of actual
installed instructions, synthetic predicate controls and falsifiers on the
observation. ndspy, Capstone and Unicorn reuse the existing project toolchain.
No new observer or test framework is introduced.

## The three observed paths

| Observed entry | Caller LR | Attribution | EN spans |
| --- | --- | --- | ---: |
| `0x0207332C` `GetMoveMaxPP` | `0x0224EF7D` | `GetBattlerVar`, MAX_PP IDs 39–42 | 12 |
| `0x02073314` `GetMoveAttr` | `0x0207333D` | Nested attr 5 lookup inside those max-PP calls | 12 |
| `0x02073314` `GetMoveAttr` | `0x022688DD` | Type-icon refresh in `BattleInput_LoadFightMenuText`, attr 3 | 12 |

The instruction for a captured Thumb BL return is at `LR - 5`. These are
`0x0224EF78`, `0x02073338` and `0x022688D8`, and their decoded targets are the
entries above. The verifier checks the real instructions; it does not infer
the target from a function name. The 12 PP children have the same move ID as
their parent, attr 5, and strictly nested entry/exit order and frames.

Three groups of four max-PP calls occur at frames 7268, 7789 and 8389. The
type lookups run across 7268–7271, 7789–7792 and 8389–8392. Those are events in
one EN route, not independent timing samples. A sentinel parent means that
no instrumented parent was observed; it does not mean the function had no caller.

### Max PP: native switch and data layout

`GetBattlerVar` is at `ov12:0x0224EDE0`. It derives a battler record from
`ctx + 0x2D40 + battlerId × 0xC0`. Its signed halfword switch table routes
IDs 39, 40, 41 and 42 to `0x0224EF6A`. That branch subtracts 39, loads a move
halfword from `mon + 0x0C + 2 × index`, loads PP-Ups from
`mon + 0x30 + index`, calls the native max-PP getter and returns.

This matches `GetBattlerVar`'s `BMON_DATA_MAX_PP_1..4` branch in
`src/battle/battle_util.c` and the ID definitions in `include/constants/battle.h`
at source-only reference `cb614ad23449d5852b40321dc409c4143872b35c`.
`movePP` in this structure is the PP-Up field; `movePPCur` is distinct.
Interpreting the name alone as current PP would misidentify the ABI.

The native getter clamps PP-Ups to three, reads attr 5 (record byte 6), applies
the PP increase and returns an 8-bit value. Its internal BL explains the second
set of 12 spans; they are nested work, not 12 additional independent max-PP
operations. The trace's PP-Ups were 0 in three calls and 3 in nine calls.

### Type icons: a conditional native refresh

`BattleInput_LoadFightMenuText` begins at `ov12:0x0226885C`. Its loop compares
incoming move IDs with the display object's retained IDs. The block at
`0x022688CA` skips the getter if the IDs agree, and also skips it if the incoming
ID is zero. Otherwise it selects attr 3 and calls `GetMoveAttr`. The continuation
loads type-icon character data into the existing icon destination, frees the
temporary char data, and later copies the incoming move display record.

This combination of changed/nonzero predicates and icon-loading continuation
matches `src/battle/battle_input.c`'s named function, rather than another nearby
consumer that also reads move type. It distinguishes native display refresh
from Party's new cache helper. The helper is synchronous and does not own these
icons, text windows or graphics allocations. No lifetime optimization follows
from merely seeing these calls.

## Byte provenance and mapping

Both functions reside in overlay 12, RAM `0x022378C0`, decoded length 226176.
Its FAT file ID is 12 and the stored image is backward-LZ compressed. The tool
reports physical FAT extent, compressed size/flags, decoded hash and logical
window offsets for each input; a compressed instruction has no simple direct
physical-byte offset.

| Native window, including switch/literals | Bytes | SHA-256 in EN retail and normalized base/r4 EN/IT |
| --- | ---: | --- |
| `[0x0224EDE0,0x0224F168)` | 904 | `33fc43e247512e55c9980ef668d1350ef1f66b9ffb92da2cfd4b428c9e3d2b8e` |
| `[0x0226885C,0x02268A64)` | 520 | `de8f0becf35db49ed4afa7831f349fd742ab0432de4d14bddcce96e88fd95ac2` |

The complete windows are identical in EN retail, both inherited 1.1 bases and
both final r4 images. Therefore they are native inherited code in this scope,
not new Plus payloads. Retail IT has an overlay base and unique predicate
blocks shifted by `-0x60`; the full shifted windows differ. A small matching
predicate is not full-function equivalence for that regional revision.

No original HGSS object, linker map or original compiler rebuild is supplied
by this case. Pinned C explains the tested operations and layouts, while the
binary correspondence above is ROM-to-ROM. These are separate conclusions.

## Reproduce and falsify

Activate an environment with [project dependencies](../../requirements.txt).
The measured host used Python 3.14.7, ndspy 4.2.0, Capstone 5.0.9 and Unicorn
2.1.4. The tool executes the actual ROM code in Unicorn; no C recompilation or
proprietary compiler is needed for this narrower check. From the repository root:

```sh
python3 source/features/native-core/tools/attribuisci_getter_mosse.py \
  --rom "$ROM_EN" --language EN --trace "$PARTY_TRACE" \
  --json "$PRIVATE_OUT/native-moves-en.json"
python3 source/features/native-core/tools/attribuisci_getter_mosse.py \
  --rom "$ROM_IT" --language IT --json "$PRIVATE_OUT/native-moves-it.json"
python3 -m unittest discover -s source/features/native-core/test \
  -p test_qualita.py -k QNativeMoveConsumerAttribution -v
```

Use a fresh JSON output path. `--trace` accepts CSV or lossless `.gz` and is
optional for ROM-only checks. An EN observation must not be presented as an IT
runtime capture merely because IT's installed functions are identical.

The isolated test starts at the real `GetBattlerVar` entry and follows its
switch for four battlers × four IDs × three move IDs × six PP-Up inputs = 288
cases per language. It executes native max-PP/attribute/division code and checks
result, return PC, SP, Thumb state and r4–r11. Only move-member transport is
replaced with the corresponding private ROM record, copied to the native stack.

Seven type-predicate cases exercise unchanged, zero and changed IDs using
actual instructions. Execution stops immediately after the real type getter
returns or at the compiled skip target. The graphics continuation is inspected
statically; its allocations, transfer completion and lifetime are not simulated
or certified by these predicate tests.

A local in-memory clone with a corrupted switch entry for ID 39 fails the
value/ABI check. Reversing the equality branch in the type predicate fails its
truth table. Trace tests reject wrong LR, parent, move, attribute, result,
completion and chronology. These counterexamples are verification tests, not
patches to the game. Unknown native caller paths are rejected rather than
silently attributed to either named consumer.

## Result and limitations

The 36 spans are accounted for: 12 native max-PP calls, their 12 PP attribute
children and 12 native type-icon refreshes. Normal execution is observed only
for the EN route inherited from P01; installed-code dispatch/predicate checks
also pass for IT. ROM-to-ROM identity is demonstrated for the full windows
listed above. Original C-to-object reconstruction, the complete graphics caller, unrelated
switch branches and regional retail-IT equivalence remain unproved.

There is no measured bug, reclaimed memory or accepted optimization here.
Removing the PP child would remove required native work; caching type icons
would require a separate ownership/invalidation and cost investigation. The
reusable result is a source/byte/caller attribution that prevents those events
being miscounted as Party fallback or independent work.
