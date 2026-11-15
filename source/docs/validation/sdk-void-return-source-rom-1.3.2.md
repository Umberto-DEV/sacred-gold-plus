# R0 after modeled void services in rematch construction

The six-Pokémon continuation does not consume the modeled R0 return from four
void services before a native instruction replaces it. This case follows the
actual caller path across returns, independently rereads instructions and tests
zero/`FFFFFFFF` substitution. It covers Pokémon construction and teardown;
the overlay-loader/native-reader prefix remains outside this observation.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate a modeled return value from a caller's actual dependence on it.
The [complete constructor](rematch-complete-source-rom-1.3.2.md) already tests
R1/R2/R3/R12/NZCV poisoning, but retains each service's R0 result. Its raw
receipts identify15 return PCs. Ten have a direct R0 overwrite; five return
through `POP PC`, whose actual continuation cannot be reconstructed from a
set of instruction PCs alone. This is the finite reason for the new observer.

Require a known live-R0 calibration: a monitor that always says “no reads” is
insufficient. Check instruction modes, read/modify/write operands, conditional
execution and SDK argument reads. Observe the instruction after the first
write, rather than assuming the predicted overwrite executed. Preserve complete
constructor semantics and the earlier receipt under the nonmutating observer.

## Il materiale più grezzo da cui partire

Use the exact current inputs and retained objects documented by the
[inert](rematch-source-rom-1.3.2.md),
[first-record](rematch-consumer-source-rom-1.3.2.md),
[first-Pokémon](rematch-firstmon-source-rom-1.3.2.md) and
[complete-constructor](rematch-complete-source-rom-1.3.2.md) cases.
They provide source/compiler/recipe, composition, sizes, language/revision,
header/FAT/FNT/y9, compression/autoload, source drift and independent readback.
This case invokes no compiler and changes no game code, installed byte or save.

| Exact input | SHA-256 |
| --- | --- |
| r4 EN,152786844B |`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`|
| r4 IT,159029760B |`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`|
| Retained strategy object |`e2429f61c7ee16071d303f7ca55cbb1553508720c6fe97b77aead9ce56e499e1`|

The reference prototypes are pinned to `cb614ad23449d5852b40321dc409c4143872b35c`:
[heap.h](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/include/heap.h),
[filesystem.h](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/include/filesystem.h) and
[filesystem.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/filesystem.c).
These are source correspondence; the actual dependence is checked at the
installed native callers. Native SDK implementations remain modeled.

| Modeled service | RAM entry | Return category used here |
| --- | --- | --- |
| Heap_Free |`0201AB0C`|void|
| ReadWholeNarcMemberByIdPair |`02007508`|void|
| NARC_ReadFromMember |`0200782C`|void|
| NARC_Delete |`0200770C`|void|

Heap allocations, GetSpeciesName and NARC_New retain their defined R0 pointer
results. Their return values are never poisoned. The heap/archive/name/capsule
bounds and lifetimes remain those of the complete case, including raw member
hashes, native24-byte capsule setters, original frees and seed restoration.

### What the observer follows

At a selected service's real return PC, it marks only R0 and optionally replaces
it with0 or`FFFFFFFF`. All other register poisoning is explicitly OFF. It checks
that every other register, SP and CPSR remain unchanged by this intervention.
The native program continues in the same CPU/RAM; no code instruction is patched.

For each actual instruction, Capstone read/write sets are examined before a
write can end the interval. A read/modify/write or `MOV R0,R0` is a read first.
A modeled SDK entry counts as a read of its R0 argument. A BL does not implicitly
end the interval. Actual PC continuation follows `POP PC` into the caller.
Unsupported implicit interfaces or excessive intervals are refused. After the
first overwrite, the next actual instruction PC and R0 are recorded to confirm
execution. Intervals are bounded to64 instructions; observed intervals need1..4.

The qualified windows are unconditional Thumb. ARM predicates are checked by
unit tests against240 isolated ARMv5 instruction executions, but this does not
claim tainted ARM runtime coverage. The observer refuses simultaneous SDK
volatile-register poisoning, which could change flags before instruction execution.

The [window manifest](../../features/rematch-variants/test/sdk-return-windows.json)
contains19 paths over15 service-return PCs and29 distinct normal instructions.
It stores addresses, modes, widths and hashes, without extracted ROM bytes.
The [independent reader](../../features/rematch-variants/tools/rileggi_sdk_void.py)
uses raw ARM9 sections, fresh disassembly and the complete case's code admission;
it does not instantiate Unicorn or call the runtime decoder.

Ten dynamic return edges are bound to actual caller BLs. Examples:

