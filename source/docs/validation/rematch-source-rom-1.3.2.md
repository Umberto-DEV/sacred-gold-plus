# Inert rematch module: source, exact ROM and loader lifetime

The r4 EN/IT images contain the same reconstructed 64-byte resident allocation
and 2048-byte overlay126 image. The installed activation byte is **0**. A bounded
execution of the real trainer-party constructor prefix reaches the real reader,
forwards its return value and restores the overlay registry on successful,
refused and failed loads. This establishes initialized inert forwarding;
phone/Dojo activation, a complete party and natural gameplay are unobserved here.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Trace both directions: authored C/ASM and configuration → authenticated compile
and relocation → cartridge insertion → independent readback; then cartridge BL
→ resident stub → loader → module/native reader → unload → caller return.
Separate Plus source, inherited WFC code, native HGSS functions, literal pools,
configuration and allocation padding. Ask whether a same-output implementation
could leak overlay126: it can, so buffer equality alone is an insufficient oracle.

An independent review checked raw identities, staging, addresses, frame offsets,
code/data guards and selected IT executions. It confirmed the missing-unload,
wrong-argument and literal-pool counterproofs. Native original HGSS objects and
its MW toolchain are absent; native source correspondence is distinct from a
native binary reconstruction. No game change follows from this attribution.

## Il materiale più grezzo da cui partire

Use your own legally obtained ROM/patch inputs. Keep complete ROMs, extracted
archives, compiled data containing trainer records, saves, BIOS and raw captures
outside the public tree. These are SHA-256 identities, not download locations:

| Input | EN SHA-256 / bytes | IT SHA-256 / bytes |
| --- | --- | --- |
| Retail HeartGold, revision0 | `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105` / 134217728 | `013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1` / 134217728 |
| Historical Plus1.1 | `281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d` / 127104144 | `7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077` / 131906120 |
| V4 balance493 pre-stage | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` / 147345256 | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` / 153228136 |
| Exact r4 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` / 152786844 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` / 159029760 |

The reader checks full identity, header/revision, FAT/FNT, overlay rows and ARM9
sections through the [shared exact-ROM reader](../../features/fairy-ai/tools/attribuisci.py).
The r4 IT header has code IPKE; select language by the authenticated full hash.
[Distribution identity](../../distribution/game-1.3.2-r4.json) and
[baseline pins](../../sgp131/baseline.py) define the required revisions.

Source ownership: [stub.S](../../features/rematch-variants/stub.S),
[native.c](../../features/rematch-variants/native.c),
[variants.c](../../features/rematch-variants/variants.c),
[variants.h](../../features/rematch-variants/variants.h),
[authored specification](../../sgp131/data/rematch-variants.json),
[ABI facts](../../sgp131/data/rematch-native-abi.json),
[compiler/materializer/installer](../../sgp131/rematches.py) and
[cartridge composer](../../sgp131/cartridge_deltas.py).
The [feature guide](../rematch-variants-1.3.1.md) describes activation requirements;
this case leaves those requirements pending.

### Build and composition

Apple clang21.0.0 `(clang-2100.4.1.1)`, SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
compiles ARMv5TE / ARM946E-S Thumb with `-Os -ffreestanding -fno-builtin
-fno-stack-protector -fno-jump-tables -fno-unwind-tables
-fno-asynchronous-unwind-tables -Wall -Wextra -Werror`.
Defines are `REMATCH_CONFIG_ADDR=0x0226B500u`, `REMATCH_CONFIG_BYTES=768u`,
`REMATCH_HOST_SP_OFFSET=48`. The stub uses `assembler-with-cpp` with ID126,
ENTRY `0x0226B4A1`, NATIVE `0x020735E9`, HLO `0x02006FF9`, ULO `0x02006F7D`.

There is no separate linker: the [production ELF loader](../../features/options/tools/carica_text.py)
relocates `.text` internal Thumb BL / ABS32 references. An independent parser in
the attribution tool verifies both objects, both internal C BL relocations,
every non-relocation byte and all repeated `$t`/`$d` mapping symbols. `.ARM.exidx`
is ignored under the existing no-unwind recipe; no other allocated section or
external symbol is permitted. Object retention is opt-in; default payload,
symbols and object deletion remain unchanged. Objects and maps are recorded locally.

| Part | RAM / layout | SHA-256 |
| --- | --- | --- |
| C payload | `0226B000`, 1216B +64B zero padding | `ca10a77bbe126b3a5450dcd630d30534232889d51bfcae2fe308679202af5a5e` |
| Configuration | `0226B500`, 716B +52B zero padding | `17092ba4b839c3547063f1230d81b0e7ee6f96648793759d42f65b7459c959be` |
| Full overlay126 | 2048B, no compression/BSS/initializer | `1777e2caab05aa3dbc1afcff721d72c394aee4a50322e2b38d8d820c5a6b0258` |
| Resident allocation | `023D59E0`, 60B +4B zero padding | `77844c84762bcdf84e64503a1e0996c871c8ca1027846b8059e5b5b86a8688ce` |

