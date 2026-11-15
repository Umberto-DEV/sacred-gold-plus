# U-turn and Shell Bell: source and installed script order

The installed pivot script checks its item effect **before** the added item
snapshot and the later flinch consumer. This contradicts the premise that this
particular pivot item check first reads the damage field after the flinch hook
clears it. It does not demonstrate healing, establish universal compatibility
or repair either [recorded U-turn defect](uturn-source-rom-1.3.2.md).

This is a static attribution and a bounded counterproof. No new guest CPU,
compiler invocation, ROM build, game mutation or save operation was needed.
The useful result is avoiding a new bug claim from an incorrect dependency
order, while identifying the exact handler and a reproducible check.

## Required inputs and provenance

Use your own current Plus r4 inputs:

| Language | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Both identify internally as IPKE/revision0. The selected script, handler and
consumer research window are byte-identical between these two inputs, without
regional normalization. This does not make retail Italian HGSS interchangeable.

Source references are the clean productive
[fork at cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c)
and [PRET HeartGold at 6bf138d6035aa6b43d6f8f4132a12df70f86dcec](https://github.com/pret/pokeheartgold/tree/6bf138d6035aa6b43d6f8f4132a12df70f86dcec).
The reader pins the participating files and complete C definitions. The newer
reference moves `battle_util.c`/its header to
`src/battle/overlay_12_0224E4FC.c` and its corresponding header.

`BtlCmd_CheckItemHoldEffectOnUTurn` is the same 320-byte definition in both
references, SHA-256 `77da05c9c5897f64a8b34f80063c03326a22a2fb03b997840973dc42989ac1d9`.
`CheckItemEffectOnUTurn` is 2615/2614 bytes and differs in the later Sticky Barb
field spelling, `moveData.flags` versus `moveData.unkB`. The Shell Bell branch
is unchanged. Neither whole-file drift nor this field rename proves binary
identity of the complete consumer.

The source branch requires hold effect88, successful move, nonzero signed
`shellBellDamage`, distinct attacker/target and living attacker with partial
HP. It calculates `DamageDivide(-shellBellDamage,modifier)`, sets the temporary
battler and outputs `BATTLE_SUBSCRIPT_RESTORE_A_LITTLE_HP`. Those are source
conditions, not newly observed healing. The original Metrowerks C build is
not reconstructed here. The installed helper/script composition and its two
known compatibility failures retain their separate U-turn case.

## Native dispatch, handler and ABI

The qualified raw header/Y9/FAT reader locates overlay12/file12, RAM
`022378C0`, decoded226176 bytes, BSS0. Its BLZ stream is161600 bytes:
EN `08314200..0833B940`, IT `08800000..08827740`.
Packed SHA-256 is `27ae58f35bb0ce6df5c6c68ef24fb8034901cc217ea133f9e28fd28b7afd4d8c`;
decoded SHA-256 is `6c95f5d2db58ebb3da1463c6b12bc1e47e7267cd0ccd8cb7905bf2568afb729e`.
Raw decoding agrees with ndspy. A decompressed instruction has no linear
physical ROM offset inside that compressed stream.

The source command table has225 entries. Its inline ASM comments must be
stripped before counting: ignoring commented `.word` lines silently drops five
commands and shifts the IDs. Table RAM`0226C6C8`, entry213, contains the odd
Thumb pointer`02245229`; entry214 starts the next handler at`0224525C`.
The selected52-byte handler has22 instruction starts and no embedded pool,
SHA-256 `f1fde9c9eda08a9112b9c1d09c41c66cf949b6910adb20a4acf6674f8070cd72`.

| BL site | Target | Source/byte relationship |
| --- | --- | --- |
| `02245232` | `02245508` | Increment script cursor by one word |
| `02245238` | `022454E8` | Read jump operand into saved r6 |
| `02245248` | `02257FA0` | Item consumer candidate `(BS,CTX,CTX+138h)` |
| `02245254` | `02245508` | Apply jump only when consumer returns FALSE |

PUSH/POP preserves r4/r5/r6 and LR/PC, a16-byte frame. The third BL receives
r0=BattleSystem, r1=BattleContext, r2=an `int *` output at CTX+`0x138`.
That is tempData/variable43, distinct from CalcTemp/variable9 at CTX+`0x134`.
The handler returns FALSE to the VM regardless of the consumer result; its
own boolean is not a healing result.

The new52-byte handler was also located independently in all eight exact
retail → base1.1 → V4 → r4 inputs, EN and IT. Its bytes are identical without
normalization. Retail IT has handler`022451C8`, table`0226C668` and actual third
BL target`02257F40`; the other seven have the current addresses above. The
locator finds a unique exact byte profile and a unique aligned consecutive
dispatch pair. It does not guess a global regional shift or transfer the whole
consumer's identity from its entry address. This establishes the selected
handler's inherited provenance, not an original C rebuild.

The768-byte lookahead at`02257FA0` has SHA-256
`5cc3fb074a0f3f55b3c2419c637877ce91c9b365dd4b73f21bdbd2ee6218ff4a`.
It is a research window containing code and data, **not a proven function
extent or an instruction-admission range**. Independent static review of its
first branch agrees with source effect88, status mask`2000h`, signed-damage
field, HP guards, division and output script. This does not execute those paths
or qualify pathological arithmetic such as INT_MIN or modifier0.

## Installed prefix and the ordering counterproof

NitroFS `a/0/0/1`, file130, contains297 members. Pivot member175 is800 bytes,
SHA-256 `eaa254c435e16397b233c8f3e796f1655003358e4252bcc57352f3ca89b58c9a`.
The project insertion begins at byte`3C`, word15. Its full source recipe is
already qualified by the U-turn case; this reader does not apply it again.

| Word | Command | Declared successor or branch |
| ---: | --- | --- |
| 0 | CheckBlackOut | Next3 or final End199 |
| 3 | TryReplaceFaintedMon | Next7 or End199 |
| 7 | TriggerAbilityOnHit | CallFromVar9 or skip to11 |
| 9 | CallFromVar variable43 | Next11 after return |
| 11 | TriggerHeldItemOnPivotMove, opcode213 | CallFromVar13 or skip to15 |
| 13 | CallFromVar variable43 | Next15 after return |
| 15 | Project snapshot marker | Begins after both item-command outcomes |

The decoder consumes complete command widths from the macro definitions.
It does not search for a numeric213 anywhere in the byte array: operands can
contain that number too. It validates typed words, boundaries, forward signed
relative branches and final End224 at word199. Both item-command outcomes join
before the snapshot; early failures leave before reaching it.

Opcode213 and healing **subscript ID213 are different namespaces**. Item
ID213 is yet another namespace. Their coincident numbers do not imply a loop,
a second item check or an observed heal.

The newer PRET pivot source places this item processing before replacement.
Its move effect configures the pivot indirect script in the earlier AfterDamage
controller states; the flinch check is later at state6. Existing evidence has
important boundaries: the [snapshot producer](uturn-producer-source-rom-1.3.2.md)
starts at word15 and does not execute this earlier prefix, while the
[AfterDamage case](afterdamage-source-rom-1.3.2.md) uses neutral indirect scripts,
not a natural complete pivot175 run. Static order is sufficient to reject the
proposed late-consumer premise, not to replace those missing runtime proofs.

## Reproduce and falsify

Run from the repository root using Python, Git and the project's ndspy/Capstone
dependencies. Parser tests use only the Python standard library. Supply your
own clean pinned source trees and exact ROMs; no compiler or emulator is needed.

```sh
python3 source/features/type-consumers/tools/rileggi_uturn_shellbell.py \
  --rom /path/to/plus-en.nds --it-rom /path/to/plus-it.nds \
  --reference /path/to/productive-hgss --heartgold-ref /path/to/newer-pokeheartgold \
  --json /path/to/private/fresh-uturn-order.json
python3 -m unittest discover -s source/features/type-consumers/test \
  -p test_uturn_shellbell_order.py
```

`--it-rom` is optional; EN is required. Exit0 means the exact static profile and
order checks passed. It is not a game-compatibility verdict. Output must be a
fresh private file outside`source/`. The generated JSON contains selected ROM
code/data slices for independent review; **keep it local and do not publish it**.
The repository contains source, hashes and owned synthetic tests, not these
extracted fixtures. Original ROMs/saves are never written.

Twelve owned tests cover inline-comment ID shifts, false/duplicate labels,
ambiguous table rows, command-versus-operand namespaces, invalid/truncated words,
branch targets inside operands, negative/oversized jumps, variable/marker
confusion, Thumb BL versus BLX, ambiguous legacy matches and an invalid successor
exactly one past the overlay end. Independent review applies further parser
mutations to the saved projections. A guarded readback also passes with CPU and
assembler imports and compiler processes forbidden; only pinned read-only Git
queries are permitted.

For a historical input, obtain its expected hash/size from the project's
[retail catalog](../../localization/languages.json),
[base input profile](../../features/fairy-ai/tools/attribuisci.py) or
[V4 catalog](../../sgp131/baseline.py). Reuse the public locator with your own
current report. This reads only overlay12 and compares the selected handler:

```sh
python3 - /path/to/legacy.nds EXPECTED_SHA256 EXPECTED_BYTES /path/to/private/current-order.json <<'PY'
from pathlib import Path
import importlib.util, json, mmap, sys
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
T = load('source/features/type-consumers/tools/rileggi_uturn_shellbell.py', 'order')
G = load('source/features/fairy-ai/tools/attribuisci.py', 'overlay_reader')
rom, digest, size, current = sys.argv[1:]
profile = bytes.fromhex(json.loads(Path(current).read_text())['rows']['EN']['handler']['code_hex'])
assert T.sha(profile) == T.HANDLER_SHA
with Path(rom).open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as raw:
    assert len(raw) == int(size) and G.sha(raw) == digest
    image, record = G.overlay(raw, 12)
    print(T.locate_handler(bytes(image), int(record['ram'], 16), profile))
PY
```

A unique profile is required; duplicate code/pointer matches, unaligned dispatch
pairs and a successor outside the overlay are rejected. Two extra owned
ambiguity checks and the end-boundary regression cover these admission rules.
The historical command does not decode or execute a whole consumer or script.

## Result and practical limit

The finite static ordering question is resolved without another guest campaign.
Source provenance, native dispatch/handler bytes and installed script boundaries
are documented. Original C binary reconstruction, consumer semantic equivalence,
actual item-request/heal execution and natural whole-battle activation are not
claimed. No new Shell Bell healing-loss defect is established, and the two
existing U-turn defects remain unfixed.

Any later correction needs a regression tied to the actual affected consumer
and lifetime. The ordinary after-move item consumer explicitly excludes the
pivot condition and must be attributed separately; it cannot be substituted
for this one because its C branch looks similar.
