# Native GetSubstruct: source table, exact ROM and every selector

The complete original `GetSubstruct` returns the physical 32-byte block selected
by its PID argument and logical block ID. All 128 table selections pass native
execution, followed by an ignored-PID-bit counterfactual and observer OFF:
130 calls, 2210 original Thumb instructions, no models or runtime host writes.
The function reads no Box header or payload; it computes a pointer.

This follows [native MaxPP](native-maxpp-memory-source-rom-1.3.2.md),
[cipher](native-mon-cipher-source-rom-1.3.2.md) and
[checksum](native-mon-checksum-source-rom-1.3.2.md) toward the encrypted Mon-data
lifecycle. See the [owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete ROM composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom).
The complete getter/setter caller remains a separate question.

## Inputs, provenance and compilation boundary

Use an owned current r4 EN ROM: 152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`.
Optional current IT readback uses 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both current headers identify IPKE/revision 0; presentation language is separate.
Only EN executes here. No ROM, extracted retail table, save, BIOS, private
capture or personal Pokémon record is published as a fixture.

The clean production source pin is `cb614ad23449d5852b40321dc409c4143872b35c`
in [ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c). Required files:

| File | SHA-256 |
| --- | --- |
| `src/pokemon.c` | `1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3` |
| `include/pokemon.h` | `54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1` |
| `include/pokemon_types_def.h` | `032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d` |

`pokemon.c:3951–3990` defines the table and selector. The structure definition
places four 32-byte blocks after the eight-byte Box header. The C recipe is
`row=(pid & 0x3E000)>>13`, check which<=3, then return
`BoxBase + 8 + offsets[row][which]`. A bounded parser compares all 128 source
array bytes with the installed table. It parses this pinned C subset without
evaluating code; it is not a general C equivalence checker.

Original Metrowerks compiler and Thumb objects remain unavailable. No new
compiler, comparison ELF or installer is used. Documented source provenance,
installed byte correspondence and targeted execution semantics are established;
original C-to-Thumb reconstruction and a complete source-built Italian ROM
remain open. The valid-path body and table originate in retail HGSS; the
inherited Italian base changes the table pointer as shown below.

## Code, literal, table and historical readback

Current ARM9 is plain, physical `0x4000`, RAM `0x02000000`, initialized length
`0x12B8E4`, entry `0x02000800`. These windows belong to initialized ARM9,
without an overlay or autoload dependency. The
[current reader](../../features/trainer-strategy/tools/rileggi_mon_substruct.py)
streams whole-ROM identity and compares physical bytes with independent ndspy
decoding, retaining only the bounded ARM9 owner and selected spans.

| Component | Logical interval, end excluded | Physical start | Bytes / starts | SHA-256 |
| --- | --- | --- | --- | --- |
| Prefix and valid guard | `0x02072608..0x0207261C` | `0x76608` | 20 / 10 | `426d3165503db1e38d2178aebc8b6e747de61d32df1fb4ce671fb3b662a2a108` |
| Lookup and return | `0x02072620..0x0207262E` | `0x76620` | 14 / 7 | `1e669de78867533449de32f097484d90e484fc145a2a57c0d2640bd9d0c34991` |
| Table literal, data | `0x02072630..0x02072634` | `0x76630` | 4 / 0 | `bdd9e387f769acd6c58a3637a6ebb45bc5cd102462572d8d4ee0416e0a3d81fb` |
| Offset table, data | `0x020FF733..0x020FF7B3` | `0x103733` | 128 / 0 | `13df5d291eb7b8276c065d7033d8044a9b430df77c05d04069cd3438e54b179a` |

The table pointer is byte-addressed and unaligned. Its low bit is data,
not a Thumb-state bit to clear. The literal is word-aligned. The invalid-which
assert BL at `0x0207261C..0x02072620`, padding at `0x0207262E..0x02072630`
and neighboring functions are outside the admitted code. Host profile rejection
of which4/255 does not qualify that native assert path.

The [lineage reader](../../features/trainer-strategy/tools/rileggi_mon_substruct_lineage.py)
independently locates the two code fingerprints in decoded sections, then
follows the actual Thumb LDR literal. It does not assume the current entry
or table address. A fresh retail → base1.1 → V4 → r4 comparison in both
languages finds the same entry `0x02072608`, 34 code bytes and 128 table values
in all eight images. One literal differs:

| Image | Table pointer | Literal SHA-256 |
| --- | --- | --- |
| Retail IT | `0x020FF6AB` | `076b2c992cdab1a150ba421e14c9acd1f668cc264fd4f747fae8ebb847391c10` |
| Retail EN and all six base/V4/r4 images | `0x020FF733` | current literal hash above |

The retail Italian table lies `0x88` bytes earlier; its values still match.
This is a concrete language/revision difference, not a general relocation rule.
Do not describe the complete 166-byte component as identical across all images.

Exact historical identities are declared in [base11.json](../../sgp12/base11.json),
[bootstrap-13-v4.json](../../distribution/bootstrap-13-v4.json) and
[release-1.3.2-r4.json](../../distribution/release-1.3.2-r4.json):

| Role | EN bytes / SHA-256 | IT bytes / SHA-256 |
| --- | --- | --- |
| Retail | 134217728 / `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105` | 134217728 / `013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1` |
| Base1.1 | 127104144 / `281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d` | 131906120 / `7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077` |
| V4 | 147345256 / `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` | 153228136 / `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` |
| r4 | current EN identity above | current IT identity above |

The six plain images pass direct physical checks for all four ROIs. Both
retail ARM9 owners are BLZ-compressed: receipts identify stored range/hash,
expanded hash and decoded owner; per-instruction physical offsets remain null.
No linear ROM offset is invented inside the compressed stream. Historical
activation or whole-image equivalence is not inferred from these readbacks.

## Callers, owned state, lifetime and ABI

Source callers include GetBoxMonDataInternal and SetBoxMonDataInternal,
selecting logical A/B/C/D blocks with the object's PID. This case enters
GetSubstruct directly; it does not prove that a caller read and passed the
correct PID from a Box header. Opaque 136-byte A5 storage at `0x022F0400`
is sufficient. It is not a validated or encrypted Pokémon.

The [freezer](../../features/trainer-strategy/tools/congela_mon_substruct.py)
records 129 distinct inputs and an explicit 130-call plan before prediction
and native execution: PID=row<<13 for every row0..31/which0..3, one alias
`0x80006001` for row3/which1 and OFF of the canonical row3/which1 input.
All initial memory is identical; only API registers vary. There are four
sparse pages, 16384 bytes: code, table, Box/return gate and stack. Two
16-byte D3 guards surround the 136-byte storage. Stack frame is 16 bytes,
with a separate 56-byte A5 guard.

Entry is Thumb/System, R0=BoxBase, R1=PIDu32, R2=which zero-extendedu8,
R3–R12 declared cookies, SP=`0x023FD000`, LR=`0x022F0181`, CPSR=`0x6000003F`.
PUSH at `0x02072608` saves R4/R5/R6/LR in four words at top−16..top.
The valid path has no BL. Final POP at `0x0207262C` restores R4/R5/R6 and
loads PC from the saved caller return word.

Final R0=`BoxBase+8+offset`, R1=`4*row`, R2=which; R3–R12 retain entry cookies,
SP=entry top, LR retains entry sentinel, CPSR=`0x3F`. The returned entire
32-byte block must lie within BoxBase+8..BoxBase+136. Full16 means R0–R14
plus CPSR, with PC checked separately.
R1 is observed volatile return state, not an additional C callee-save promise;
the complete context is retained for attribution and caller checks.

Read owners are exactly one four-byte literal read at `0x02072620`, one
one-byte table read at `0x02072626` for the declared row/selector, and four
saved-word reads at the POP. Only the four PUSH writes are permitted. No
Box header/payload, global RNG, heap, FS, callback or IRQ access is admitted.
All pages, guards, chronological accesses, preimages and forward/inverse
four-store replay are checked by the
[bench](../../features/trainer-strategy/test/mon_substruct_bench.py).

## Qualified instructions, causal tests and receipt reuse

The [finite frontend](../../features/trainer-strategy/test/arm_thumb_substruct_oracle.py)
adds only ANDS low register and LDRB register offset to the pinned cipher
frontend. AND updates N/Z while preserving C/V; register LDRB sums the two
old operands modulo32, reads one byte without alignment and zero-extends it,
preserving flags. These follow [ARM DDI0100I](https://documentation-service.arm.com/static/5f8dacc8f86e16515cdb865a)
Thumb AND A7-14 and LDRB(2) A7-56. The run retains the exact parent bytecode,
defaults and complete effective namespace with three explicit bindings changed.

Six owned instruction kernels qualify flags, unaligned bytes, zero extension,
register aliases and address wrap before original-code execution. Their
[4184-byte receipt](../../features/trainer-strategy/test/substruct-instruction-qualification.json)
is safe to distribute: owned synthetic programs, relative source identities,
register results and flow hashes, without ROM code/data. Reuse it when its
four source pins match; the CLI checks exact full16 and two-step flow digest
for every named kernel, metadata types and completed checks. The
[qualification tool](../../features/trainer-strategy/tools/qualifica_mon_substruct.py)
can regenerate a private receipt with the documented backend.

An early verifier accepted wrong kernel results when shape/metadata matched.
Before any original GetSubstruct guest, two forgeries reproduced that gap and
the gate was strengthened. The original six CPU programs/receipt remain
unchanged. Four regression tests and the distributed owned fixture prevent
that false success. Four additional source/type/completeness receipt forgeries
are rejected. These are separate from the 19 native-raw forgeries below.

Each native call executes 17 Thumb instructions, visits 17 PCs, makes six
reads/four stores, has a 16-byte stack peak and 18 callbacks including the
unexecuted return gate. One uninterrupted `emu_start` uses the unchanged NARC
producer bytecode with new input/code namespace and an empty ARM corpus.
Only admission sets reach it, never expected arithmetic responses. Predictor
cap is64; inherited guest cap8192 with one-second timeout. Backend is Unicorn
2.1.4 CPU17 (Cortex-A15), without an ARM946 timing/cache/interrupt claim.

Two counterproofs matter beyond correct pointers:

- Row24 repeats row0's four output pointers, but R1final=96 rather than0 and
  each table read is96 bytes later. All128 table bytes are actually read by
  the grid. A row%24 substitution can preserve the C pointer result while failing the
  installed-instruction/volatile-state/readback attribution.
- PID `0x6000` and `0x80006001`, which1, give identical final full16/maps and
  accesses. Raw R1/R4 and intermediate N differ; full16 joins at `0x02072624`
  after LSLr1. The real prefix is retained, without normalization.

Observer OFF preserves enforcement, counters, CPU and maps with no observation
ledger. Nineteen native-raw forgeries reject normalized row24 ABI/read, aligned
literal, word load, AND→EOR, omitted bit17, transposed selector, bad stack
preimage/POP/LR, extra Box read, admitted assert/padding, PID camouflage/prefix
normalization, bool/signed metadata, table write and omitted header offset.
These are CPU-free evidence mutations, not extra native guests.

## Reproduction with owned inputs

Use [project requirements](../../requirements.txt): ndspy4.2.0 and Capstone5
for readback/verification, plus Unicorn2.1.4 for execution. ROM-free tests and
PRET source alignment use only standard library. CPU-free raw verification
uses `-I` with site packages enabled; CPU/assembler imports and compiler
subprocesses were also explicitly forbidden in a second successful check.

Set `SGP_SUBSTRUCT_ROM` to the owned exact EN image,
`SGP_SUBSTRUCT_REFERENCE` to the clean production source checkout and
`SGP_SUBSTRUCT_WORK` to a new private directory outside `source/`.
No save, capture, BIOS or SDK object is needed. Outputs must be new.

```sh
mkdir -p "$SGP_SUBSTRUCT_WORK"
SGP_SUBSTRUCT_QUAL=source/features/trainer-strategy/test/substruct-instruction-qualification.json
.venv/bin/python3 -B source/features/trainer-strategy/tools/rileggi_mon_substruct.py \
  --rom "$SGP_SUBSTRUCT_ROM" --json "$SGP_SUBSTRUCT_WORK/resources.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/congela_mon_substruct.py \
  --rom "$SGP_SUBSTRUCT_ROM" --json "$SGP_SUBSTRUCT_WORK/input.json"