Module symbols: `rematch_select=0226B001`, `rematch_apply=0226B00D`,
`rematch_native=0226B3DD`, `rematch_hook=0226B4A1` (Thumb bit included).
The resident 60B consist of 42B instructions, 2B alignment and 16B literal pool.
The C object contains five code islands separated by five data islands; the
final literal at `0226B4BC` belongs to the hook, not executable code.

The installer obtains c8.module-stubs from the reserve receipt, rewrites the
constructor BL at `0207363A` and replaces file126/FAT/y9, appending its image.
The composer's deferred resident writes preserve the other 128B of the shared
192B allocation. Those bytes belong to [U-turn](uturn-source-rom-1.3.2.md), not
rematch padding. V4 has zeroes in this allocation; retail/Plus1.1 do not map it.
Missing mapping is not evidence of padding.

| Installed span | EN physical ROM | IT physical ROM |
| --- | --- | --- |
| Stub allocation64 | `001252A0..001252E0` | `001252A0..001252E0` |
| Constructor seam4 | `0007763A..0007763E` | `0007763A..0007763E` |
| Native reader16 | `000775E8..000775F8` | `000775E8..000775F8` |
| Module file2048 | `091B4F9C..091B579C` | `097A9200..097A9A00` |

The tool emits independent ARM9 physical offsets for the seam and native reader,
section mappings, complete y9/FAT rows, member offsets, stored/decoded hashes and
compression receipts. Overlay126 row is `[126,0x0226B000,2048,0,0x0226B000,
0x0226B000,126,0]`. Historical file126 is a 20B BLZ placeholder decoding to32B.
Do not apply a linear physical-offset formula across compressed overlays.

### Respect the stage preimage

Run the original full semantic guard on V4. Applying it indiscriminately to r4
correctly refuses `archive preimage differs: a/0/5/6`. The subsequent
[trainer correction](../../sgp131/trainer_fixes.py) swaps Wade460/461 (32B each).
The tool proves this exact swap, preserved headers/personal/learnsets/egg/item
archives and all declared move records/TM entries. It then materializes the exact
configuration from V4 with battle types `(1,2049)` and enemy index1 and requires
identical materialization from the relevant final records712/713. It neither
weakens the original preimage guard nor claims it passes on the final archive.
The default `(1,)` materialization has a different hash and is not the installed
configuration.

### Callers, ABI and lifetime

The native constructor spans `02073604..02073A98` (1172B). Retail/Plus1.1 → V4
changes only the four documented level-read sites. V4 → r4 changes only the
reader BL: native target `020735E8` → resident `023D59E0`; reversing those four
bytes restores constructor SHA
`0e58b8aae7ba33081541d4f50f748c7ea1fffe9c084eee23d95af0e9f648f38b`.
The tested prefix stops on return at `0207363E`, before executing that instruction.

At the seam, R0=trainer712/713, R1=108B transient buffer, R4=BattleSetup,
R6=236B workspace, R7=enemy index×4. The native frame is152B; host offsets are
index `SP+10`, saved seed `SP+68`, buffer pointer `SP+74` (hex).
The stub pushes `{r0,r1,r2,lr}` (16B); the module hook adds32B, so the host SP
is its SP+48. It calls the native reader once, returns its exact R0, restores
R1/R2 and R4–R11 and restores SP. The native-control reader's R1/R2 are volatile.

The actual party-reader extent is16B: 10B code, 2B alignment, 4B literal.
It tail-calls `02007508` with `(buffer,56,trainer)`. Its 28B historical hash pin
also includes the adjacent 12B trainer-header thunk; the latter contains a
regional literal difference. The party-reader16B are identical across all eight
inputs. Never label the whole28B as one function.

Real `HandleLoadOverlay=02006FF8` checks the registry via CanOverlayBeLoaded,
then writes active1 at PC `0200702E` and ID126 at `02007030` **before** FS image
loading. Busy overlay12 causes refusal before registration. FS failure leaves
126 registered until the stub's real `UnloadOverlayByID=02006F7C` executes;
real unload-record code clears active at `02006F78`. The 300B loader hash window
includes both HandleLoadOverlay180B and CanOverlayBeLoaded120B.

