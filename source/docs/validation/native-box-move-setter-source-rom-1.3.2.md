# Native Box move setter: halfword stores and idempotent writes

The original `SetBoxMonData(Box,54,ValueU16)` completes its encrypted-record
path on owned synthetic data. Three calls pass: move310 already present,
counterfactual move311 and observation OFF. Each executes3780 original Thumb
instructions, including both native checksums and both crypto phases, with no
models or runtime host writes. Move310 leaves the complete Box unchanged but
still performs the field and checksum-header stores.

This follows the [PP byte setter](native-box-pp-setter-source-rom-1.3.2.md)
and [PP-Up getter](native-box-ppup-source-rom-1.3.2.md) toward the complete
move caller. The [owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom)
describe the wider source/build context. No gameplay, ROM, save, ABI, IDs or
defaults change. The complete higher caller does not execute in this case; its later
[separate composition proof](native-box-move-caller-source-rom-1.3.2.md)
retains the actual stack Value and four-call lifecycle.

## Exact inputs, source and compilation boundary

Use your own current r4 ROMs. EN executes; optional IT is readback only.

| Input | Bytes | SHA-256 |
| --- | --- | --- |
| Current EN |152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| Current IT |159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Both identify IPKE/revision0; presentation language is distinct. The clean
productive source is
[ctrl-cheeb-del/pokeheartgold at cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).

| Source file | SHA-256 |
| --- | --- |
| `src/pokemon.c` | `1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3` |
| `include/pokemon.h` | `54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1` |
| `include/constants/pokemon.h` | `64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74` |
| `include/pokemon_types_def.h` | `032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d` |

`pokemon.c:953–970` defines the outer setter. The internal function starts
at972, selects four blocks at986–989 and writes moves at1100–1104.
Attribute54 is `MON_DATA_MOVE1`; `VALUE(u16)` supplies the two-byte move ID
at BlockB+0. CurrentPP and PP-Up occupy different fields at BlockB+8/+12.
The C return type is `void`.

