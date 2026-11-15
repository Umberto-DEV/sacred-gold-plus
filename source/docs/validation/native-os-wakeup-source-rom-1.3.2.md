# Native WakeupThread: an empty queue, original IRQ leaves and ABI layout

This follows the empty modeled boundary in [ReleaseCommand](native-fs-release-source-rom-1.3.2.md).
The finite question is whether the installed `OS_WakeupThread` preserves the
actual caller's frame, archive, queue and interrupt control when its head is
NULL, while executing the original native body and IRQ leaves. Thread removal,
rescheduling and a complete filesystem caller remain outside this case.
No game, ROM, save, ABI, identifier or default changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Freeze the earlier model's field invariants before inspecting or executing the
new component. Compare those invariants independently of the new instruction
oracle. A no-op can preserve all fields: require a separate native activation
transcript, including live instruction identities, PUSH preimages and original
return control. Check aggregate layout with unmodified pinned headers; matching
assembly alone cannot prove C ABI compatibility. Seek independent review before
guest execution. Group duplicate inputs only after literal comparison of the
complete initialized CPU memory image and entry registers; report provenance
counts separately from distinct states and guest executions.

## Il materiale più grezzo da cui partire

Use the eight exact ROM inputs, sizes and SHA-256 identities in the
[Send input table](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
All are revision0; retail IT is IPKI, EN and inherited/localized IT are IPKE.
ARM9 file offset is `0x4000`, load `0x02000000`, entry `0x02000800`.
The body is resident ARM9 code, not an overlay, Plus insertion, data or padding.
There is no new overlay lifetime or autoload region.

`OS_WakeupThread` occupies `[0x020D1ECC,0x020D1F34)`:104 bytes,26 ARM starts,
no literal pool. V4 and current physical ROM offset is `0x000D5ECC`.
Older compressed images require section decoding; the reader leaves their direct
physical offset NULL rather than inventing a byte mapping. Body SHA-256:
`25c7d621d6b4d855be6828b9ec8d98162df8ecdda5a22db405caf344aa4102db`.
All eight images match the recovered body. The following WakeupThreadDirect
prologue and later literal pool are outside this extent.

Source counterpart: `lib/NitroSDK/src/os/os_thread.c::OS_WakeupThread` in the
[reference commit cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
File SHA-256 `eb91f80067f2aa05ef0e17d31c3c5c77aec256e7ce1e4e3e2211da1572723ed5`;
definition SHA-256 `7ba9fe60d6218f8c3bbbd0799e628d4453d8e9f79ba6291a541946b22a5c0f40`.
`thread_shared.h` SHA-256 `c5912e365f7a55ab466f1c4db082a5fa9ca1222d69b1709b16bac256369123e2`;
`OS_InitThreadQueue` inline definition SHA-256
`86451bbc5ac1556f6b1b6a6e7a1cb70e3dad1048a9b7ff0772f5e64147ba4369`.
That inline is present in the complete body but skipped on the empty path.

The [assembly recipe](../../features/trainer-strategy/sorgenti/os-wakeup.S)
has no installer. Recovered ELF SHA-256:
`301ee02865717259040b07b1e5f162ef43287f8b91882633cb2b0d1d805426b4`.
The independent ELF reader rejects text relocations. This is a recovered binary
correspondence and a pinned source counterpart, not an original C build.
The reference config names MWCC2.0/sp2p2; that executable and Wine were absent.
No SDK/header patch or historical compiler reconstruction was performed.

### Layout is part of the evidence

Clang21 `clang-2100.4.1.1` executable SHA-256:
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
Both probes use the same18 original pinned headers and ARMv5TE/ARM946E-S/ARM
target. The new recipe explicitly selects `-mabi=apcs-gnu`.

| Layout fact | Default Clang EABI | Explicit APCS GNU compatibility |
| --- | --- | --- |
| scalar `_Alignof(u64)` | 8 | 8 |
| CPContext size/alignment | 32/8 | 28/4 |
| OSContext size/alignment | 104/8 | 100/4 |
| OSThread size/alignment | 200/8 | 192/4 |
| thread state/queue/link.prev/link.next offsets | 104/124/128/132 | 100/120/124/128 |
| OSThreadQueue size; head/tail offsets | 8;0/4 | 8;0/4 |

The installed nonempty body contains offsets100/120/124/128. The flag makes the
aggregate layout compatible; scalar u64 alignment stays8. Layout assertions
cover all facts in the right column and OSContext.cp_context offset72.
An initial default-EABI build failed the offset assertions; a subsequent wrong
scalar-alignment assertion also failed. Both failures were retained and corrected
before the first guest. This establishes compatibility of this local recipe,
not the flags/compiler originally used by Nintendo, and not nonempty runtime
correctness. The source and original headers remain unchanged.

| Call site | Target | Selected execution |
| --- | --- | --- |
| `0x020D1ED4` | DisableInterrupts `0x020D3A38` | five native IRQ instructions |
| `0x020D1EF8` | RemoveLink `0x020D1750` | skipped, headNULL |
| `0x020D1F24` | Reschedule `0x020D18B0` | skipped, headNULL |
| `0x020D1F2C` | RestoreInterrupts `0x020D3A4C` | six native IRQ instructions |

The [qualified IRQ leaves](native-fs-wait-source-rom-1.3.2.md) are20/24 bytes.
The caller is Release BL `0x020D68B0`, actual LR/return fetch `0x020D68B4`
(`MOV r0,r6`), stopped before execution. R0 points to the empty FSFile queue at
file+24; I=1, SYS ARM, F=0. File/ARG/archive fields and source-fixture limitations
are inherited from Release, not natural boot initialization.

TOP=`0x023BEEC0`, file=`0x023BEDD0`, queue=`0x023BEDE8`, archive=`0x021E3654`.
Entry SP=TOP−328; native PUSH `{r3,r4,r5,r6,r7,lr}` adds24 bytes, frame352.
Those24 preimage bytes come from the tail of the **captured** previous guard56.
The new lower guard56 contains24 newly declared fill bytes followed by the first
32 captured guard bytes. Only the newly unknown24 bytes receive the selected
fill. A nonuniform portable fixture checks this provenance equation.
Hypothetical complete-caller peak672 exceeds the old608-byte ownership bound:
this case remains isolated and does not enlarge an earlier mask.

## I metodi e gli strumenti da usare

Start at [Linking source to an exact ROM](../test-bench.md#linking-source-to-an-exact-rom)
for the whole-ROM composition route and the difference between owned Plus
compilation and retained native recipes. The standard-library catalog can locate this guide for a human or another tool:

```sh
python3 -I -S -B source/attribution_cases.py show native-os-wakeup-source-rom-1.3.2 --json
```

This case is guide-only in the catalog; no acceptance state or executable command interface is inferred. Commands below run from repository root.
Use private fresh output directories, Python3, ndspy, Capstone, Unicorn2.1.4 and
Clang with ARM support. Pure contract export needs only Python's standard library;
native/source benches also import Unicorn even during CPU-free preparation.

### Freeze before the new component

First reproduce the complete earlier [Release campaign](native-fs-release-source-rom-1.3.2.md)
with your own ROMs and retained private raw records. Its replay config contains
EN/IT cells `{prepare,report,raw_dir}`; `prepare` contains exactly
`rom,language,parent_report,parent_config,recipe_dir` for that earlier component.
Keep its ancestor config and original fixtures. Before inspecting/building the
new component, export the model's caller-frame/archive/queue/control invariants:

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_wakeup_contract.py \
  --en-report "$RELEASE_EN_REPORT" --it-report "$RELEASE_IT_REPORT" \
  --json "$PRIVATE/wakeup-fields.json"
```

Retain the file hash and chronological command receipt. The exporter is not a
native validator and its output cannot prove its own creation time. The native
CLI later authenticates the complete earlier48-cell matrix per language.
In this case the original contract was frozen before raw inspection, compilation
or guest execution; a later export reproduced all16 cells exactly but is recorded
as a later reproduction. The reserved ordinal7 duplicates ordinal5 bytes: there
is no blind/generalization claim.

### Build, independently read back, prepare and execute

```sh
python3 source/features/trainer-strategy/tools/compila_os_wakeup.py \
  --reference "$REFERENCE" --cc "$CLANG" --uscita "$PRIVATE/wakeup-recipe"

python3 source/features/trainer-strategy/tools/rileggi_os_wakeup.py \
  --retail "$RETAIL_EN" --base "$BASE_EN" --v4 "$V4_EN" --rom "$ROM_EN" \
  --language EN --recipe-dir "$PRIVATE/wakeup-recipe" --json "$PRIVATE/lineage-en.json"
python3 source/features/trainer-strategy/tools/rileggi_os_wakeup.py \
  --retail "$RETAIL_IT" --base "$BASE_IT" --v4 "$V4_IT" --rom "$ROM_IT" \
  --language IT --recipe-dir "$PRIVATE/wakeup-recipe" --json "$PRIVATE/lineage-it.json"

python3 source/features/trainer-strategy/tools/attribuisci_os_wakeup.py \
  --parent-config "$RELEASE_REPLAY_CONFIG" --recipe-dir "$PRIVATE/wakeup-recipe" \
  --field-contract "$PRIVATE/wakeup-fields.json" --prepare-only \
  --json "$PRIVATE/wakeup-prepare.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_os_wakeup.py \
  --parent-config "$RELEASE_REPLAY_CONFIG" --recipe-dir "$PRIVATE/wakeup-recipe" \
  --field-contract "$PRIVATE/wakeup-fields.json" \
  --raw-dir "$PRIVATE/wakeup-raw" --json "$PRIVATE/wakeup-report.json.gz"
```

`--probe` selects only the first group/normal policy; it is mutually exclusive
with `--prepare-only`. A probe report is explicitly marked and cannot replace a
complete campaign in the private replay test. Output files/directories must be
fresh and outside `source/`. The recipe produces no ROM. ROM composition retains
this native ARM9 body; physical/ndspy/ELF agreement proves those installed bytes.

Preparation authenticates earlier source identities, recipes, all raw-equivalent
parent results, OFF/counter proofs, actual service entry16/frame328/archive92 and
preserved guard. Both exact current ROMs are read separately. The84 runtime source
identities are frozen and checked again after execution. A group is shared only
when complete initialized4MiB images compare literally equal, entry16 matches,
and entryPC/CPU17/Unicorn2.1.4 match. Code148 bytes and return gate are inside
that image. The16 provenance cells yield four distinct images and two entry
vectors; four distinct initialized states, rather than16 independent trials, describe coverage.
ON, OFF and fill39 still run separately for every group.

The observer admits only the three exact code bodies and permitted word accesses;
it checks live instruction bytes and never models a callee or writes guest state.
Stop is the original return fetch. Source predictions cover21 full register
vectors, six native PUSH stores/preimages, seven reads,22 hook steps including
the return fetch,24-byte peak and whole4MiB readback without exclusions.
Parent328/archive92/queue8 and R4–R11/SP are preserved, I stays1.
Void residual R0=`0x80`, R1/R2=`0x6000009F`, LR=`0x020D1F30`, CPSR=`0x6000009F`.
These volatile differences are reported; R0 is not a filesystem BOOL.

The frozen-field comparator does not import/call the new predictor. A synthetic
no-op passes its memory/control invariants; separate activation checks reject
missing flow/PUSH/reads/PCs/stack evidence. Additional mutations cover caller RAM,
archive, saved registers, I, original return, report/raw binding, contract hashes,
header/compiler/layout/inline identities. OFF must match every functional field
and the whole-RAM hash with zero projection.

### Tests and private replay

```sh
python3 -I -S -B -m unittest discover \
  -s source/features/trainer-strategy/test -p 'test_os_wakeup_freeze.py'
SGP_OS_WAKEUP_RECIPE_DIR="$PRIVATE/wakeup-recipe" \
SGP_OS_WAKEUP_REPLAY_CONFIG="$PRIVATE/wakeup-replay.json" \
python3 -m unittest discover \
  -s source/features/trainer-strategy/test -p 'test_os_wakeup*.py'
```

Own private `wakeup-replay.json` contains string paths
`parent_config,recipe_dir,field_contract,report,raw_dir`. The replay reconstructs
inputs without guest execution, verifies each raw record and exact policy grid,
then recomputes native, OFF and every provenance-cell frozen proof. Missing private
recipe/replay inputs produce explicit skips, not qualification. Raw RAM, retail
bytes and complete ROMs are not included in Git; fixtures are derived from the
earlier campaign using your own authenticated inputs. Keep command argv, exits,
hashes, source snapshots, resource receipts and independent reviews privately.

### Result and remaining uncertainty

Static source provenance, recovered binary correspondence and eight-image
readback are established. Twelve native runs cover four initialized states, each
with ON/OFF/fill39. The48 earlier-field comparisons pass and all four OFF pairs
match whole RAM and CPU without projection. Fifteen tests pass with zero skips
when the private recipe and replay inputs are supplied:13 portable obligations
and two private obligations. The complete campaign takes8.920s, peak OS RSS
862322688 bytes; CPU-free replay/tests take9.778s, peak861962240 bytes. These
are host tool costs, not game performance. Independent raw review is recorded
locally. Do not infer a complete filesystem or scheduler implementation
from the isolated contract. No original MW C reconstruction, nonempty thread path,
full-caller integration, natural boot/archive activation, IRQ delivery, silicon
timing, save/cold restart or physical-device result is established here.

The reusable additions are the explicit aggregate-layout assertions, independent
earlier-field export/comparison, full-image grouping and raw-bound CPU-free replay.
They improve attribution tools; no game optimization or resource saving follows.

A same-context native Release/Wakeup composition is not qualified by these isolated records. The original608-byte caller ownership bound remains unchanged.

The [single-context Release/Wakeup case](native-fs-release-wakeup-source-rom-1.3.2.md) is a separate composition result. It does not retroactively change the scope of these isolated Wakeup records.