Its successful return is inherited Plus code: V4/r4 replace the retail return
with a BL to WFC bridge `023DA47C`, which runs helper `023DA3CC`. For ID126 this
only increments the overlay-load counter at `023DA044`. The exact archived
[WFC bundle](../../sgp12/build/wifi/vfinale/manifesto.json) matches current bytes.
Its recorded clang version differs from this rematch compiler: this is archived
binary correspondence plus [source correspondence](../../features/native-core/sorgenti-v-finale/wifi_slot4.c),
not a fresh WFC rebuild. FS failure executes actual GF_AssertFail only with the
fixture's CommState pointer NULL; other assertion/error states are unqualified.

## I metodi e gli strumenti da usare

Install the [test dependencies](../../requirements.txt) in your own virtual
environment. Qualified versions: Python3.14.7, ndspy4.2.0, Capstone5.0.9,
Unicorn2.1.4 and the authenticated compiler above. The command uses the
[attribution utility](../../features/rematch-variants/tools/attribuisci.py) and the
existing [constructor bench](../../features/rematch-variants/test/constructor_bench.py)
through a bounded mmap adapter, avoiding full-ROM heap copies. From repository root:

```sh
python source/features/rematch-variants/tools/attribuisci.py \
  --rom /private-inputs/r4-EN.nds --v4 /private-inputs/v4-EN.nds \
  --base /private-inputs/plus-1.1-en.nds --retail /private-inputs/retail-EN.nds \
  --language EN --work /private-results/rematch-EN-build \
  --json /private-results/rematch-EN.json
```

Use corresponding IT inputs and `--language IT` for the second run. Work directory
and JSON must be new, distinct, outside `source`; existing files/aliases are
refused. Exit0 means this bounded attribution passed, exit2 means validation
refused. Retain argv, exit code, source hashes and resource limits alongside the
JSON and private objects. Run without Python `-O` (inherited assertions required).

```sh
PYTHONPATH=source SGP_R4_ROM_DIR=/private-inputs \
  python source/features/rematch-variants/test/test_attribution.py
```

Tests expect `r4-EN.nds`/`r4-IT.nds`; optional `SGP_R4_ROM_NOME` is a single `%s`
pattern. Without exact-current inputs the five Class B methods skip: such a run
does not qualify runtime evidence. Two retention methods and CLI hygiene are
ROM-free. The qualified run executed all eight methods without skips.

The real guest runs constructor entry → native party initialization/encryption
of empty slots → allocations → seam → stub/module/native reader/load/unload →
seam return. SDK heap, archive transport and FS info/image/start/unload are
models with checked ABI; no existing full-constructor result is inherited.
Unloading fills module RAM with diagnostic poison to expose use-after-unload;
it does not claim real FS erases RAM. Reader returns `5EED0001`,0,`FFFFFFFF` are
synthetic ABI sentinels, not measured SDK outputs. Raw trainer bytes come from
the authenticated input. Original fixtures are never written.

Code guards admit only pinned native instruction blocks and independent ELF
code maps, with exact width/Thumb/ARM mode and byte checks. Data/pool fetches,
unexpected stores, SDK arguments, frame disagreement, overflow/instruction budget,
changed canaries, seed drift and unrelated main RAM changes fail. Registry stores
are bound to their exact PCs. Current/native RAM comparison masks only declared
stack, loader registry/module, WFC counter and the four-byte control seam.

Success criteria include **all** of readback, reader once, exact return/ABI,
108B buffer equality, both allocation canaries, stack canary, unchanged seed,
empty-party header `[6,0]`, full registry lifetime, config short-circuit reads
and PC-specific native stores. Each language covers 12 positive paths
(2trainers×2Plus states×3load outcomes),8 native controls and2 return sentinels.
Four counterproofs cover missing unload on success/failure (same R0 and buffer
but active126 remains), wrong fallback argument before copying, and a real
fetch at the unchanged stub literal pool. Counter mutations exist only in named
RAM copies after normal exact-ROM admission.

### Result, coverage and next checks

Documented provenance and exact binary reconstruction are established for the
owned C/stub/configuration. Initialized inert semantic equivalence and native
load/unload execution are established within the declared model boundaries.
Natural activation is **not observed**. Active variants, full party construction,
context provenance in phone/Dojo, original native MW compilation, other overlay
lifetimes, SAVE/cold restart/device and gameplay timings remain separate checks.

For these fixtures the instruction-hook counts are17710 success,17596 refusal,
17671 FS failure versus17367 native control; maximum observed stack depth288B
versus216B. They establish nonzero initialized work, not console cycles or UI
performance. An inert fast path is a possible future optimization, with medium
implementation cost and significant activation/lifetime regression risk. Any
proposal needs all state/return/registry/activation checks and natural runtime
measurement; this attribution does not implement or authorize it.

The reusable outputs are strict ELF/readback/mmap checks, code/data guards,
SDK ABI boundaries, teardown and equal-output counterproofs. Continue with a
finite question about active configuration gates or a later native caller;
do not turn inert forwarding into an activation or universal compatibility claim.
