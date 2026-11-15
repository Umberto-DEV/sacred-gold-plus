# Native maximum PP through the complete memory-archive chain

The original `GetMoveMaxPP(310, ppUps)` executes its clamp, PP lookup, integer
multiplications, native signed division and u8 return. With PP=15 it returns
15 for zero PP-Ups and 24 for three or four. A declared source-memory PP=1
counterfactual returns 1 with three PP-Ups. No SDK model, test caller or runtime
host write supplies these results.

This extends the [complete PP getter](native-pp-memory-getter-source-rom-1.3.2.md).
See the [owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete ROM composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom).
These are isolated executions under an explicit memory-archive fixture;
in-game activation, natural CARD delivery and Mon setters remain separate.

## Inputs and source provenance

Use an owned exact r4 EN image: 152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`.
Optional current IT readback uses 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both current headers identify IPKE/revision 0; presentation language is a
separate property. Current execution uses EN only. No ROM, extracted member,
save, BIOS, private capture or personal path is distributed.

The clean source reference is [ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c)
commit `cb614ad23449d5852b40321dc409c4143872b35c`. Required source identities:

| Source relative to that checkout | SHA-256 |
| --- | --- |
| `src/move.c` | `e9adae2d57511a89ec5cc52ebb5741172a5d90123d02d33be66143ddf210e7b2` |
| `lib/MSL_C/src/msl_fp_runtime.c` | `4772579d74e6406a595ce01ebbbcc45b1f64bf7b7b79833b16b509f591c1dcaa` |
| `lib/MSL_C/src/msl_fp_runtime.alias-map.json` | `9d97f95c6184fe3607cf3a7a0a1c0c8342ea2244342bf0340ac9a1bd1e29a2f3` |
| `lib/asm/msl_fp_emulation_types.s` | `eb05b23346092145aac221d5fa2807c32976da12ff01abe63446f890f7194b06` |

`move.c` supplies the MaxPP C candidate. The MSL runtime contains the signed
integer division assembly at lines 2599–2731. Its alias map bounds offsets
`0x230C..0x2518`; this excludes the following unsigned routine. Documentation
and newer PRET checkouts are useful discovery references, but execution and
compilation remain bound to these exact inputs rather than silently following
upstream changes. See [using newer PRET references](../test-bench.md#using-newer-pret-references).

## Recovered compilation and installed bytes

The [division recipe](../../features/trainer-strategy/sorgenti/s32-div.S) is
compiled by [compila_s32_div.py](../../features/trainer-strategy/tools/compila_s32_div.py).
Before invoking the compiler, the builder expands its sole `.rept 32` loop and
compares all 131 instructions and the internal label to the authenticated MSL
body. It records source hashes, compiler identity, arguments, output and exit
code. The retained comparison object has one 524-byte text body, no relocation
and entry symbol `native_s32_div_recipe`.

The measured compiler was Apple Clang 21.0.0 (`clang-2100.4.1.1`), SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
Its ELF SHA-256 is
`0db63529b23cb790fabd2b48618da3b49c86265856427a04c8ddab0e28f2f4c4`.
The text hash below matches the installed division. The current builder and verifier require that exact compiler hash.
A different compiler requires separate qualification and an explicitly revised
receipt policy; recording its identity alone does not make it accepted.

| Component | Logical interval, end excluded | Current physical start | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| GetMoveMaxPP, Thumb | `0x0207332C..0x02073354` | `0x7732C` | 40 | `9a0f4b0193e9ec2c4fcffddf1526daf9a9bb23262051e5b6b6e986ffcba6ec9f` |
| `_s32_div_f`, ARM | `0x020F2998..0x020F2BA4` | `0xF6998` | 524 | `e8183a62ffe6a54210cd7d025b01431ff792025c1b45a0e8537abd8cec16ccfb` |

Both current ROMs store initialized ARM9 plainly at physical `0x4000`, loading
at `0x02000000`, length `0x12B8E4`; these functions are not overlays/autoload
or padding. The [independent reader](../../features/trainer-strategy/tools/rileggi_maxpp_memory.py)
compares direct physical bytes with ndspy-decoded ARM9 and checks instruction
boundaries. The MaxPP body has 18 Thumb starts. Division has 131 ARM words,
including the actual NOP at `0x020F2A08`; no pool, load/store, SP use or BL.
Its final `BX LR` is at `0x020F2BA0`.

A fresh eight-image comparison authenticated retail, inherited base 1.1,
Plus v4 and current r4 in both languages. All division bodies match the ELF.
Six images have direct physical division offset `0xF6998`. The two retail
ARM9 owners are BLZ-compressed: their receipts identify the complete stored
owner and decoded hash, and leave the per-instruction physical offset null.
Adding a RAM delta to a compressed owner's ROM offset is invalid. The current
public reader intentionally requires the plain current input; historical
lineage is supporting coverage, not an option exposed by this CLI.

The thirty SDK comparison objects from the [memory-Read recipe](native-fs-memory-read-source-rom-1.3.2.md#methods-components-and-recovered-compilation)
remain required. Together with the division this makes 31 authenticated ELF
bodies. The historical project driver is not mapped. Original Metrowerks
compiler/Thumb objects remain missing: MaxPP C-to-Thumb compilation and a
complete source-built ROM are not established by this recovered ARM recipe.
There is no installer or ROM mutation in this bench.

## Callers, ABI, state and resources

The isolated entry is the original MaxPP function in Thumb/System state,
R0=move 310, R1=PP-Ups 0, 3 or 4, with declared R2–R12 cookies and SP
`0x023FD000`. A game caller above that entry is not executed. MaxPP clamps
values above three, calls GetMoveAttr with attribute 5, then executes two
MULS and `_s32_div_f` for `PP*20*clampedUps / 100`. The quotient is added to
PP and narrowed by the actual LSL/LSR pair before return.

The [parent resource mapping](native-pp-memory-getter-source-rom-1.3.2.md#physical-and-logical-locations)
is unchanged: NARC 11 → `a/0/1/1` → filesystem ID 140 → member 310, 16 bytes,
PP at member byte 6. The ROM-derived fixture declares the memory archive,
cached FAT/FNT, callback `0x020D7448` and cleared procedure bits `0x600`.
It does not initialize native FILE/parser fields or return buffers on the host.
Four input fixtures are frozen before prediction and CPU execution; no private
capture is required or accepted through a snapshot option here.

MaxPP saves R3/R4/R5/LR in its 16-byte frame. The nested getter uses a 16-byte
buffer at top minus 40; the FILE is at top minus 152 and parser locals at top
minus 176. Combined peak is 656 bytes plus a separate 56-byte guard. All 19
mapped pages (77824 bytes), chronological accesses and exact saved-word owners
are checked. No heap allocation or global RNG participates.

Final R0 is the MaxPP result, R1 the division remainder, R2 either the short
path's preserved SDK residue `0x6000001F` or normal division residue `0x54`.
R3 and R4–R11 restore their cookies, IP=0, SP=entry top, LR=`0x0207334D`,
CPSR=`0x3F`. The division returns by BX through odd LR to Thumb `0x0207334C`.
Full16 means R0–R14 and CPSR; PC is checked separately.

## Qualified instructions and falsifiable predictions

The pinned SDK predictor remains unchanged. A separate [division oracle](../../features/trainer-strategy/test/arm32_div_oracle.py)
adds only RSB and ADC within the division body. ADC samples the input carry
from CPSR before operand shifting. The [MaxPP frontend](../../features/trainer-strategy/test/arm_thumb_maxpp_oracle.py)
adds Thumb LSR immediate, MULS and BLS. MULS preserves C/V under ARMv5;
Rd=Rm is rejected before effects because it is unpredictable before ARMv6.
These rules follow the primary [ARM Architecture Reference Manual, DDI0100I](https://documentation-service.arm.com/static/5f8dacc8f86e16515cdb865a)
(ADC, RSB, Thumb MUL and LSR). Fourteen owned synthetic CPU kernels qualified
the added arithmetic/router before any native guest. They contain no ROM
code or complete filesystem/division bodies.

Unicorn 2.1.4 CPU model 17 (Cortex-A15) executes each native run with one
uninterrupted `emu_start`. The backend is not an ARM946 timing/cache/interrupt
model; CP15 bit15 LOW/T-bit loading is an explicit inherited assumption.
No runtime register/memory response or copy is injected by the observer.

| Input | Native instructions (ARM + Thumb) | Unique PC | R0 / remainder | Division instructions |
| --- | --- | --- | --- | --- |
| PP15, Up3 | 6350 (6205 + 145) | 977 | 24 / 0 | 46 |
| PP15, Up0 | 6321 (6176 + 145) | 948 | 15 / 0 | 17 |
| PP15, Up4 | 6351 (6205 + 146) | 978 | 24 / 0 | 46 |
| PP1, Up3 | 6321 (6176 + 145) | 948 | 1 / 60 | 17 |

Each has 1741 reads, 1305 stores and a 656-byte peak. Numerators 0 and 60
use the short division path; 900 uses the normal path with computed branch
`0x020F2A04 → 0x020F2B5C`. Other numerators, negative values and denominator
zero are outside this finite qualification.

Up3 and Up4 converge at `0x02073338` after one extra real MOVS in Up4.
Their final full16/maps and all accesses match. The extra step stays in raw;
it is not discarded to force equality. The PP1 input changes only source byte
`0x02312272` before entry. Compared with PP15/Up3, read values 1583 and 1734,
copy-store 1215 and only two final bytes (source and buffer PP) differ.
The ROM stays unchanged; final R0=1 is produced by native copy, byte load and
arithmetic. All these deltas were predicted before CPU execution.

## Reproduction with owned inputs

Use the [project dependencies](../../requirements.txt): ndspy 4.2.0 and
Capstone 5 for readback/verification, plus Unicorn 2.1.4 for execution. The
ROM-free tests need only Python standard library. Raw verification imports no
CPU/assembler and invokes no compiler; use `-I` with site packages enabled,
not `-I -S`, for its ndspy/Capstone dependencies.

Set `SGP_MAXPP_ROM` to the owned EN image, `SGP_MAXPP_OBJECTS` to the parent's
thirty-object JSON mapping, `SGP_MAXPP_RECIPE` to its verified memory-Read
recipe, `SGP_MAXPP_REFERENCE` to the clean pinned checkout, and
`SGP_MAXPP_WORK` to a new private directory outside `source/`. Reproduce the
parent recipes first if those artifacts are unavailable. Record your compiler
path in `SGP_MAXPP_CC`. All output directories below must be new.

```sh
mkdir -p "$SGP_MAXPP_WORK"
.venv/bin/python3 -B source/features/trainer-strategy/tools/compila_s32_div.py \
  --reference "$SGP_MAXPP_REFERENCE" --cc "$SGP_MAXPP_CC" \
  --uscita "$SGP_MAXPP_WORK/div-recipe"
