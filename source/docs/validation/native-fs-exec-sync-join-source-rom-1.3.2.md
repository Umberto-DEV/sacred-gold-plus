# Native ExecuteSync join: stored error, original POP and native volatile registers

This follows the [empty NextCommand case](native-fs-next-source-rom-1.3.2.md).
The finite question is whether the original instructions consume the actual
stored file error after native NextNULL and return to the original Send boundary.
It uses a copied observed checkpoint, not one uninterrupted upstream execution.
No game, ROM, save, ABI, identifier or default changes.

The subsequent [continuous ExecuteSync case](native-fs-exec-sync-native-callees-source-rom-1.3.2.md)
qualifies the wrapper and native callees in one CPU while retaining an explicit
Translate projection. It does not retroactively widen this isolated join case.

**Verified host evidence:** eight native normal/OFF runs over four literal
CPU/image groups,32 frozen provenance-member checks, four OFF comparisons and
two stored-error pairs. Eleven source/export/gate/raw-replay tests pass without
skips. Independent final raw review is recorded separately from these results.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Freeze the actual earlier CPU and memory fields before the new guest. Preserve
volatile registers left by real callees rather than normalizing them to older
model outputs. Reuse a qualified object instead of recompiling unchanged assembly.
Require literal complete CPU/image equality before grouping provenance aliases.
Bind every guard to actual image bytes. Seek the same NULL input with different
stored errors, independently check reads and flags, and keep final-field equality
separate from instruction activation. Review source, ABI, collector and raw data
before broadening the grid.

## Il materiale più grezzo da cui partire

Use the exact [eight source-to-ROM inputs](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire)
and the complete native Next parent with its raw report, frozen contract and
ancestral recipes. Current EN and localized IT are IPKE revision0; retail Italian
IPKI is a separate input. This case independently authenticates current r4 EN/IT
and the retained object. Earlier historical matching keeps its original scope.

| Component | Runtime address | Current physical offset | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| Original ExecuteSync object text | `0x020D7744` | `0x000DB744` |68| `44b2f23b47f01552bd478420b9a14ae0fc2ed6013e7d551d5112075264a43d55` |
| Join tail including excluded Async call | `0x020D7768` | `0x000DB768` |32| `3b188a965b586c94c24e280668f3906c9e22c9f1a70f8ef5b9bed035008f7f87` |
| Original Send stopped POP | `0x020D7928` | `0x000DB928` |4| `8e0f1d53fab1ae8a8a53c4fbaa1c4b34b5fe18c8cb9857fb1dfacf5292204134` |

Independent physical ARM9 and decoded section reads agree with the retained
68-byte ELF text and its suffix. The object SHA-256 is
`768a6e34e5cf2ce6535446110482f27edf3c39c3bd3105956c8037e5049bd011`.
The existing [assembly recipe](../../features/trainer-strategy/sorgenti/fs-exec-sync.S)
has no installer. No new compiler invocation is needed for this unchanged object.
The ancestral compiler/header/recipe checks still apply; original MW C codegen
has not been recovered by this experiment.