for phase in prepare matrix; do
  .venv/bin/python3 -B source/features/trainer-strategy/tools/attribuisci_mon_substruct.py \
    --mode "$phase" --rom "$SGP_SUBSTRUCT_ROM" --reference "$SGP_SUBSTRUCT_REFERENCE" \
    --input-contract "$SGP_SUBSTRUCT_WORK/input.json" --qualification "$SGP_SUBSTRUCT_QUAL" \
    --out-dir "$SGP_SUBSTRUCT_WORK/$phase"
done
.venv/bin/python3 -I -B source/features/trainer-strategy/tools/attribuisci_mon_substruct.py \
  --mode verify --rom "$SGP_SUBSTRUCT_ROM" --reference "$SGP_SUBSTRUCT_REFERENCE" \
  --input-contract "$SGP_SUBSTRUCT_WORK/input.json" --qualification "$SGP_SUBSTRUCT_QUAL" \
  --raw-dir "$SGP_SUBSTRUCT_WORK/matrix" --out-dir "$SGP_SUBSTRUCT_WORK/verification"
for suite in test_arm_thumb_substruct_oracle.py test_mon_substruct.py \
             test_mon_substruct_cli.py test_mon_pret_alignment.py; do
  python3 -I -S -B -m unittest discover \
    -s source/features/trainer-strategy/test -p "$suite"
