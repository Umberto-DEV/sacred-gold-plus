# Summary hint recipe and exact installed path

The current EN/IT r4 images contain the expected 96-byte Summary hint patch.
Its two flag stores and two-branch return path execute from the real inherited
Plus function entry with synthetic resources. The native Summary root, Plus
wrapper and language text remain unchanged from the exact 1.1 bases. This is
a verification result; no game bytes, input behavior or save layout change.

See the [owner](../../features/guide/README.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).
This Summary guide is separate from the field Guide and the published inactive
Summary-controls configuration.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish the Plus combined-guide payload, the later 96-byte recipe, native
Summary code and language text. Follow source recipe→insertion→readback and
the reverse root→wrapper→function→patch→return chain. An instruction match
is not proof of a natural Summary visit or panel rendering. Check eligibility,
resource/settling/visibility gates, ABI and writes with counterexamples.
Independent Sol 6.1 review used the raw ROMs and source separately, including
an independently constructed full-entry fixture and six gate controls.

## Il materiale più grezzo da cui partire

Use your own exact EN/IT r4 images from the
[game contract](../../distribution/game-1.3.2-r4.json) and the corresponding
Plus 1.1 bases. Their full hashes, sizes and preparation requirements are
listed in the [camera input table](camera-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
The final-image reader authenticates complete inputs, not filenames. No save,
BIOS, extracted asset or gameplay capture is required or redistributed.

Raw material is the NDS ARM9 header, autoload section mapping, ITCM code,
Thumb branches/literal pools, 96-byte replacement recipe, 1098-byte language
signature, current state layout and inherited root/wrapper. The
[combined source](../../native-guide/combined_guide.c) and
[historical build](../../native-guide/build_combined_guide.py) explain names
and the original insertion scheme. They do not establish current C-to-object
identity: the original compiler is unauthenticated. Earlier build notes record
a compiler-sensitive rebuild regression; this case does not repeat that build
or replace its 4752-byte payload.

## I metodi e gli strumenti da usare

Reuse the owner raw/autoload reader and compare it with ndspy sections. The
raw reader shares project layout validation; ndspy is the separate parser.
Reconstruct the four Thumb instructions and NOP fill from the public recipe,
compare exact bytes, decode both return branches, authenticate the root/wrapper
and compare the bounded function window base→r4. Execute installed bytes in
Unicorn with synthetic Summary data/MMIO and no helper stubs on these paths.

From the repository root, with Python dependencies in
[requirements.txt](../../requirements.txt):

```sh
.venv/bin/python3 source/features/guide/tools/attribuisci.py \
  --language EN --base /path/to/plus-1.1-en.nds \
  --rom /path/to/exact-r4-en.nds --json /tmp/sgp-summary-hint-en.json
.venv/bin/python3 -m unittest discover \
  -s source/features/guide/test -p test_applica_guida.py -v
```

Repeat the first command for IT with its own input pair. Use the virtualenv
setup from the [test bench](../test-bench.md). This case used Python3.14.7,
ndspy4.2.0 and Unicorn2.1.4; it needs no compiler or linker. Exit0 means exact
input admission, raw/ndspy agreement, patch/text/root/wrapper and function-delta
checks, and all eleven isolated checks passed. JSON records hashes, RAM and
physical offsets, observed state/writes/stack depth and coverage. No personal
paths, retail bytes or ROM outputs are emitted.

## Recipe, composition and addresses

The [production block](../../sgp12/blocchi/guida.py) and
[owner installer](../../features/guide/tools/applica_guida.py) construct:

```text
movs r0, #1
str  r0, [r7, #0x2C]     ; Persistent.badge = 1
str  r0, [r7, #0x30]     ; Persistent.pending = 1
b    0x01FF8B18
44 × mov r8, r8          ; unexecuted fill on this path
```

This is a direct machine-code recipe, with no compilation, relocation or new
trampoline. The installer admits the original 96-byte fingerprint and replaces
only that interval. Final-image attribution checks the component; it does not
apply the old Guide-only reader's whole-ROM delta rule to r4's many features.

| Component | RAM address / size | Physical base/r4 EN/IT |
| --- | --- | --- |
| Native Summary root | `02088424`, 8B | `0008C424` |
| Plus wrapper | `01FF91F4`, 52B | `00116A54` |
| Plus `guide_main` window | `01FF8880`, 672B | `001160E0` |
| Replacement | `01FF8A1A`, 96B | `0011627A` |
| Language signature | `01FF9B10`, 1098B | `00117370` |

The code is ARM9 autoload ITCM, not an overlay. These base/r4 bytes are directly
mapped from uncompressed file sections; no compressed offset arithmetic is
used. Root `ldr r3; bx r3` loads `01FF91F5`; wrapper BL at `01FF9200` calls
`01FF8880`. The wrapper first calls native `02007291`, then sends its returned
Summary pointer and saved state pointer into `guide_main`. A return0 continues
native Summary at `0208842D`; return1 takes the wrapper's handled path. This
root/wrapper connection is static in this case; execution starts at guide_main.

Within the function, r7 points at the 64-byte Plus state `01FF9FC0`, not a save
record. The patch sets badge/pending flags without acquiring a badge context,
font, Window or bitmap. It branches `01FF8A20→01FF8B18→01FF894A`. The shared
epilogue returns r5, adds36 to SP and restores r4–r7/PC; the entry prologue
had saved20 bytes and reserved36. The valid idle path returns0. Synthetic tests
check r4–r11, SP, Thumb and final PC; r0–r3 and flags are caller-saved.

Upstream checks require phase0, eligible Summary state/page, no conflicting
input, matching resource descriptors, a settled BG, display visibility and
free cells in both tilemaps. The exact fixture sets callback/host, BG heap19,
map2048/descriptor, font pointer/descriptor and MMIO values as required by
`summary_resources`; both tilemaps are zero. These are synthetic host memory
values, not captured hardware state. The reader never stubs a successful gate.

## Results, counterexamples and limits

**Documented provenance:** the original Plus C/build explains Persistent
fields and wrapper logic; the later own-project recipe explains the exact
replacement. No original compiler match is claimed for the surrounding payload.

**Binary reconstruction/readback:** original96B SHA
`9ffbcb8c920f67d2343e16cde7426b57f5a639ebddee956cfe2b240dc6bf9aa9`;
current96B SHA `e9c85f702347a58698951876d43662f5f6690f5dbff0290465a435892e46bf08`.
There are95 changed bytes within that96-byte range in the672-byte function
window, with no change elsewhere in that window. Wrapper52B is identical.
Language text1098B remains base-identical: EN SHA
`5b2061b68b6b471c6043def4e222c893c4b977de4a5389518f8f9f2f77b18188`,
IT SHA `c7b977a19f50135526e35fc89ea968f855c652395a923b77d708c2c1187f21cd`.
A text fingerprint preserves that interval; it does not certify every string,
other language or text in the field Guide.

**Demonstrated isolated behavior:** eleven checks per language use fourteen
actual guide_main invocations. Idle reaches the patch once, sets badge/pending1,
keeps context/heap0 and returns0. Seven separate controls (keys, BG heap,
settling, display, RAM tile, GPU tile and wrong Summary state) avoid the patch.
After an idle preparation, raw START and an inside touch each trigger the first
opening transition, return1 and set phase1; a key blocker prevents it. This
covers the opening gate, not the next modal allocation/render/update/cleanup.
No helper is replaced; execution must stay within installed Plus code.

Observed writes stay in synthetic stack, Plus state and, on follow-up input,
the display register. The deepest observed stack write is72B below entry SP
on these paths; the checker rejects writes beyond its128B stack allowance.
That allowance is not a measured universal maximum. Badges flags1 do not imply
an allocated/drawn badge. No save data is read or written.

**Counterexamples:** the unit suite rejects six individual96-byte mutations
and altered continuation/epilogue. Existing semantic instruction tests remain
in place. Fourteen test methods pass without skips. Initial integration found
two mistaken synthetic opcode fingerprints for equivalent Thumb move forms;
they were corrected against actual readback, not by changing the game. The
original failed command receipts remain local.

**Activation not observed:** no new natural Summary input, full three-panel
rendering, native callback transport, UI performance, save migration or physical
run is implied. Branch/literal checks establish the chosen path, not universal
unreachability of every padding byte through arbitrary indirect calls. This
case does not attribute the whole native HGSS Summary source or claim that all
historical combined-guide C bytes reconstruct with today's compiler.

Final measured peak RSS was about702/724MiB EN/IT, elapsed about0.20/0.21s,
using OS `time -l`. The periodic sampler is not a reliable peak measurement for
these short commands. There are no retained whole-ROM derivatives. A source
rebuild of the combined payload would be a separate high-risk task requiring
its toolchain, full root/ABI/modal regression tests and natural input coverage;
no such game change is proposed here.
