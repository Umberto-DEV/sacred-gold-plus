# Native ReleaseCommand: unlinking, error assignment and a void return

This follows [ExecuteSync](native-fs-exec-sync-source-rom-1.3.2.md) into its
modeled Release boundary. The finite question is whether the exact installed
Release body unlinks the file, clears status bits, assigns the actual translated
result and restores interrupt control, while preserving command4. WakeupThread
remains an explicit empty-queue value boundary. No game/ROM/save/ABI/ID change.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Reconstruct source/recipe→ELF→ROM and ROM→caller→ABI→source. Separate native
stores from input projections and modeled services. A store that happens to write
the same value already present needs instruction/register/preimage evidence;
a deliberately different old error can falsify “keep the old field”. Treat a
void function's residual register as evidence of ABI behavior, never as a BOOL.
Require independent raw review and preserve the distinction between an isolated
source fixture and natural filesystem completion.

## Il materiale più grezzo da cui partire

Supply the eight exact ROM inputs in the
[Send input table](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
All are revision0. EN and inherited/localized IT are IPKE; retail IT is IPKI.
ARM9 file offset`0x4000`, load`0x02000000`, entry`0x02000800`. Use section decoding
for older compressed images rather than inventing a direct physical offset.

`FSi_ReleaseCommand` occupies`[0x020D6864,0x020D68C0)`:92 bytes,23 ARM starts,
no literal pool. Current physical ROM offset is`0x000DA864` in main uncompressed
ARM9; no overlay/autoload lifetime is introduced. Full body SHA-256:
`658daf608846bdeca5f8d48b8b0ea7d46280ebcd2ef783fce8b5f9e12735f568`.
All eight retail/base1.1/V4/current images match. This is retained HGSS native
code, not inserted Plus code or padding. The following Translate prologue is
outside the body.

Source counterpart: `lib/NitroSDK/src/fs/FS_command.c::FSi_ReleaseCommand` at
[reference commit cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
Source file SHA-256`07333027376e89d3ecc243b0022d089f9c3153cfe4226ef433e086cbe9777e60`;
definition SHA-256`9c23fd8514c97f05b746bf4c52b9258302f8ab15192c48c334dc69a78887373c`.
`fs_private.h` SHA-256`b3abfe01ae14a8b64fd68372a4e0646f975373dd296626d4396ffc113c3a122c`;
its one-line `FSi_CutFromListCore`/`FSi_CutFromList` definitions are hashed separately
in the recipe receipt. The narrow extractor accepts unique complete one-line
definitions and rejects duplicates/prototypes/multiline bodies; it is not a
general C parser.

The [assembly](../../features/trainer-strategy/sorgenti/fs-release.S) is a
recovered attribution recipe, with no installer. Original MW compiler/objects
remain unavailable. Authenticated Clang21 targets ARMv5TE/ARM946E-S/ARM mode;
receipts record executable SHA/version, flags, commands, exits,18 original headers
and ARM32 layout assertions. Recovered object SHA-256:
`7bf95cfa7e9f0abca8f3cafccc2f276a66725a2331d0f6b8e6b4588ed423526a`.
The independent ELF reader rejects text relocations; raw ROM mapping and ndspy
section decoding must agree with all92 bytes.

| Native call | Target | Selected ABI |
| --- | --- | --- |
| BL`0x020D6870` | Disable`0x020D3A38` | native qualified IRQ leaf |
| BL`0x020D68B0` | Wakeup`0x020D1ECC` | R0=file+24, empty thread queue, I=1 |
| BL`0x020D68B8` | Restore`0x020D3A4C` | R0=saved incoming I bit0 |

The [IRQ leaves](native-fs-wait-source-rom-1.3.2.md) are retained native20/24-byte
components with independent recovered objects/readback. FSFile is72 bytes, fields
prev0/next4/arc8/stat12/command16/error20/queue24/prop32/arg48. FSArchive is92 bytes,
flag28/list.next36. BUSY1, CANCEL2, SYNC4, ASYNC8 and OPERATING`0x40` form clear
mask`0x4F`. Two new assertion names were initially reversed; the original header
caught the error before any Release guest execution. Failed logs/source are
retained locally. This did not change the native mask or preceding cases.

Inputs come from the actual isolated ExecuteSync `services[1].entry`,
`services[1].frame_before` (312 bytes), `services[1].archive_before` (92 bytes),
plus the last16 preserved guard bytes. Select both normal and Translate-failure
rows, producing eight fixtures per language from four Plus/seed cells. These are
actual native caller contexts after a **modeled** Translate error projection.
They do not establish native translation or natural boot archive state.

TOP=`0x023BEEC0`, file=`0x023BEDD0`, archive=`0x021E3654`, SP=TOP−312,
frame=TOP−328. File is linked after the archive sentinel, stat`0x45`, command4,
error equal to translated R1=0 or1, empty queue. Archive flag`0x13` and list.next
point to the file. Its original no-ACTIVATE source fixture remains explicit.
Native PUSH saves R4/R5/R6/LR,16 bytes. A hypothetical complete caller peak648
exceeds608; isolated coverage does not enlarge the old guard or ownership mask.

## I metodi e gli strumenti da usare

### Source and byte reconstruction

Use Python3, ndspy, Capstone and Clang with ARM support. Supply a clean reference
checkout at the pinned commit and fresh private output directories outside
`source/`. ROMs, extracted data, RAM, saves, BIOS and personal paths stay local.

```sh
python3 source/features/trainer-strategy/tools/compila_fs_release.py \
  --uscita "$SGP_RELEASE_RECIPE" --cc "$SGP_CLANG" --reference "$SGP_HGSS_REFERENCE"
python3 source/features/trainer-strategy/tools/rileggi_fs_release.py \
  --retail "$SGP_RETAIL" --base "$SGP_BASE11" --v4 "$SGP_V4" \
  --rom "$SGP_ROM" --language EN --recipe-dir "$SGP_RELEASE_RECIPE" \
  --json "$SGP_OUT/release-lineage-EN.json"
SGP_FS_RELEASE_RECIPE_DIR="$SGP_RELEASE_RECIPE" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_release_recipe.py' -v
```

Repeat lineage for IT. Three recipe tests cover output ownership, the narrow
inline extractor and independent92-byte ELF/23-start/three-BL readback. Missing
private objects cause an explicit skip. Full qualification requires zero skips.
One producer at a time;180s/command,1GiB peak RSS,2MiB log,16MiB case,1GiB disk
peak and at least10GiB free after peak. Keep argv, exit codes, hashes, snapshots,
raw faults and OS peak RSS. No complete ROM build or emulator installation is
needed for byte comparison.

### Finite semantics and counter

The selected prev pointer is the archive sentinel and next is NULL. Native code
stores zero to archive.list.next, file.prev and file.next, clears stat`0x4F`, and
stores the R1-derived R4 to error. Command4, properties, ARG and queue remain
unchanged. The false STRNE next-link hook is present without a memory effect.
Archive RUNNING remains set; Next has not run in this case.

Wakeup is **one value-only model with no RAM writes**, admitted only for the
actual empty queue. Pinned `os_thread.c::OS_WakeupThread` has file SHA-256
`eb91f80067f2aa05ef0e17d31c3c5c77aec256e7ce1e4e3e2211da1572723ed5` and definition
SHA-256`7ba9fe60d6218f8c3bbbd0799e628d4453d8e9f79ba6291a541946b22a5c0f40`.
An empty head skips thread mutation and rescheduling in that source. Its native
interrupt instructions, full register behavior, scheduler and nonempty queues
are excluded here. The model may return0/all-ones and clobber permitted volatile
registers/flags while preserving mode/I, callee-saved registers and SP.

Normal inputs already have error=R1. The `stale_error2` control declares only an
initial error-word projection to BUSY2, preserving the authenticated base fixture
and actual caller ABI. It is not natural post-Translate state. The native STR
must expose before2/valueR1 and overwrite that word with0 or1. Final frame/archive,
registers, flow, reads, model records and complete RAM converge with baseline;
initial RAM and that native store preimage differ. This tests assignment rather
than inferring causality from an idempotent write. A positive metadata disguise
must still reject the retained native store preimage.

Release is void. Normal residual R0 is`0x80`, the I bit observed by Restore before
restoration; it is neither a filesystem BOOL nor FSResult. PC returns to original
ExecuteSync`0x020D7760`, LR remains`0x020D68BC`; R4–R11/SP are preserved. Normal
CPSR is`0x6000001F`, R1=`0x6000009F`, R2=`0x6000001F`. Void Wakeup poison changes
only context`0x020D68B4`; MOV R0,R6 discards it. Clobber R3/IP persists; native
Restore preserves modeled NZCV while clearing I back to0.

### Authenticated preparation and isolated execution

First reproduce the linked ExecuteSync/Send/Find-caller cases. Reuse the local
ExecuteSync replay-config schema documented in its guide. `--parent-config`
selects `[EN|IT].prepare` only, requiring exactly its12 keys, matching ROM and
language, string paths and an optional null capture_source; the file is bounded
to512KiB. It contains personal local paths and must remain private. The CLI checks
all32 ExecuteSync parent cells,74 source identities, source proofs, OFF/counters
and their ancestors without repeating their guests. It reads its own Release
ELF and both previously qualified IRQ objects independently from the supplied
Wait recipe directory.

```sh
python3 source/features/trainer-strategy/tools/attribuisci_fs_release.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_EXEC_REPORT" \
  --parent-config "$SGP_EXEC_REPLAY_CONFIG" --recipe-dir "$SGP_RELEASE_RECIPE" \
  --prepare-only --json "$SGP_OUT/release-prepared-EN.json.gz"
```

Prepare-only executes no guest and is mutually exclusive with probe. For a
one-cell probe replace `--prepare-only` with
`--probe --raw-dir "$SGP_OUT/release-probe-raw"` and select a fresh report filename.
For48 cells per language omit `--prepare-only`, add a fresh `--raw-dir` and report.
Repeat with IT. Execution needs Unicorn2.1.4/model17 (Cortex-A15): admitted
instruction semantics only, not ARM946 silicon, timing or interrupt delivery.

The collector initializes CPSR before banked registers, whitelists all live ARM
bytes and exact data owners, and captures raw faults/halts before source
assessment. A source oracle predicts34 full16-register native contexts, nine
stores, seven reads, one modeled call and36 steps including the original stopped
return fetch. Two native IRQ leaves supply11 of those contexts. Whole4MiB RAM
is reconstructed from fill, actual frame328, archive92, code92+44, original
stopped LDR and one own model NOP. Source-derived hashes must match actual CPU
readback, with no RAM exclusion. OFF omits native transcripts while preserving
all functional registers, model records and whole RAM with zero projection.

### CPU-free replay

Provide a private JSON config with EN and IT keys. Each value contains `report`,
`raw_dir` and `prepare`. `prepare` has exactly five keyword arguments: `rom`,
`language`, `parent_report`, `parent_config`, `recipe_dir`. All except language
are local path strings. `parent_config` is the preceding ExecuteSync replay-config
already described above; no new copy of ROMs or raw data is needed. Point `report`
to the final48-cell matrix and `raw_dir` to its48 numbered gzip records.

```sh
SGP_FS_RELEASE_REPLAY_CONFIG="$SGP_RELEASE_REPLAY_CONFIG" \
SGP_FS_RELEASE_RECIPE_DIR="$SGP_RELEASE_RECIPE" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_release*.py' -v
```

Without private artifacts, replay/object tests explicitly skip. Complete
qualification requires zero skips. Replay checks79 runtime identities, parent
proof/fixture reconstruction, exact48-cell grids, raw/report equality, strict
register/store/read/model types, whole RAM and causal controls. Every forged
receipt test must first prove that its typed JSON differs from the original,
preventing ineffective zero-to-zero mutations.

### Results and limits

Byte correspondence and finite pure semantics are qualified. Eight historical
bodies match the recovered ELF. Three recipe tests pass with zero skips;
five source tests pass and independent opcode review checks128 pure predictions
from16 actual parent origins. Prepare EN authenticates all inputs without guest
execution,5.803s/658440192-byte peak RSS.

The final96 isolated runs cover eight actual inputs per language and six policies:
normal, OFF, stale error2, void Wakeup all-ones, volatile clobber and fill39.
EN takes6.375s/658472960-byte OS peak RSS; IT6.686s/671776768 bytes, including
ancestor preparation. All79 runtime source identities, native collector and
predictor remain unchanged from the first probe through both matrices. The80 ON
runs each expose34 native full16-register contexts, nine stores, seven reads,
one Wakeup boundary and36 steps. Sixteen OFF runs preserve exact registers,
model records and whole RAM with zero projection.

The16 stale-input controls change only initial error byte108 and its native
STR preimage (before2→R1-derived0/1). Complete final RAM, flow, reads, API registers
and Wakeup records equal baseline. Disguising the policy and initial metadata
as baseline still fails with `Release source-derived stores`. Void poison is
ignored after context`0x020D68B4`; clobber R3/IP/flags persists as predicted while
IRQ control is restored. Both translated results return residual R0=`0x80`,
confirming that it cannot be interpreted as a filesystem BOOL. Fill39 preserves
owned frame/archive outputs and changes the declared unowned image.

Fifteen tests pass with zero skips: ten portable and five requiring private
objects/reports,8.960s/851918848-byte OS peak RSS. They authenticate both matrices,
all96 preserved raw records, strict typed receipts,16 forged-evidence variants,
OFF, stale-input causality, void/clobber and fill controls. No compiler is invoked
during the matrices or replay. Independent reviews cover source, recipe/layout,
oracle, collector, preparation, actual probe and public reproduction instructions.

| Conclusion | Coverage |
| --- | --- |
| Documented provenance | pinned native source/inline helpers/original headers, actual isolated ExecuteSync inputs |
| Recovered binary match |92-byte recovered assembly/ELF, eight image readbacks; original MW build missing |
| Finite source semantics | selected linked file/empty queue, native IRQ, declared Wakeup boundary and stale-error input control |
| Observed activation |96 isolated calls from16 actual caller contexts; no natural or complete-caller execution |
| Unattributed links | native Wakeup/scheduler/nonempty queues, whole-caller integration, natural archive, translation/ID delivery/full completion |

No game memory recovery, speedup, hardware/SAVE/cold restart or naturally executed
filesystem completion is established. The next executable link should remove one
explicit remaining boundary with its own source, raw input and ownership proof.


## Independent comparison with the earlier frozen contract

A later follow-up compares the earlier ExecuteSync report's retained Release
model with these native Release records using the
[standalone comparator](../../features/trainer-strategy/tools/confronta_release_holdout.py).
It imports no project predictor, collector or oracle, runs with Python3.9+
standard libraries and executes no guest or compiler. Supply your own exact
parent/child reports from the preceding reproduction steps:

```sh
python3 -I -S -B source/features/trainer-strategy/tools/confronta_release_holdout.py \
  --model-report "$SGP_EXEC_REPORT" --native-report "$SGP_RELEASE_REPORT" --json
```

Repeat for IT. The child must name the exact parent file SHA-256, every fixture
must bind that digest, source ancestry must retain the74→79 capture identities,
and the complete32/48-cell policy grids must be structurally consistent. The
comparison selects eight normal Release inputs per language (four Plus/seed
cells, translated result0/1), not all96 source-oracle runs.

For each selected input, it checks the actual entry16, the complete312-byte
parent frame before/after, archive92 and all five field-write events
(address/width/preimage/value). The later native PUSH16 is verified independently
against saved R4/R5/R6/LR and its four store events, rather than hidden by a mask.
The native STR error witness must consume the R1-derived R4 and actual file R5.
Full328/92 Wakeup snapshots must equal the actual native state and have no
modeled RAM writes. Callee-saved registers/SP and return control are checked.

The retained earlier Release-error fault provides four negative contracts per
language: identical input and void-return metadata, with only stored error1
instead of0. The comparator requires that exact fault shape and the expected
frame-contract rejection; a malformed ABI or empty snapshot cannot count as a
successful negative control. The original16 matched pairs and eight rejected
fault contracts require no new guest campaign.

Both native result0/1 paths leave R0=`0x80`; compared with the earlier void model,
R0/R1/R2/LR/CPSR differ. These volatile/residual differences are reported explicitly,
not normalized into full register equality. Original native replay remains a
prerequisite. Whole isolated RAM differs in code/setup/extra stack; only the named
frame/archive/store contract is compared. This is a retrospective comparison with
an earlier frozen contract, not a preregistered blind experiment or proof of
joined caller/natural filesystem execution.

For CPU-free regression tests, provide a private JSON config with EN and IT keys,
each containing `model_report` and `native_report` local path strings:

```sh
SGP_RELEASE_HOLDOUT_CONFIG="$SGP_HOLDOUT_CONFIG" \
python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p test_release_contract_holdout.py -v
```

Without private reports, two tests explicitly skip; complete holdout qualification
requires zero skips. This separate test filename does not add dependencies or
skips to the earlier `test_fs_release*.py` replay interface. Synthetic tests cover
owned stack bytes, field preimages/types, native source-register witness, fixture
provenance, bound Wakeup snapshots and non-vacuous negative controls. These checks
strengthen the method without changing the game or relabeling the original cases.

The [empty Wakeup follow-up](native-os-wakeup-source-rom-1.3.2.md) qualifies that boundary separately; it does not retroactively turn these isolated Release records into a complete native caller.