done
```

To regenerate the instruction receipt rather than reuse its exact qualified
source version, run `qualifica_mon_substruct.py --json` with a new private
path and use that path as `SGP_SUBSTRUCT_QUAL`. The reader optionally accepts
`--it-rom`. There is no snapshot or probe mode. Frozen input, qualification,
source drift and exact raw file hashes are bound to the completed matrix
report; raw is saved before the verdict.

For optional historical readback, set the four owned paths for one language:

```sh
.venv/bin/python3 -B source/features/trainer-strategy/tools/rileggi_mon_substruct_lineage.py \
  --retail "$SGP_SUBSTRUCT_RETAIL" --base "$SGP_SUBSTRUCT_BASE" \
  --v4 "$SGP_SUBSTRUCT_V4" --rom "$SGP_SUBSTRUCT_ROM" --language EN \
  --json "$SGP_SUBSTRUCT_WORK/lineage-EN.json"
```

Repeat with all four Italian inputs, `--language IT` and a new output path.
This new166-byte ROI is distinct from the old172-byte PP-provider lineage;
no completed native execution campaign is repeated by this read-only check.

## Aligning with the newer PRET sources

The optional [source comparison tool](../../features/trainer-strategy/tools/confronta_mon_pret.py)
uses the read-only HeartGold pin `6bf138d6035aa6b43d6f8f4132a12df70f86dcec`
and Platinum pin `62bdaacdca6c56a6a396f3e9911e2f922b79bba8`.
Whole C files changed, while four complete HGSS function fragments are byte
identical to production:

| Component | Fragment bytes / SHA-256 |
| --- | --- |
| Checksum | 187 / `8c52331e3092b8f8223569aa70b046aa75a0a3ecf0791603623f34527ed19681` |
| GetSubstruct | 1418 / `157a4ae5396adfa3abbd06b5230071d962360758d31e01157955a81c7e783eba` |
| Cipher core | 159 / `a9c35a727e4bf07d19256c2f8c1d7c5e31145c8e6dd667c7226efc440882d3d3` |
| Local LCG | 116 / `8033b79cff387722fb9309e0ae477b6903dfa4475080d4d2d2097f23a91147e6` |

Platinum's selector uses a switch and macro, with the same128 block-index
mappings after normalization to HGSS32-byte offsets. Its checksum declares
`static u16`, compared with HGSS`u32`. Source recipes for local LCG and
checksum agree; compiled addresses, volatile ABI and Italian build support
are separate evidence. The adapter checks exact source pins/hashes and a
bounded macro/switch grammar; it is not a future arbitrary-C solver or a
measurement of Platinum's binary layout.

```sh
python3 -I -S -B source/features/trainer-strategy/tools/confronta_mon_pret.py \
  --reference "$SGP_SUBSTRUCT_REFERENCE" --heartgold-ref "$SGP_PRET_HGSS" \
  --platinum-ref "$SGP_PRET_PLATINUM" --json "$SGP_SUBSTRUCT_WORK/source-alignment.json"