.venv/bin/python3 -B source/features/trainer-strategy/tools/rileggi_maxpp_memory.py \
  --rom "$SGP_MAXPP_ROM" --json "$SGP_MAXPP_WORK/resources.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/qualifica_maxpp_aritmetica.py \
  --json "$SGP_MAXPP_WORK/arithmetic.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/congela_maxpp_memory.py \
  --rom "$SGP_MAXPP_ROM" --json "$SGP_MAXPP_WORK/input.json"
for phase in prepare matrix; do
  .venv/bin/python3 -B source/features/trainer-strategy/tools/attribuisci_maxpp_memory.py \
    --mode "$phase" --rom "$SGP_MAXPP_ROM" --objects "$SGP_MAXPP_OBJECTS" \
    --recipe-dir "$SGP_MAXPP_RECIPE" --div-recipe "$SGP_MAXPP_WORK/div-recipe" \
    --reference "$SGP_MAXPP_REFERENCE" --input-contract "$SGP_MAXPP_WORK/input.json" \
    --out-dir "$SGP_MAXPP_WORK/$phase"
done
.venv/bin/python3 -I -B source/features/trainer-strategy/tools/attribuisci_maxpp_memory.py \
  --mode verify --rom "$SGP_MAXPP_ROM" --objects "$SGP_MAXPP_OBJECTS" \
  --recipe-dir "$SGP_MAXPP_RECIPE" --div-recipe "$SGP_MAXPP_WORK/div-recipe" \
  --reference "$SGP_MAXPP_REFERENCE" --input-contract "$SGP_MAXPP_WORK/input.json" \
  --raw-dir "$SGP_MAXPP_WORK/matrix" --out-dir "$SGP_MAXPP_WORK/verification"