| Return in window | Actual next caller PC | Prior caller BL targets |
| --- | --- | --- |
|String_Delete `020263A0`|`0206F4C6`|`02026380`|
|Internal box setter `0206F4C8`|`0206EDC4`|`0206EDE8`|
|FreeMonPersonal `0206FBC0`|four observed callers|`0206FBB0`|
|Growth loader `0206FD2C`|two observed callers|`0206FD14`|
|Move-data reader `02071FDA`|`0207131E`|`02071FC8`|
|Personal-data reader `020725C6`|`0206E368`|`020725B4`|

The reader verifies the BL immediately before each caller return and its exact
function target. Other steps must progress sequentially. Physical locations and
code hashes are derived from each developer's exact ROM in the readback report;
these are loaded ARM9 windows, not an offset rule for compressed overlays.

### Calibration and comparisons

A diagnostic interval marks the already-live workspace pointer at CreateMon
entry`0206DE38` without changing it. The actual first instruction,
`PUSH {R0,R1,R2,R3}`, must be reported as a read. The complete constructor's
receipt stays identical. This diagnostic is rejected if relabeled a normal
no-read result.

With the observer nonmutating, all eight ordinary EN/IT constructor receipts
must equal the preceding complete case, including intermediate evidence.
Zero/ones controls must preserve the six encrypted records, actual return,
seed, counters, lifetimes and every other guest observation. Only the logged
R0 results of these four void services may differ. A narrow comparison
projection replaces just those result-log fields and recomputes the derived
first-receipt hash; no game data, pointer argument, defined result or execution
field is masked. Tests verify that changes to these other fields remain visible.

## I metodi e gli strumenti da usare

Use the [pinned dependencies](../../requirements.txt), exact private ROMs and
objects prepared by the preceding cases. From repository root:

```sh
python source/features/rematch-variants/tools/attribuisci_sdk_void.py \
  --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --trainer 713 --seed 0x12345678 --mode observe \
  --json /private-results/sdk-EN-observe.json.gz

python source/features/rematch-variants/tools/rileggi_sdk_void.py \
  --rom /private-inputs/r4-EN.nds --language EN \
  --report /private-results/sdk-EN-observe.json.gz \
  --json /private-results/sdk-EN-readback.json
```

Repeat observation for both trainers712/713 and selection seeds`12345678`/
`12345679` in each language. Repeat the representative713/seed`12345678` case
with modes`zero`, `ones` and`diagnostic`, always using a new output. Read back
each capture against its matching private ROM. The reader handles deterministic
gzip or plain compact JSON, bounds compressed/expanded inputs and preserves
input aliases. Keep capture reports private: they contain raw guest memory.
Exit0 qualifies the selected finite path; exit2 is a validation refusal.

```sh
PYTHONPATH=source SGP_R4_ROM_DIR=/private-inputs \
  SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
  SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
  SGP_COMPLETE_REPORT_DIR=/private-results \
  python source/features/rematch-variants/test/test_sdk_return_attribution.py
```

The preceding report names default to`complete-EN.json.gz`/`complete-IT.json.gz`,
configurable with one `%s` in `SGP_COMPLETE_REPORT_NOME`. ROM names default to
`r4-EN.nds`/`r4-IT.nds`, configurable with `SGP_R4_ROM_NOME`. Tests authenticate
the preceding exact input identity and revalidate its semantics before comparison.
Missing private inputs cause explicit skips, not acceptance. The
[tests](../../features/rematch-variants/test/test_sdk_return_attribution.py)
include ROM-free output/projection/predication/admission checks and private
full-path comparisons, poison controls, calibration and forged-reader counterproofs.

Store argv, exit code, source/fixture hashes and OS resource receipts locally.
Bound runs to180s/1GiB RSS/2MiB log/16MiB case output, retaining10GiB disk
headroom. The inherited guest budget is3million instructions/512-byte stack;
these are verification bounds, not hardware timing measurements.

### Result and remaining links

The eight nonmutating observations cover2690 void returns. In each, the native
caller replaces R0 within1..4 instructions without reading it first. The complete
prior receipts stay identical. Zero/ones controls preserve the exact constructor
result; the live-pointer diagnostic detects the genuine read with no game-state
change. This qualifies independence from the modeled R0 values in these finite
body/teardown paths and the observer's sensitivity.

The nine tests passed with no skips, including the eight prior-receipt comparisons,
four zero/ones paths and one live-read diagnostic. Raw readback passed for both
languages. The reader records the post-overwrite R0 value but does not independently
recalculate instruction operands; its proof is of the first write and absence of
a preceding read.

The result does not establish native SDK allocator/filesystem behavior, failure
paths, all callers of these APIs, loader/native-reader prefix R0 handling,
arbitrary trainer formats/state or natural phone/Dojo activation. Installed
activation remains0. Original native MW and historical Plus toolchain limitations
remain unchanged. No ROM/save, gameplay repair, optimization or hardware speedup
is implemented or implied.