```

This gives other developers and coding assistants a repeatable way to reuse
unchanged components, learn from a second implementation and detect differences
before transferring assumptions. See [newer PRET references](../test-bench.md#using-newer-pret-references).

## Results, reviews and remaining gaps

The first129 source forecasts and first130 native calls agree without changing
native expected values, fixtures or producer. Independent reviews check every
raw/hash, all128 table reads, full ABI and the 129 observed four-store inverse
replays, four final pages per call and absence of Box access. A separate
stdlib review verifies129 ANDS/LDRB next-state transitions and raw chronology.

Forty ROM-free tests cover arithmetic, owners, parser/locator, receipt rejection
and PRET source adapters. The matrix costs1.822s/115261440B peak host RSS;
CPU-free verification1.537s/58589184B and guarded verification1.500s/57344000B.
The eight-image readback costs1.129s/38780928B. Budget:180s per command,
1GiB host RSS,2MiB log,16MiB evidence; planned total≤9MiB,1GiB disk peak and
at least10GiB free afterward. These host figures are not DS timings or a game
speedup. Core runtime31source bindings remain unchanged after native execution;
source alignment/lineage readers are independent, separately identified tools.

| Conclusion | Established coverage | Remaining limit |
| --- | --- | --- |
| Documented provenance | Exact C/header/structure pin; newer HGSS components unchanged; Platinum source comparison | Original MWC/Thumb objects absent |
| Binary correspondence |34native code bytes and128table bytes across eight exact images; IT retail literal difference located; current physical/decoded mapping | No reconstructed original C object or whole-ROM equivalence |
| Targeted semantics | Every32row×4selector; one ignored-PID control; exact pointer/ABI/access/replay/pages | No empirical coverage of every u32 PID or invalid-which native assertion |
| Observed activation |130isolated EN API calls, neutral OFF | No natural getter/setter caller, header-PID binding, IT or physical run |
| Still unattributed | Complete encrypted Box data lifecycle | Requires its own source/byte/caller/state contract |

No gameplay, ROM, save layout, IDs, ABI or defaults change. The reusable outputs
are exact readers, owned fixtures/qualification receipt, finite frontend,
source-alignment adapter and verification commands, without private ROM data.

The [complete encrypted Box PP-Up getter](native-box-ppup-source-rom-1.3.2.md)
subsequently binds the PID to native header loads and composes these selectors
with decrypt, checksum and re-encryption. Its own caller, fixture and stack
proof qualify that context; the standalone selector coverage above is unchanged.
