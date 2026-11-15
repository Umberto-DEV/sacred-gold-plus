# Resident ANIM v4 and retired entry paths

The historical ANIM v4 payload remains byte-identical in r4 EN/IT, and its
current C recipe reconstructs all 752 code bytes. Its two original entry paths
have been replaced by ANIM2 and the later copy barrier. The entire allocation
is not shown to be unused: the v4 state guard still has explicit UI dependencies.
No bytes are removed or made available for reuse by this investigation.

This case follows the [source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom)
and the earlier [Party](party-source-rom-1.3.2.md) and
[native getter](native-move-callers-1.3.2.md) cases. It answers an existing
inventory gap without repeating animation, performance or save campaigns.

## Professional checks, raw inputs and method

A resident byte range is different from an active task, a data dependency or
free space. This case reconstructs source→compiled→installed bytes and follows
ROM entry paths back to the installers. It also searches for counterexamples
to the retired-entry attribution, including data references, misleading ISA
interpretations and unobserved indirect calls. Independent Sol 6.1 reviews
checked the bytes and the new reader separately.

Use your own exact EN/IT images from the
[r4 game contract](../../distribution/game-1.3.2-r4.json). Complete hashes and
sizes are mandatory. Raw material comprises ARM9 autoload sections, the overlay
table/FAT and decoded images, branch instructions versus literal pools, the v4
C/header and ELF, generated table/parameters/canary, current ANIM2 and copy-barrier
bundles, and their source recipes. Keep ROMs, extracted bytes, saves and raw
captures private. No new gameplay or memory mutation is needed for these checks.

Methods are targeted compilation with the real flags, complete-owner readback,
two overlay decoders, instruction/literal classification, source dependency
review and a bounded lexical reference scan. Existing wrapper and Settings
compiled-code tests support specific control/data dependencies. They are not a
new observation of v4 activation or a proof of global inactivity.

## Source and exact reconstruction

The v4 unit is [`anim_blob4.c`](../../features/anim/sorgenti/anim_blob4.c),
including `anim_idle4.c`, `sgp_anim4.h` and `sgp_chunk.h`. Its
[compiler](../../features/anim/tools/compila_anim4.py) targets ARM946E-S Thumb,
`-Oz`, freestanding/no-builtin/no-stack-protector/no-unwind/no-jump-tables,
with state/table/slot defines at `0x023D8E40`, `0x023D8E00`, `0x023D8E80`.
The complete compiler arguments are recorded in the generated manifest.
[`load_text`](../../features/anim/tools/carica_text.py) resolves internal Thumb
calls in ELF `.text`; no general linker or native SDK object is imported.

Apple clang `2100.4.1.1`, executable SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
reproduced code, public symbols, table, parameters and canary exactly.
This proves current reconstruction. The shipped bundle's
[`origine.json`](../../sgp12/build/anim/origine.json) remains an extraction
receipt from older EN/IT images; it is not silently rewritten as a historical
compiler receipt. Original source/executable provenance and a current exact
rebuild are separate records.

| Owner part | RAM range / size | Verified property |
| --- | --- | --- |
| Code | `0x023D8B00..0x023D8DF0`, 752 B | Exact rebuilt/shipped/installed bytes |
| Canary | `0x023D8DF0`, 16 B | Exact generated canary |
| Table and parameters | `0x023D8E00`, 64 B | Exact 32-byte table and 32-byte parameters |
| State | `0x023D8E40`, 64 B | Initial flags 0, guard byte at `+1` = `0x5A`, other bytes zero |
| Four slots | `0x023D8E80`, 128 B | Initial slots zero |

Code hash:
`06a031fd71b3225409845bea7abeca77c66227d0c266ba8dbfbca38eba3eb18b`.
Whole 1024-byte owner hash:
`565460511dd0d8e24b90cc6ab563d976a0ba6e3ecef1f321664c642b2a24b9c2`.
The two public Thumb symbols are `sgp_idle_task2 = 0x023D8BE5` and
`sgp_idle_stop = 0x023D8BD3`. Code and data retain their reserved addresses;
no ABI, setting or save identifier changes.

The reader reports the physical ROM offset through ARM9 module parameters and
autoload mapping, rather than subtracting the main ARM9 base blindly. Overlay
12 is independently decoded both by ndspy and the existing forward BLZ reader;
it reports physical FAT extent, RAM address and decoded hash. Compressed code
requires that mapping, not a guessed direct file offset for an instruction.

## The two original roots and their replacements

The [older installer](../../sgp12/blocchi/anim.py) placed v4 and installed two
roots in overlay 12. [ANIM2](../../features/anim2/tools/applica_anim2.py) replaces
them, and [maintenance](../../sgp12/manutenzione.py) subsequently inserts the
copy-ownership barrier. Composition preserves the old allocation deliberately.

| Site | Historical v4 role | Exact r4 state |
| --- | --- | --- |
| `ov12:0x0226200C` | Task callback literal `0x023D8BE5` | Literal `0x023DBC9B`, the copy-barrier wrapper |
| `ov12:0x02262032` | BL to v4 stop/cleanup | Native `ldr r0,[r4,#0x20]; movs r1,#4`, followed by native `Pokepic_SetAttr` |

The first site contains a pointer, not two executable Thumb instructions.
Disassembling it linearly produces plausible but irrelevant mnemonics. The
second is executable code restored by ANIM2's explicit retirement recipe.
The reader also checks ANIM2's start, stop-head and capture BLs against the
installed ANIM2 bundle, instead of assuming the task name proves activation.

