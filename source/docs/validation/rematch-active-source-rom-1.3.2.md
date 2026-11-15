# Rematch active gates and native buffer copy in RAM

The exact installed r4 module remains **active0**. This case first authenticates
that image, then applies named shadows to a fresh emulated RAM instance. Real
native code selects the authored A/B party and copies108B under the exercised
gates. It returns the original reader result and unloads overlay126. This proves
finite initialized active semantics, not natural phone/Dojo activation or an
authorized change to the installed game.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Continue the [inert attribution](rematch-source-rom-1.3.2.md) into the actual
native wrapper/core. Verify source-defined gates, saved-seed selection, the
entire baseline precondition, both variants' integrity and all108 guest stores.
Require the helper's complete return and caller ABI independently of buffer
hashes. A single same-output counter can disprove a weaker oracle.

Independent review checked the raw code and source, repeated selected IT paths
and counterproofs without invoking a compiler, and distinguished the helper's
1/2 result from the SDK reader's forwarded R0. None of these observations removes
the runtime-context proof required by the [activation design](../rematch-variants-1.3.1.md).

## Il materiale più grezzo da cui partire

Use your own exact r4 ROM and retained objects from the inert case. Its
[input identity table](rematch-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire)
provides size/language/revision/provenance for retail, Plus1.1, V4 and r4.
Only r4 and the two objects are read by this continuation:

| Input | SHA-256 |
| --- | --- |
| r4 EN,152786844B | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| r4 IT,159029760B | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |
| rematch-variants.o | `cfc4dce49574df18f3064fb66c2f8d75b66f5e6ed63e26d36e97893e2168817a` |
| rematch-stub.o | `43848467a67b11f1fec275a63e89f861c8641f325c86af38df03320a10d7c68a` |

The [inert verifier](../../features/rematch-variants/tools/attribuisci.py)
produces the objects with authenticated clang21.0.0 `(clang-2100.4.1.1)` and the
pinned flags/defines. This continuation invokes no compiler. It verifies each
object SHA, independent ELF/relocation/code-map readback against the installed
payload, exact source snapshots and full-ROM/ARM9/FAT/y9 identity before any
shadow. Module126/stub/seam physical offsets, compression, allocation padding,
inherited WFC and HGSS provenance remain as documented in the inert case.

The source is [native.c](../../features/rematch-variants/native.c),
[variants.c](../../features/rematch-variants/variants.c),
[variants.h](../../features/rematch-variants/variants.h),
[stub.S](../../features/rematch-variants/stub.S) and the
[authored specification](../../sgp131/data/rematch-variants.json).
A separate tuple encoder applies the declared before/after changes and packs
six18B records, checking each authored SHA. It does not call the production
materializer or its party encoder to obtain the expected result.

### Native data flow

`rematch_hook=0226B4A1` calls the real reader once before
`rematch_native=0226B3DD`. The wrapper's active1 branch checks Plus exactly1,
context type, enemy-index mask, host buffer/trainer agreement and trainer header.
It calls `rematch_apply=0226B00D` at `0226B48C` with registers
`(buffer,trainer,type_count,Plus)` and stack words `(saved_seed,0226B500,768)`.
The helper entry SP is host-seam SP−104; its complete return is checked at
`0226B490`, including R4–R11/SP. Its result1/2 is **not** the caller's returned
reader R0 (`5EED0001` is the inherited synthetic SDK sentinel).

The standalone selector at `0226B000` exists, but the call is inlined in the
apply function at `0226B150..0226B15E`. It computes
`(saved_seed ^ (saved_seed >> 16) ^ trainer) & 1`. The two fixture seeds
`12345678`/`12345679` select both A/B outcomes for both trainers712/713.
No RNG service is called by the variant core; the actual pre-entry seed setter
and constructor's saved-seed read remain native. Global seed is unchanged at
this boundary. This says nothing about natural seed distribution.

The core validates both variants before selecting, including the unselected
variant's FNV and protected fields. It compares all108 baseline bytes before
copying. The only permitted variant store is `STRB` at `0226B180`, using
buffer R4 and index R1=0..107; the loop at `0226B17E..0226B186` stops at108.
The verifier requires all108 ordered stores and the exact source byte values.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt) in an isolated Python
environment. First run the inert attribution to obtain a private objects
directory. Then, from repository root:

