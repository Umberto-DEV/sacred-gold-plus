# Transform reload: own assembly, exact installed body and guarded fields

The existing HG-B08 assembly reconstructs all340 bytes of the current r4 EN/IT
reload function. Its source installer also preserves the following52-byte native
literal pool. Current execution distinguishes the five copied combat stats from
the common fields that must continue reloading. This adds attribution tools and
optional ELF retention; game code, installed ROMs and saves are unchanged.

See the [owner](../../features/type-consumers/README.md),
[Transform transport case](transform-transport-source-rom-1.3.2.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[battle audit](../bug-audit-1.3.1.md#battle-and-ai-repairs).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Follow assembly/flags/compiler→retained ELF→loader→installed function→callers,
guarded queries and stores. Check the reverse direction from the current body
to its exact recipe. Separate compiled replacement, inherited preimage, preserved
native literals and source-declared padding. A matching final stat value cannot
prove that a guarded query was skipped.

Use independent raw readback and Sol6.1 review for addresses, ABI, field widths,
regional differences and counterexamples. The reviewer read all eight input-role
images, independently exercised the equal-state/wrong-query IT counterexample
and rejected actual entry into padding. Older private HG-B08 original/candidate
campaigns retain their own input identities; they are not rerun as r4 evidence.

## Il materiale più grezzo da cui partire

Use your own exact retail revision0, Plus1.1, V1.3 V4 and r4 images. Complete
identities and preparation are in the
[flags input section](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire),
[`baseline.py`](../../sgp131/baseline.py) and
[r4 contract](../../distribution/game-1.3.2-r4.json). Every CLI run verifies the
size and SHA-256 of all four complete files for its selected language. No ROM,
retail dump, BIOS, extracted asset or save fixture is distributed with this case.

Project source is [`reload_transform.S`](../../features/type-consumers/reload_transform.S),
SHA-256 `d3fc2de070898e246232f55f3a2a2ef15b59b66e9eee74d9298b9879ef124c16`.
[`transform_reload.py`](../../sgp131/transform_reload.py) compiles and authenticates
the340-byte replacement and supplies its guarded edit. The shared
[`fairy_ai.py`](../../sgp131/fairy_ai.py) composer inserts it alongside disjoint
type/ability edits before the one canonical overlay rewrite and UI-seed
reconciliation. [`mechanics_stages.py`](../../sgp131/mechanics_stages.py) checks
the shared container/region invariants. This case replays the decoded reload
installer and independently reads the exact final image; it does not rebuild
the whole ROM or attribute unrelated overlay changes to this component.

At reference commit `cb614ad23449d5852b40321dc409c4143872b35c`,
`battle_util.c::BattleSystem_ReloadMonData` explains the inherited unconditional
stat reads and later Transform/Mimic guards. That original native C build,
compiler, object and link map are not reconstructed. The project's replacement
assembly has its own separately verified compilation chain.

## I metodi e gli strumenti da usare

Recorded dependencies: Python3.14.7, ndspy4.2.0, Capstone5.0.9 and Unicorn2.1.4.
Fresh compilation requires the protected pinned Apple Clang21.0.0
(`clang-2100.4.1.1`) executable SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
The compiler API checks actual executable identity, version and free-space floor;
an arbitrary compiler with a matching version string is insufficient.

The flags are `--target=armv5te-none-eabi -mcpu=arm946e-s -mthumb -ffreestanding
-fno-builtin -x assembler-with-cpp`, followed by `-c` source and `-o` object.
The strict project [ELF loader](../../features/options/tools/carica_text.py)
loads ARM ELF32 `.text` at `0224EA14`, checks the Thumb entry and rejects
unresolved external symbols or unsupported allocated content/relocations.
No general linker is used. This object has zero relocation records: local BLs
are resolved and its external targets are explicit Thumb literal words.
Loaded text equals the payload without further byte changes.

Set private input/report variables and use your dependency environment's Python:

```sh
# BUILD is a new private artifact directory; compile once.
python3 source/features/type-consumers/tools/attribuisci_reload.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --work "$BUILD" --json "$CASE/reload-EN.json"
# Verify/reuse that exact retained build for IT without invoking the compiler.
python3 source/features/type-consumers/tools/attribuisci_reload.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --build "$BUILD" --json "$CASE/reload-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_transform_reload.CurrentCompositeReload -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_transform_reload.TransformReloadCompiler \
  sgp131.test_transform_reload.TransformReloadAttributionCLI -v
```

With no qualified compiler/build, replace `--work`/`--build` with
`--readback-only`; the report explicitly omits build provenance. That branch was
tested with compiler/build functions made unavailable. Missing private ROM unit
inputs explicitly skip. Compiler unit methods require the pinned compiler.
No full ROM build, emulator capture or save is needed.

`compile_native(..., retain_object=True)` optionally retains `reload_transform.o`.
The default remainsFalse and leaves no object. Before/after checks establish
identical default receipt, object and payload identities; the ASM is unchanged.
A conflicting artifact or symlink is refused. `--work` retains object, binary and
receipt; `--build` checks source/builder/loader/compiler identities and reloads
the object. The CLI protects the four ROM inputs and three retained artifacts
against `--json` aliases before compiling or verifying. A reviewer found the
initial artifact-output collision; temporary-copy regression tests reproduced
it, then passed18 direct/symlink/hardlink cases after the guard was added.

### Binary reconstruction and mapping

| Material | Current RAM / extent | Evidence |
| --- | --- | --- |
| Replacement | `0224EA14–0224EB68`,340 B | Complete compiled/readback identity |
| Executable code/veneers | Function+`0x000–0x10E` |270 B; ends before alignment/data |
| Alignment | Function+`0x10E–0x110` |2 B; not admitted as executable |
| New literal pool | Function+`0x110–0x11C` |12 B: `0x2D40`, `0223A881`, `0206E541` |
| Source padding | Function+`0x11C–0x154` |56 zero bytes; no reclamation claim |
| Preserved native pool | `0224EB68–0224EB9C`,52 B | Unchanged following data; closure392 B |

Retained own ELF SHA-256 is
`b13435d64a96c332cec868df076e2fff9ddc2cc4414e55fba2dbeb87bb299c02`.
Current340-byte SHA-256 is
`41ad8522c1920ccf38115b5e971d28ec9ae0126536756d002379e0624eb2f942`;
the old canonical body is
`be3d7eed5638700df69d0d701dd7e5d0ca4564ef516f92abeb1a12d7e57f08a2`.
The preserved52-byte pool is
`cee233e2d20a36a9ea65ba6bee1bea92392467730e62773bd2a1102b07dbd142`.
Source replay of V4 changes325 bytes in the340-byte owner and matches the
complete current392-byte body/pool closure. It allocates no new resident slot.

Retail IT's old function is at `0224E9B4`, SHA-256
`7eb5f715160303534482dc3a3cf74d7f8b6b42ba194821a0e5da7f41468b16b2`.
Its fourteen ARM9 BL fields target the same GetMonData (thirteen) and Mask
(one) entries. Targets and bounded entry/body signatures are verified before
normalizing those fields only in a comparison copy. The signature check does
not establish native GetMonData execution. Runtime bytes remain unchanged.
The native pool matches across all eight inputs.

Current overlay12/file12 is BLZ-compressed:226176 decoded bytes at `022378C0`,
BSS0,161600 stored bytes at EN `08314200–0833B940` or IT
`08800000–08827740`. Reports retain raw y9/FAT, encoded/decoded identities,
footer and ndspy/project decompression agreement. Decoded instructions have
no simple linear physical ROM offset.

### ABI, callers, guards and resources

Entry arguments are r0=BattleSystem, r1=context, r2=battler0–3, r3=party index0–5.
The replacement frame is24 B. It computes BattleMon as
`ctx+0x2D40+0xC0*battler`. LDR/BX veneers at `0224EB1A/EB1C` and
`0224EB1E/EB20` reach PartyMon lookup and GetMonData through Thumb literals.
These two external services are controlled models; data queries require
r0=nominal Pokémon, field ID in r1 and null data pointer in r2. They do not
execute encrypted Pokémon lookup or decryption.

The first Transform guard at `0224EA3A` skips five GetMonData fields165–169
and16-bit stat stores at BattleMon+2/4/6/8/A. Common fields always reload:
level161 and friendship9 as bytes at+`0x34/35`; HP163 and maxHP164 as words
at+`0x4C/50`. The second guard at `0224EAB8` skips moves/PP/PP Ups/experience
for Transform. Otherwise Mimic bits2–5 from BattleMon+`0x8C` protect individual
slots; queries54+i,58+i,62+i update that slot's move/PP/PP Ups. Experience8
still reloads after the loop. Species, types, ability, form, status and every
other context field remain unchanged.

Four known BLs at `02245442`, `02245CDA`, `0224604C`, `02246358` target the
current entry. The reference has the script refresh and three level-up/move
learning reload sites, with selected-party-index conditions. These are static
caller links; their outer script/EXP state machines are not executed here, and
the check is not a global caller census.

The bench reuses the existing ReloadBench query models while loading actual
ARM9 segments and the installed overlay. It adds actual PC/SP/Thumb return,
eight distinct saved-register cookies, allowed code/veneer ranges, field-width
write guards, context/other-battler and nominal PartyMon immutability,
stack/caller canaries and code/data preservation. Pools, alignment and padding
reject real entry attempts. The native old ordinary comparison executes the
real MaskOfFlagNo; the replacement uses its own inline bit selection. Maximum
observed stack is24 B current and56 B native old including Mask.

### Results, counterexamples and limits

Per language,23 current entries comprise all16 ordinary Mimic masks, six
transformed masks and one equal-stat control. Sixteen corresponding ordinary
native-preimage executions match state and query order. Battler and party
indices vary by mask modulo4/modulo6; this is not their full cross-product.
The ordinary runs use fixed distinct field values. Transformed runs preserve
the five stats, moves, PP, PP Ups and experience while updating all four common
fields, querying only `[161,9,163,164]`.

Three named RAM counterexamples per language restore the native old body,
disable the first guard or disable the second guard. Each is normally refused
by identity checks. The old body loses the five copied stats. The first-guard
counter uses equal stat inputs, producing exactly the same final state but five
extra stat queries; the independent query oracle rejects it. The second-guard
counter retains the copied stats but reloads moves/PP/PP Ups/experience and also
fails. Thus ABI and final stat equality alone cannot establish both guards.

Three compiler methods, four current-image methods, the18-case CLI method and
21 structural/domain negatives pass. Build retention tests preserve conflicting
artifacts and reject nonboolean options. The review's CLI finding is closed;
canonical artifacts were never overwritten. These are bench/tool improvements,
rather than a new game correction.

Provenance and binary reconstruction are established for this project's ASM
replacement and exact source installer interval. Finite native ordinary
equivalence, guarded state and query behavior are demonstrated. Original native
C compilation, natural refresh/level-up/move-learning, complete battle histories,
native PartyMon/GetMonData operation, SAVE/cold restart, hardware and timing
remain unqualified. Padding identity establishes bytes, not reusable memory.