The source counterpart is `FS_archive_prefix.c::FSi_ExecuteSyncCommand`, returning
`FS_IsSucceeded(p_file)` from `lib/include/nitro/fs/file.h` (stored error offset20),
at [reference cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
The source file SHA-256 is
`d359268374ed97b359e4344a820c892382fd23f8923d2895a828175662ae3f2d`;
header SHA-256 is
`4e874cfbaa77f546b6f69473ef8bd24afdaab082c5a99f0bb16c37d41f24598f`.
Newer [PRET references](../test-bench.md#using-newer-pret-references) provide useful
higher-level callers, but their wrapped SDK sources are not materialized in the
inspected clones. Their HEADs do not replace this SDK attribution.

### Actual checkpoint and ABI

Start at fetch `0x020D7768`, with R0=NULL, R4=file `0x023BEDD0`,
SP=`0x023BED88` (TOP−312) and LR=`0x020D76A4`. TOP=`0x023BEEC0`;
archive=`0x021E3654`. Preserve every other actual register. In particular,
R1=`0x6000009F`, R2=`0x6000001F`: older modeled callee outputs differ.

Seven executed starts are `7768,776C,7774,7778,777C,7780,7784` in that ARM9
region. The non-NULL BL at `7770` remains in the authenticated bytes but is
excluded from execution. The LDR reads file+20; the POP reads the actual saved
pair at SP/SP+4, restoring R4=archive and PC=`0x020D7928`, with SP=TOP−304.
POP into PC does not change the current LR register. The original Send POP at
that return address is verified but stopped before execution.

| Stored error | Returned BOOL | Final CPSR |
| --- | --- | --- |
|0 SUCCESS|1|`0x6000001F`|
|1 FAILURE|0|`0x2000001F`|

The conditional MOV instructions do not update flags. In the failure case R0 is
zero while Z remains clear from CMP(error,0). Check the complete contexts and
both conditional starts, including the false one, rather than inferring CPSR
from the final BOOL. There are three word reads, zero stores and no new stack
allocation. Frame416, guard56, archive92 and every byte of initial join RAM must
remain unchanged.

### Preserve the parent image

Reconstruct the earlier isolated image using its existing recipe and actual
frame/archive checkpoint; require the observed whole-RAM SHA-256. Retain all
parent bytes, including dead stack and mapped unused code. Add only the missing
28 tail bytes after the existing CMP and four bytes at the stopped Send gate.
No new fill or caller-mask extension is used. The initial join image therefore
has a different digest from the earlier Next image; its own before/after digests
must agree. The guard metadata must match the actual parent image slice.

This preserves the parent's captured-versus-reconstructed provenance. It neither
adds a natural RAM capture nor enlarges the old608-byte full-caller ownership
bound. The earlier hypothetical736-byte aggregate peak remains unqualified.

## I metodi e gli strumenti da usare

First reproduce the complete [Next parent](native-fs-next-source-rom-1.3.2.md).
All commands run from repository root; relative JSON paths resolve there.
Keep inputs, raw output and receipts outside `source/` and Git. The parent's
replay configuration has five string fields:

```json
{
  "parent_config": "evidence/release-wakeup/replay.json",
  "recipe_dir": "evidence/next-recipe",
  "field_contract": "evidence/next-fields.json",
  "report": "evidence/next-report.json.gz",
  "raw_dir": "evidence/next-raw"
}
```

Export earlier final-field expectations with the standard-library-only tool:

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_fs_exec_sync_join_contract.py \
  --parent-report "$NEXT_REPORT" --json "$PRIVATE/join-fields.json"
```

The export uses earlier observed CPU/memory plus BOOL/POP semantics without
importing the new join predictor. It does not prove its own chronology or the
authenticity of an arbitrary parent. In this campaign it predates the new
predictor/guest, after body inspection; inputs are known, not blind.

The complete producer requires the existing project Python environment with
ndspy, Capstone and Unicorn2.1.4, even for CPU-free preparation. Parent receipts
retain their qualified Clang21 identity
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`;
an alternate compiler requires its own qualification. This join CLI has no new
`--cc` or `--recipe-dir`: it reads the qualified object through the parent chain.

```sh
python3 source/features/trainer-strategy/tools/attribuisci_fs_exec_sync_join.py \
  --parent-config "$NEXT_REPLAY_CONFIG" --field-contract "$PRIVATE/join-fields.json" \
  --prepare-only --json "$PRIVATE/join-prepare.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_exec_sync_join.py \
  --parent-config "$NEXT_REPLAY_CONFIG" --field-contract "$PRIVATE/join-fields.json" \
  --raw-dir "$PRIVATE/join-raw" --json "$PRIVATE/join-report.json.gz"
```

Every output must be fresh. `--probe` selects the first group/normal only;
it is mutually exclusive with `--prepare-only`. Execution requires `--raw-dir`.
Preparation rejects an incomplete/probe parent before expensive ancestor replay.
It checks current input/source/ELF/ROM identities and complete parent raw,
OFF/counter/frozen evidence without rerunning that parent's guest.

Complete CPU registers and literal full RAM establish grouping; SHA-256 is only
reported as an identifier. The collector admits only the seven original starts,
the three declared reads and zero writes. No host state setter runs during guest
execution. Unicorn CPU17 is its Cortex-A15 backend: admitted instruction semantics,
not ARM946 timing, IRQ delivery or hardware behavior.

The new replay configuration has four string fields:

```json
{
  "parent_config": "evidence/next-replay.json",
  "field_contract": "evidence/join-fields.json",
  "report": "evidence/join-report.json.gz",
  "raw_dir": "evidence/join-raw"
}
```

Run portable source/field/gate tests and the optional private CPU-free raw replay:

```sh
SGP_FS_EXEC_SYNC_JOIN_REPLAY_CONFIG="$JOIN_REPLAY_CONFIG" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_exec_sync_join_*.py' -v
```

Without private inputs, that replay test skips explicitly; it is not passed
coverage. Retain exact argv, exit codes, source snapshots, hashes and resource
limits. This campaign uses180s per command,1GiB OS peak RSS,2MiB logs,16MiB case
output and1GiB planned disk peak, retaining at least10GiB free.

### Counterexamples and limits

Two stored-error states already occur in the qualified parent inputs with the
same actual NextNULL entry registers. These are declared source-fixture states,
not naturally observed SDK failures. Compare their real readsets: only the
file-error value may differ; the two saved POP reads must agree. Do not claim
their entire initial RAM images are byte-identical. A metadata disguise must
fail on the native returned context. Non-NULL R0 would enter excluded Async and
is not a valid failure control for this contract.

Keep source-derived full-context/read verification separate from the independent
frozen final-field comparator. Reject altered BOOL, flags, saved R4, SP, LR or
target; omitted conditional starts/reads; and coherently forged guard metadata.
Final values pre-applied without the seven native instructions cannot establish
activation. Compare ON/OFF using identical CPU and whole RAM without projections.

The first verified probe has seven contexts/eight fetches including the stopped
gate, three reads and zero writes; it passes four provenance-member field checks.
That is one guest, not four. The subsequent complete grid contains eight guests:
four normal/OFF pairs with zero RAM projection. Its32 frozen checks cover sixteen
provenance members under two observer policies; they are not32 independent trials.
Both actual stored-error pairs return BOOL1/0 with identical NextNULL entry
registers and the same readset except the file-error value. Disguising the failure
as success is rejected on the native returned context. Raw replay rejects altered
BOOL, aligned R4/SP/LR, Z flag, omitted false conditional start/read, forged guard
metadata, and frame/archive changes with coherently recomputed whole-RAM hashes.
The source-derived checks and earlier frozen fields both reject the memory edits.

Measured command receipts for the qualified source snapshot:

| Check | Elapsed host time | OS peak RSS | Result |
| --- | --- | --- | --- |
| CPU-free preparation after literal-grouping correction |11.135s|877576192B|16 origins,4 groups; no compiler/guest |
| First probe |10.879s|877805568B|1 normal guest,4 member checks |
| Complete normal/OFF matrix |10.921s|877412352B|8 guests,4 OFF,32 fields,2 error pairs |
| Source/export/gates and CPU-free private replay |11.883s|877772800B|11 tests,0 skips; no new guest |

The94 runtime source hashes are archived before the first guest and rechecked
against every report. The earlier16-cell contract is retained unchanged. Two
pre-guest bench findings were corrected and their failing controls preserved:
guard metadata is bound to actual RAM, and grouping compares literal images
rather than digests alone. These are verification-tool repairs, not game fixes.

There is no new original-MW C build, full ExecuteSync/Send return, natural
filesystem completion, card/thread/scheduler, SAVE/cold or physical hardware
result, game correction or resource gain here. The suffix still has zero new
stack allocation; it does not qualify the upstream aggregate ownership bound.
