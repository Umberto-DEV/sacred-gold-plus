# Conversion2: compiled row reader, native RNG and exact current command

The current64-byte helper reconstructs from project assembly and the protected
compiler, including its one external BL fix. Exact r4 EN/IT readback and339
isolated entry invocations per language verify every direct row, random transport,
full command paths and two semantic counterexamples. RNG and unsigned division
execute as native code. Five external command services remain explicit models.

See the [owner](../../features/type-consumers/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[preceding caller case](postko-source-rom-1.3.2.md). No assembly, game policy,
ROM, type IDs, save layout or settings change is made by this work.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Trace source→object→relocation/post-link fix→installed overlay bytes, then
helper callers→command→row selection and state writes. Check both the direct
and random ABI, input domain, control records, final return and neutral direct
path. A matching row alone does not establish correct RNG state.

Read literal words as data: a Thumb disassembly of an embedded word is not
its value. The initial seed-offset hypothesis`BS+0x48` was rejected before the
main runner: the actual32-bit literal is`0x2448`. Independent Sol6.1 review read
raw regional inputs, corrected that fixture premise, validated native math and
selected executions, and independently rejected a same-row/wrong-state mutant.

## Il materiale più grezzo da cui partire

Use your own retail HeartGold revision0, Plus1.1, V1.3 V4 and exact r4 EN/IT.
Full identities/preparation are linked from the
[flags input section](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire),
[`baseline.py`](../../sgp131/baseline.py) and the
[r4 contract](../../distribution/game-1.3.2-r4.json). Every run authenticates all
four whole-file hashes/sizes. The IT composed image's header still says`IPKE`;
header code alone is insufficient to establish language. No save, BIOS, ROM,
extracted asset or retail dump is distributed or required in the repository.

Sources are [native.S](../../features/type-consumers/native.S),
[compiler/edits](../../sgp131/type_consumers.py),
[chart recipe](../../sgp131/type_chart.py) and the
[shared AI composition](../../sgp131/mechanics_stages.py). The native reference
at pret/pokeheartgold commit`cb614ad23449d5852b40321dc409c4143872b35c` supplies
`src/battle/battle_command.c::BtlCmd_TryConversion2`,
`battle_system.c::BattleSystem_Random` and macro`TryConversion2` in
`asm/macros/btlcmd.inc`. Native source correspondence is distinguished from
project assembly reconstruction; original native MW binaries are not rebuilt.

## I metodi e gli strumenti da usare

Recorded dependencies are Python3.14.7, ndspy4.2.0, Capstone5.0.9 and Unicorn2.1.4.
Build mode uses protected Apple CLT Clang21.0.0 (`clang-2100.4.1.1`), executable
SHA-256`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
Flags are ARMv5TE/ARM946E-S Thumb, freestanding, no builtins and assembler-with-cpp;
the exact list is in the receipt. Use a Python environment with those dependencies
and set variables to private inputs and a fresh report/build directory:

```sh
python3 source/features/type-consumers/tools/attribuisci.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --work "$CASE/build" --json "$CASE/conversion-EN.json"
python3 source/features/type-consumers/tools/attribuisci.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --build "$CASE/build" --json "$CASE/conversion-IT.json"
PYTHONPATH=source python3 -m unittest sgp131.test_type_consumers.TypeConsumerCompiler -v
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_fairy_ai_rom.CurrentCompositeConversion -v
```

`--work` compiles and retains`type-consumers.o`, `native.bin`,
`compile-retained.json`; a differing artifact is preserved and rejected.
`--build` verifies and reuses those canonical artifacts without a compiler call
or duplicate tree. `--readback-only` instead records no compilation/reused-build
proof while still performing byte/CPU checks; this mode is separately exercised
on EN. These modes are mutually exclusive. Report output cannot replace inputs
or artifacts. Missing private unit-test inputs explicitly skip, not pass.

### Compilation and exact installed bytes

The strict [ELF reader](../../features/options/tools/carica_text.py) resolves
internal relocations. Symbols establish Thumb entry`0225260D` and external-call
site`0225261A` (decimal offset14). The source emits a four-byte BL placeholder;
the recipe replaces exactly those bytes with a BL to native RNG`0223BD98`.
Independent Capstone decoding verifies the target, and the remainder of the
object text matches installed bytes exactly. No system linker/map is needed.

The64-byte payload SHA-256 is
`1ab0ab8d6b3b2bc003a44e57330beab3a4a393020b52e71f4c48bb7489645875`;
recorded own-project ELF SHA-256 is
`20a39a2a1b1437a886b3b8f1c21515e7633c912d05711b7eab9f1a1b5d4f4fa3`.
Assembly source SHA-256 is
`abc8e80875ae0af6cca2cd6fe904394271f2d206985da55883c76d5ca9e91016`.
Builder/loader/compiler hashes record tool drift separately. Optional object
retention changes tooling only; the production default retains no object and
keeps its prior receipt and payload contract.

| Component | RAM / extent | Role |
| --- | --- | --- |
| Installed helper | `0225260C`,64 B |52 B code plus12 B literal pool |
| Helper literals | owner+52/+56/+60 |325 rows, ARM`020F2BA4`, chart`021FBE60` |
| Full command | `02240C98–02240E58`,448 B | Includes24 B of context-offset literals and alignment |
| RNG | `0223BD98–0223BDC4`,44 B | Thumb code, alignment and three32-bit literals |
| Unsigned divmod | ARM`020F2BA4–020F2D88`,484 B | Real quotient/remainder of16-bit RNG output by325 |
| Modern chart | overlay18,`021FBE60` |325 records before three-byte FF terminator |

The helper replaces its entire old span in overlay12, file12, decoded base
`022378C0`, size226176, BSS0. Current encoded FAT spans are EN`08314200–0833B940`,
IT`08800000–08827740`,161600 B. Raw y9/FAT, stored/decompressed hashes and BLZ footer
are recorded again and independently decoded with project code and ndspy, as
explained in the flags case. There is no simple physical file offset for an
instruction in the compressed stream. Overlay18 and ARM9/autoload mappings
are read independently, with their identities in the report.

Current chart replay from V4 uses the two-byte Ghost correction recipe; only
the chart region is attributed, not the entire shared overlay18. The325 records
are322 ordinary matrix records plus`FE,FE,0`, Normal→Ghost0 and Fighting→Ghost0.
The FE marker is selectable by the low-level helper, but a command with valid
last attack type0–17 cannot accept it. The helper never reads the FF terminator.
Current chart SHA-256 over975 record bytes plus first FF byte is
`349a69b6b0029141811239f4b7a40ff53ab14e16607936dc75602c0b20179221`;
the chart parser separately validates the full terminator.

### Historical inputs and reverse links

Command448 and RNG44 are byte-identical across all eight inputs. Their hashes
are respectively
`54720adb00d5dd7627ab0bc09d68bdf803956eb182233c740341476332de0748` and
`29e88b6c3903a8d41c8471aebff5a8ae313f9a36682b73e57d04ddf085267cd8`.
The484-byte ARM math SHA-256 is
`3b0403581ea03e86bdfc0cde00ea2ca13f522291aec399b93ecdf2fef57944eb`.

Retail IT's old helper is`022525AC`, raw64-byte SHA-256
`785e4f2d33313f9230b0fb1f65048daa2056f7880a7a8ed13904baa60182c7a4`.
Its old RNG call at offset`0x0C` reaches regional`0223BD38`; the encoding agrees
because caller and target moved together. Its BLX at offset`0x12` still targets
ARM`020F2BA4`. Three PC-relative loads at`0x1C/0x22/0x28` alias pool words
`0x34/0x38/0x3C`, pointing to regional sparse-chart columns0/1/2. Only after
checking the actual targets, math identity and pointer aliases does a comparison
copy normalize the BLX field and three words. It then equals the canonical
64-byte preimage in the source recipe. Runtime bytes are never translated.
This bounded correspondence does not imply a global regional offset rule.

Three current helper BLs are verified at`02240D32`, `02240DB0`, `02240E28`.
The battle-script dispatch table at`0226C6C8` has opcode93 slot`0226C83C`
pointing to Thumb`02240C99`, matching the native macro/reference. This table link
is static. The runner enters the command explicitly; it does not execute the
interpreter or establish a naturally selected Conversion2 move.

### ABI, RNG and write boundaries

The helper takes r0 BattleSystem pointer, r1 unsigned index, r2 attack-byte
pointer, r3 defender-byte pointer and an effect-byte pointer on the incoming
stack. It writes exactly those three bytes. Indices0–324 return1 without RNG;
indices≥325 call RNG once, reduce the returned16-bit value modulo325 and return0.
`0xFFFFFFFF` therefore takes the random path, not an out-of-bounds direct read.
The16-byte helper frame reads its fifth argument at`[sp+0x10]`. The native RNG
adds8 bytes; ARM divmod uses no extra stack in this domain. Callee registers,
SP and Thumb return are verified with eight distinct cookies and output canaries.

RNG literal`0223BDB8` is the full32-bit field offset`0x2448`, followed by multiplier
`0x41C64E6D` and addend`0x6073`. The executed code updates that word modulo2^32
and returns its high16 bits. Every call's input state equals the previous output;
LCG, returned value, native return ABI and final state are checked independently.
Direct paths must retain the initial seed. Actual unsigned division verifies
quotient and remainder, with ARM entry/Thumb return and unchanged live callee
registers; no host arithmetic replaces its instructions.

The full command's24-byte push plus16 local bytes form a40-byte frame. With
helper/RNG, observed depth reaches64 B. Guest writes are confined to bounded
stack and seed, three helper outputs, or command type bytes at ctx+`2D64/2D65`
and message word ctx+`130`. Code/chart, caller stack, other BS/CTX bytes and
canaries remain unchanged. Executed/read ranges are hashed. Literal pools are
excluded from executable regions; terminator reads are explicitly rejected.

The runner reuses the legacy bench's five non-RNG controls: script pointer
increment/read, ability, unrelated precondition and current-type queries.
Their exact entry addresses/arguments are in the JSON. They return the declared
synthetic controls; script cursor movement and actual ability/precondition
implementation are not qualified. RNG itself is no longer a model in this case.

### Results, counterproofs and coverage

Per language,325 direct rows are exhaustive; seven random boundary/seed cases
exercise325,65535 and`0xFFFFFFFF`. Five command scenes include the three Fairy
resistances Poison/Steel/Fire, a Fire control, and Dragon with both available
resistances Steel/Fairy already current. Immediate-success seeds are derived
by inverting the LCG for a known row, rather than bypassing the RNG.

The failure scene actually runs1000 random attempts,325 direct records and
one final random row discarded by the caller:1326 helper calls,1001 RNG calls.
It returns without changing type/message and has the independently predicted
final seed. The old112-row domain would have the same RNG count but fewer
helper calls; RNG count alone cannot prove the row domain.

Two named RAM-only counterexamples exercise the strengthened oracles. A literal
325→112 makes index112 return a random row/0 instead of its direct row/1. A NOP
replacing the RNG seed store, seed0, returns the same row0/0 as the positive,
but leaves seed0 rather than24691. The state oracle rejects it despite matching
output and return/ABI. Normal admission also rejects either altered code image;
only explicit counterexample fixture flags bypass the relevant identity gate.
No input file or canonical artifact is mutated.

Three compiler methods pass, including opt-in retention/collision/default tests.
Three current-image methods pass in EN/IT with no skips. Nine structural negatives
cover code/chart/math, wrong seed literal, forged build metadata and a forbidden
terminator read. Independent review repeats bounded native cases and both
regional and same-output RNG reasoning; it does not claim the full matrix as
its own run. Historical campaigns are not repeated.

Final reused-build EN/IT readers exit0 in1.229/1.667s with OS peak RSS
203,341,824/209,534,976 B. Fresh CLI build/execution exited0 in1.358s, peaking328,007,680 B, below1GiB.
Logs are bounded2MiB and case output16MiB; no full ROM composition or capture.
These are host proof costs, not game responsiveness or device measurements.

- **Documented provenance:** exact inputs, source/recipe, protected compiler,
  retained own ELF and shared writer.
- **Reconstructed binary correspondence:** complete64-byte helper, external BL,
  literals, native command/RNG/math continuity and bounded regional references.
- **Demonstrated semantics:** full direct domain, declared random/command scenes,
  actual RNG state/divmod and semantic counterexamples with ABI/write checks.
- **Observed activation:** isolated helper/command entries under five controls.
- **Unattributed or untested links:** original native compiler, actual script
  dispatcher/cursor, real context allocation/abilities/preconditions, natural
  battles, cross-session RNG state, save compatibility, timing and hardware.

No game correction or optimization is proposed from these results. The reusable
extension is exact mixed-ISA row transport with actual state progression, where
identical outputs would conceal a missing write. Grounding literals and their
native damage consumer remain a separate same-owner path to attribute next.