The current [`copie.S`](../../features/manutenzione/sorgenti/copie.S) wrapper
at `0x023DBC9A` preserves r0/r1/r4/lr and checks the native-copy counter at
`0x023DBBC0`. With copies and animations active, it validates the sprite,
neutralizes only its y-offset when necessary and returns. Otherwise it invokes
ANIM2 task `0x023DB72D`; its option accessor is `0x023DB621`.
It does not call v4. These addresses occur as literals in the wrapper pool,
which must not be disassembled as additional instructions.

The 160-byte copy-barrier owner, including its canary, was rebuilt exactly
from assembly, SHA-256
`6926e17b5530f5d4edbd644438d6a9557bbac370ec3ad04994a1d3bc7f8a5ef9`.
Eight existing isolated wrapper tests pass, including OFF/ON transitions,
lifetime-count branches and missing/inactive sprite cases. This is an ABI and
control-path check, not new gameplay or timing acceptance. The current ANIM2
1532-byte code also matches its bundle; its wider animation evidence retains
its [original scope](animation-cadence-1.3.2.md).

## Counterexamples to “the whole block is dead”

The initialized native scan covers 137 components and 4749260 bytes per image:
all ARM9/ARM7 sections and decoded overlays. It searches halfword-aligned
Thumb-1 BL, word-aligned conditional A32 B/BL, and aligned little-endian u32
values into the 1024-byte owner. It preserves the low bit of data pointers;
`0x023D8E41` is a byte address, not necessarily a Thumb function.

EN/IT have the same four external candidates:

| Source | Candidate | Interpretation after checking context |
| --- | --- | --- |
| ARM9 `0x02051EBC` | A32 branch encoding to `0x023D8EE4` | False ISA match: two Thumb instructions in the native Thumb context |
| ARM9 `0x023D9174` | u32 `0x023D8E41` | State guard reference, outside code |
| Overlay 54 `0x021EBCB8` | u32 `0x023D8E41` | State guard reference |
| Overlay 54 `0x021EC2B8` | u32 `0x023D8E41` | State guard reference |

No external candidate toward the 752-byte code interval was found by those
three scan families. This is not exhaustive reachability analysis. BSS/runtime
state, archives, unaligned pointers, computed/indirect calls, short Thumb branches
and A32 BLX immediate are outside coverage. A lexical candidate is retained for
review even when it is data or the wrong ISA; the tool never upgrades it to a
proven caller automatically.

The dependency is explicit in current
[`settings-ui/owners.c`](../../features/settings-ui/owners.c): its guard-address
selection returns `0x023D8E41` for animations. That guard is captured and checked
alongside the option and load status. The older Options common UI also documents
it. The existing Settings last-read guard test passes, including mutation of
that byte and refusal without stores. This verifies a compiled-source dependency;
this case does not newly observe execution of each overlay-54 reference in the
game. The state byte cannot be dismissed merely because v4's two motion roots
were retired.

## Reproduce with your own image

Use [project dependencies](../../requirements.txt) and an ARM-capable Clang.
The measured environment was Python 3.14.7, ndspy 4.2.0, Capstone 5.0.9 and
Unicorn 2.1.4. Preserve the original bundles and choose a new private directory:

```sh
python3 source/features/anim/tools/compila_anim4.py \
  --uscita "$PRIVATE_OUT/anim-v4-rebuilt"
python3 source/features/manutenzione/compila.py \
  --uscita "$PRIVATE_OUT/copy-wrapper-rebuilt"
cmp "$PRIVATE_OUT/copy-wrapper-rebuilt/copie.bin" \
  source/sgp12/build/manutenzione/copie.bin
python3 source/features/anim/tools/attribuisci.py \
  --rom "$ROM_EN" --language EN --build "$PRIVATE_OUT/anim-v4-rebuilt" \
  --json "$PRIVATE_OUT/anim-v4-en.json"
python3 source/features/anim/tools/attribuisci.py \
  --rom "$ROM_IT" --language IT --json "$PRIVATE_OUT/anim-v4-it.json"
python3 -m unittest discover -s source/features/anim/test \
  -p test_blob4.py -k AttributionScanTest -v
python3 -m unittest discover -s source/features/manutenzione \
  -p test_wrapper.py -v
```

Every listed command must exit 0. The two scan tests do not require extracted
game modules; the older v4 behavioral suites have additional private-module
requirements and must report their skips separately. `--no-scan` performs only
the exact-owner and current-root readback. Full scan output contains coordinates,
hashes, domains and candidates, not game bytes or input paths.

The new tests reject code, canary, table, parameter, state and slot mutations.
Authored Thumb BL, A32 BL and byte-pointer fixtures must be detected. The false
A32 candidate in the real ROM is an additional warning against treating every
match as executable code. The independent reviewer reran the direct test-file
entry point and both full EN/IT CLI scans after checking the algorithms against
an independent scan.

## Result and remaining uncertainty

Current source→code reconstruction is exact. Complete-owner readback is exact
in EN/IT. The two historical v4 roots are retired, the replacement chain is
installed, and a bounded scan finds no additional external code candidate.
Data references to the old state are retained and explained separately.

No universal inactivity, reclaimable 1024-byte region, new animation improvement,
hardware timing or save-compatibility acceptance is claimed. Any future removal
would need a separate proof for data consumers, indirect paths and ownership,
with the existing save/ABI constraints preserved. This case authorizes no such
removal.