These are inherited native HGSS bytes. Original Metrowerks compiler, Thumb
objects, ELF and link map remain unavailable. No compiler, new installer or
ROM composition runs here. The evidence establishes documented source
provenance, installed byte correspondence and finite semantic equivalence;
it does not establish reconstructed C-to-Thumb equality or a complete Italian
source build. New PRET references help
[compare components despite file drift](native-mon-substructure-source-rom-1.3.2.md#aligning-with-the-newer-pret-sources),
without replacing the productive pin or importing Platinum ABI/layout.

## Byte ownership and static caller

Current ARM9 is plain at physical`0x4000`, RAM`0x02000000`, initialized length
`0x12B8E4`, entry`0x02000800`. Physical offset here is
`0x4000 + RAM - 0x02000000`. There is no overlay/autoload dependency for these
initialized windows. The [reader](../../features/trainer-strategy/tools/rileggi_box_move_setter.py)
authenticates the full ROM and compares physical bytes with independent ndspy
decoding. Execution uses328 code bytes/154 Thumb starts and528 data bytes.
The common wrapper, prefix, dispatch, crypto/checksum/selector/pools and hashes
are in the [preceding byte-setter map](native-box-pp-setter-source-rom-1.3.2.md#installed-windows-and-the-static-caller).
The new move leaf replaces the PP leaf; it does not add that branch to the route.

| Component | RAM interval, end excluded | Physical start | Bytes / starts | SHA-256 |
| --- | --- | --- | --- | --- |
| Move leaf and internal return | `0206F0E4..0206F0F4` | `730E4` |16 /8 | `4f920065b56cd91bd9ecf53c4862b154f56e8dc91164dcbfe79c0caab2c1e8a5` |
| Retained attribute table, data | `0206EE3C..0206EFB4` | `72E3C` |376 /0 | `fd895513256dc971df570f3f9f8bc069c9f41bb58da799241a4eadf5aa6aa2bf` |
| Complete static move caller | `020714F0..02071532` | `754F0` |66 /29 | `241d632c25e2e2130111d57bd97d01fa3e0c3085fcd88383e7ea4fc0ef01c5e4` |

The188-halfword table is data. Row54 at`0206EEA8` contains`0x02A6`;
ADDpc at`0206EE3A` uses PC+4=`0206EE3E` to reach`0206F0E4`.
Failure/assert gap`0206ED9C..0206EDBA`, default branch`0206EE2E`, other
attribute leaves and padding remain excluded. The selector's odd data-table
pointer retains its low bit. No historical lineage is inferred for new windows:
fresh current EN/IT equality and earlier prerequisite lineage have distinct scope.

The source caller `BoxMonSetMoveInSlot` is at`pokemon.c:3132–3140`. Its four
native BL targets are checked statically:

| BL | Target | Purpose |
| --- | --- | --- |
| `020714FE` | `0206ED70` | Set move, attr54+slot |
| `0207150A` | `0206E640` | Read PP-Up, attr62+slot |
| `02071516` | `0207332C` | Compute MaxPP |
| `02071526` | `0206ED70` | Set currentPP, attr58+slot |

The caller window is authenticated but removed from execution parts and pages.
The standalone Value pointer is synthetic. These checks do not establish
actual caller activation or a MaxPP-to-setter bridge.

## Owned records and why endpoint equality is insufficient

The [freezer](../../features/trainer-strategy/tools/congela_box_move_setter.py)
constructs the same owned encrypted Box136 used by the preceding cases:
PID`0x4000`, flags0, checksum`02AB`, physical blocks[A,C,B,D], species355,
move310, currentPP15, PP-Up3 and other plaintext bytes zero. Initial SHA-256:
`f88425686bc184b9f50a004384b16518c09f785cf190112595938e3220c72cf1`.
The separate Value storage is now two bytes with16-byte guards on each side.
No save, extracted player record or personal data supplies these fields.

Only Value differs between profiles: bytes`36 01` versus`37 01`. Entry CPU
and Box are identical. The unchanged high byte means even a wrong byte store
could appear correct at the final move field. The proof therefore requires
the actual two-byte load/store transcript and instruction qualification using
a source/preimage with different high bytes and a nonzero register offset.

| Value | Final key | Seed63 | Seed64 | Final Box136 SHA-256 |
| --- | --- | --- | --- | --- |
|310 | `02AB` | `85732C58` | `8D9D11EB` | `f88425686bc184b9f50a004384b16518c09f785cf190112595938e3220c72cf1` |
|311 | `02AC` | `43B984BD` | `039D7AEC` | `b251f1be25d728af9728f427888a554b3313eadf98a4d2399d5a2fb9fd6a3ef4` |

For310, both STRH move310→310 and STRH checksum`02AB→02AB` still execute.
Dropping either from a forged ledger fails despite an unchanged endpoint.
The owned replay unit also demonstrates the limit of replay alone: an empty
journal can explain unchanged bytes. The source-specific raw comparison is
what requires these idempotent instructions and their recorded stores.

For311, the field changes, the second native checksum becomes`02AC`, STRH
updates the header and LDRH reloads it for encryption. Both native crypto
passes,128 local seed updates and128 checksum reads remain required. Decrypt
uses old key`02AB`; encrypt restarts from the final header key. No host repair,
seed reset or expected-field injection occurs. PP15 and PP-Up3 remain unchanged.

## Writer ABI and stack lifetime

Entry: Thumb`0206ED70`, R0=Box`022F0000`, R1=54, R2=Value`022F0200`,
R3–R12 cookies, SPtop=`023FD000`, LR=`022F0181`, CPSR=`6000003F`.
At STRH`0206F0F0`, native ADDSP80 has **already executed**:

```text
R0=offset0, R1=ValueU16, R2=3, R3=0206ED8D
R4=ValuePointer, R5=BlockB, R6=BlockD, R7=BlockA
SP=SPtop-40, LR=0206EE27, CPSR=4000003F
```

This differs from the PP writer's pre-ADDSP SPtop−120, pointer R0 and flags.
The LSLS of the normalized zero offset sets Z and clears C. STRH uses
`[R5,R0]`, with register offset unscaled, rather than a computed pointer in R0.

Each call executes3780 Thumb instructions/154 unique starts,709 reads and312
stores, peak stack136B and eight mapped pages32768B. The complete final34-word
frame follows the [preceding frame map](native-box-pp-setter-source-rom-1.3.2.md#abi-stack-and-complete-memory-evidence),
with saved attr54 and this profile's final seed64. Thirteen unused words retain
their actual fill. Chronological store preimages, full16 at every PC and every
mapped byte match the source prediction; forward/inverse replay restores the
initial page hashes. Guards cover the full16+2+16 Value extent.

Final R0=`8D9D` or`039D`, R1=0, R2=seed63, R3=`0206EDE5`, R4–R12
restored cookies, SP restored, LR=`0201FF59`, CPSR=`6000003F`.
R0 is a void-function cipher residue, not a move or boolean. Volatile state is
an observed property of this path, not a new C prototype guarantee.
Across profiles final CPU differs only at R0/R2; final mapped memory differs
in132 bytes: one checksum byte,127 cipher bytes, the Value low byte and three
seed-slot bytes. All128 crypto halfword stores (64decrypt+64encrypt) occur.
OFF preserves full input, endpoint and enforcement counters with empty ledgers.

## Reproduce with your own inputs

Dependencies are in [requirements](../../requirements.txt): ndspy4.2.0,
Capstone distribution5.0.9, Unicorn2.1.4; tested Python3.14.7. Pure tests need
only the standard library. CPU17 is Cortex-A15 instruction emulation, not
ARM946 silicon/cache/CP15/IRQ or DS timing qualification. No compiler is needed.

From the repository root set absolute paths `ROM`, optional `IT_ROM` and
clean productive `HGSS_REFERENCE`. Use a fresh private directory outside
`source/`; retain at least10GiB free after a planned1GiB disk peak.

```sh
PY=.venv/bin/python3
TOOLS=source/features/trainer-strategy/tools
OUT="$(mktemp -d)"

"$PY" -B "$TOOLS/rileggi_box_move_setter.py" --rom "$ROM" --it-rom "$IT_ROM" --json "$OUT/resources.json"
"$PY" -B "$TOOLS/congela_box_move_setter.py" --rom "$ROM" --json "$OUT/frozen.json"
"$PY" -B "$TOOLS/qualifica_box_move_setter.py" --json "$OUT/instructions.json"

"$PY" -B "$TOOLS/attribuisci_box_move_setter.py" --mode prepare --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --out-dir "$OUT/prepared"
"$PY" -B "$TOOLS/attribuisci_box_move_setter.py" --mode matrix --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --out-dir "$OUT/matrix"
"$PY" -B "$TOOLS/attribuisci_box_move_setter.py" --mode verify --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --raw-dir "$OUT/matrix" --out-dir "$OUT/verify"
```

Omit the optional IT flag when unavailable. Reader/freezer execute no CPU code.
`prepare` predicts; `matrix` alone runs original code. `verify` recomputes the
prediction and checks the original prepared bindings, raw hashes and complete
matrix report without importing Unicorn. A second guarded replay passes with
CPU/assembler imports and compiler/non-Git subprocesses forbidden. Raw files
are written before verdicts and remain private; no ROM/dump/save is published.

The [new frontend](../../features/trainer-strategy/test/arm_thumb_box_move_oracle.py)
adds aligned STRH register offset only, mask`FE00==5200`. It preserves its
parent's run bytecode, defaults and complete effective namespace, with three
explicit overrides. Four owned kernels test low16 little-endian, changed high
byte, nonzero register offset, aliases and32-bit wrap against hard registers,
flow, preimages, neighbors and all pages, followed by actual CPU execution.
Odd addresses are rejected by the host domain; no unaligned-silicon claim follows.

The [owned receipt](../../features/trainer-strategy/test/box-move-instruction-qualification.json)
contains synthetic registers and source/flow/store/page hashes. Validation
reconstructs exact expected content without invoking the oracle or CPU. Earlier
frontend/fixture domains remain unchanged. Contextual semantics and replay are
in the [bench](../../features/trainer-strategy/test/box_move_setter_bench.py);
the [CLI](../../features/trainer-strategy/tools/attribuisci_box_move_setter.py)
binds all42 runtime source identities before/after each cell.

Run the23 ROM-free tests, also registered in [the public runner](../../run_tests.py):

```sh
"$PY" -B -m unittest discover -s source/features/trainer-strategy/test -p test_arm_thumb_box_move_oracle.py
"$PY" -B -m unittest discover -s source/features/trainer-strategy/test -p 'test_box_move_setter*.py'
```

## Counterproofs, conclusions and limits

Twenty-six pure raw forgeries reject a well-formed byte store with an identical
idempotent endpoint, missing move/header stores, wrong load/store widths,
preimages, PP target, old key/seed, omitted second checksum/Value/PID reads,
legacy pre-ADDSP SP/R0/flags, missing normalization, counterfeit return/LR,
camouflaged input, count/type errors and injected host writes. Old-key cases
use311 because310 deliberately retains the same key. They pass before CPU
on source-generated records and again on the actual completed native evidence.

A professional attribution checks both source→recipe→bytes→execution and
ROM→function→source, preserves source/revision differences and seeks
disconfirming paths. Independent source/raw and instruction/ABI reviews check
actual addresses, full states, eight-page replay and temporary ownership.
Names, similar functions and unchanged final fields alone do not prove a store.

| Conclusion | Established coverage | Remaining limit |
| --- | --- | --- |
| Documented provenance | Four exact pins, attr54 recipe and complete static caller | Original MWC/Thumb objects/map absent |
| Binary correspondence | Current EN/IT856execution bytes plus66static caller bytes, independent mapping | No rebuilt C binary or expanded historical-window lineage |
| Targeted semantic equivalence | Complete idempotent/causal move lifecycle, width2, keys, full ABI/maps/replay | Other attributes/slots/PIDs/flags/assert paths unqualified |
| Observed activation | Three isolated original EN calls,11340Thumb instructions, neutral OFF | No actual higher caller, Italian, save or physical execution |
| Still unattributed | Complete move caller joining both setters, getter and MaxPP | Longer context needs a separate contract and explicit limits |

First native matrix passes in1.654s/106266624B peak host RSS; verification
1.420s/103088128B and guarded replay1.468s/104595456B. Four owned kernels
take0.074s/39960576B. Limits:180s,1GiB RSS,2MiB log,16MiB case evidence;
predictor4096 and guest8192 instructions/1s remain unchanged. Host figures
are not game performance claims. The future complete caller is approximately
17198 instructions and cannot fit the current cap: it needs a new bounded
local policy, contextual forecast and review before execution.

Reusable results are the exact move reader, two-byte owned fixture, halfword
qualification/cache and idempotent-store verifier. A future optimization of
repeated crypto would require a separate game-change decision, caller/error/
ownership/save proofs and measured hardware benefit. No optimization is
implemented or claimed here.