for suite in test_arm32_div_oracle.py test_arm_thumb_maxpp_oracle.py \
             test_s32_div_recipe.py test_maxpp_memory.py; do
  python3 -I -S -B -m unittest discover \
    -s source/features/trainer-strategy/test -p "$suite"
done
```

The reader also accepts `--it-rom` for current IT byte readback. This bench has
no `--snapshot` or `probe` mode. Save all receipts and source bindings beside
raw before interpreting a verdict. Source drift invalidates verification.
Bound runs, logs and output; the recorded case used 180 seconds per command,
1 GiB host RSS, 2 MiB per log and 32 MiB logical evidence, with 1 GiB planned
disk peak and at least 10 GiB free afterward. Host costs are not DS timings.

## Results, review and limits

The final matrix has five cells: Up3, Up0, Up4, Up3 observer OFF and PP1Up3.
Four observed cells compare full16 at each PC, reads, store preimages and all
19 final pages. OFF preserves enforcement, final CPU, counters and maps.
Ten forged raw claims are rejected: missing clamp/division steps, zero
quotient, wrong carry context/scalar/remainder, input camouflage and wrong or
missing PP reads/copy stores. These are evidence forgeries, not guest runs.

There were ten actual native invocations. An earlier five-cell run saved
correct raw but exited 2 at its final negative-test classification: PP1 input
camouflage was rejected at counter comparison before the expected ABI check.
Only that expected reason string changed. Its tool version and raw were kept;
a source-bound five-cell rerun passes and all five raw are byte-identical to
the originals. This does not retroactively turn the first verdict into PASS.
No arithmetic, fixture, producer or expected native result was retuned.

Seventy-one ROM-free tests cover ARM arithmetic, Thumb/router admission,
source/recipe matching and ownership/CLI contracts, including parent regression
coverage. Independent reviews checked raw chronology and inverse replay,
19-page maps, 456 IRQ-leaf full16 caller/return transitions and all 16 actual
ADC transitions without using the new arithmetic predictor. CPU-free raw
verification also passes with CPU/assembler imports and compiler subprocesses
explicitly forbidden.

| Conclusion | Established coverage | Remaining limit |
| --- | --- | --- |
| Documented provenance | Pinned C, MSL assembly, alias bounds, source/recipe/toolchain receipts | Original MWC/Thumb objects missing |
| Reconstructed binary match | One newly compiled 524-byte division and 30 retained SDK bodies; current physical/decoded readback; eight division lineage images | No MaxPP C-to-Thumb rebuild or complete ROM build |
| Demonstrated targeted semantics | Four inputs, native clamp/multiply/divide/u8 path, ABI/access/maps and PP causality | No universal division/API/error-path equivalence |
| Observed activation | Five final isolated cells under declared EN memory archive | No natural game caller/CARD, IT execution or physical hardware claim |
| Unattributed links | Mon mutation/encryption and natural CARD delivery | Separate bounded work required |

The reusable result is a compiler-bound division recipe, finite ARM/Thumb
qualification and a source/byte/execution verifier. Reuse these before adding
another probe. A future error-path hardening or optimization would need an
explicit compatibility policy and separate validation; none is introduced by
this attribution work. ROM/save/default/ABI/ID and gameplay remain unchanged.

The [native Mon segment cipher](native-mon-cipher-source-rom-1.3.2.md) follows the original wrapper,
core and private LCG on 128 synthetic bytes. Two API seeds and neutral observer
OFF qualify native data/seed writes, stack lifetime and full ABI without player
records or global RNG access. The reusable fixture, frontend and verifier keep
C provenance, installed byte identity and finite semantics distinct from the
missing original C compiler.