```sh
python source/features/rematch-variants/tools/attribuisci_attivo.py \
  --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --json /private-results/rematch-active-EN.json
```

Repeat with the corresponding IT ROM and objects. JSON must be new and outside
`source` and the retained-objects directory. Existing inputs, symlinks and hard
links cannot be overwritten. Exit0 means the bounded checks passed; exit2 is a
validation refusal. Keep commands, exit code, dependency/source identities and
resource limits with the private JSON. Never publish the ROMs, raw trainer data,
materialized configurations or RAM dumps. No raw RAM dump is needed here.

```sh
PYTHONPATH=source SGP_R4_ROM_DIR=/private-inputs \
  SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
  python source/features/rematch-variants/test/test_active_attribution.py
```

The [tests](../../features/rematch-variants/test/test_active_attribution.py)
expect `r4-EN.nds`/`r4-IT.nds`, or a single `%s` pattern in `SGP_R4_ROM_NOME`.
One CLI method is ROM-free; five Class B methods require both ROMs and objects.
The qualified run executed all six methods without skips. Python `-O` is refused.
The shared inert audit now exposes its initial seed as an overridable class
default; all52 previous complete CPU records/rejections remain identical.

### Fixtures and counterproofs

The [active reader](../../features/rematch-variants/tools/attribuisci_attivo.py)
reuses the bounded constructor/loader audit and code/data maps. It starts the
real constructor at `02073604` and stops before executing the seam resume
`0207363E`. SDK heap/archive/FS remain ABI-checked models. The installed byte is
first verified0, then active1 is written in RAM after FS loads the original
module. Every shadow records exact address, original/replacement bytes and reason.
Frame/config/buffer mutations are controlled pre-apply inputs; a late shadow is
not a natural state observation.

Each language covers:

- Eight positive paths: trainers712/713 × two saved-seed parities × contexts1/2049.
- Twenty negative fixtures: active0/2, Plus0/2, context0/803, enemy index0,
  host buffer disagreement, setup trainer disagreement, format2/count5,
  final baseline-byte disagreement, magic/size/reserved/layout failures,
  and corrupt unselected variants with either unchanged hash or updated hash
  but an illegal protected level, for both selection parities.
- Four counterproofs: opposite saved-seed shadow and partial-copy shadow for
  both parities. Even when renamed as a normal case, their evidence is rejected.

Wrapper gates that refuse before apply are distinguished from core gates that
return0. Baseline-byte107 disagreement reaches the complete baseline check,
performs zero stores and preserves the declared pre-apply input; that input is
a deliberately modified fixture, not the original archive member. Corrupting
the unselected party and updating its FNV still fails its protected-level check.

The partial-copy counter changes only the named RAM instruction
`0226B184: 6C29 → 6B29` (CMP108→107). It performs107 guest stores, yet returns
the same reader value, frees126 and produces **the same full buffer SHA**:
byte107 is already0 in the baseline and all authored parties. The normal image
is unchanged. This demonstrates why successful output hashes cannot replace an
execution trace proving the full108-byte copy.

ISA/width/byte guards retain the explicit counter exception only for that CMP.
Native stores are checked for PC, index, width, address and source value. Reads
from own code are confined to declared module/config, setup, buffer, Plus byte
and bounded stack. Canaries, global seed, unrelated main RAM, actual registry
stores, native helper returns and caller R0/R1/R2/R4–R11/SP are checked separately.
The maximum observed stack depth is352B under a512B oracle bound; instruction
budget200000. These are initialized CPU bounds, not hardware timing claims.

### Result and remaining links

Owned source/binary correspondence is inherited from the exact reconstruction;
this case adds observed native gates, inline selector, full baseline validation,
108-store copy and teardown in initialized active RAM. The ROM remains active0.
Natural phone/Dojo context, full Pokémon construction, later level/PP processing,
all malformed configurations, unsupported trainers, SAVE/cold/device and gameplay
performance remain unqualified. SDK FS/heap/archive models and the inherited
WFC126-only qualification still apply. No gameplay repair or optimization is
implemented. The next useful link is the native constructor consuming the
chosen party after the seam, with its own finite contract and counterproof.
