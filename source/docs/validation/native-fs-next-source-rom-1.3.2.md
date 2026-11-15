# Native NextCommand: empty archive, conditional RUNNING clear and original bridge

The subsequent [ExecuteSync join](native-fs-exec-sync-join-source-rom-1.3.2.md)
follows this actual native return through the stored-error BOOL and original POP;
it preserves the full context rather than restoring older modeled volatile values.

This follows the [native Release/Wakeup composition](native-fs-release-wakeup-source-rom-1.3.2.md)
from its observed return checkpoint. The finite question is whether the original
ExecuteSync LDR/BL delivers the actual archive to native `FSi_NextCommand`, which
clears RUNNING and returns NULL on the qualified empty/no-callback path. Returning
NULL alone does not establish the archive state or execution of that store.
No game, ROM, save, ABI, identifier or default changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Preserve the observed caller checkpoint, including dead stack bytes reused by
the next function. Derive the stack allocation from installed instructions before
assigning ownership. Separate captured spans from a reconstructed full image,
require its observed digest, and keep every parent byte except documented code
and input variations. Execute the original bridge rather than forcing the callee
entry. Seek a valid inactive branch that converges on the same final output;
then demand native contexts, reads and stores as independent evidence. Review
addresses, header offsets, ABI and negative controls independently before guest
execution and review raw results afterwards.

## Il materiale più grezzo da cui partire

Use the eight exact ROM identities in the [Send input table](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Current EN/localized IT are IPKE revision0; retail IT is IPKI revision0.
ARM9 file offset `0x4000`, load `0x02000000`, entry `0x02000800`.

The retained main ARM9 body occupies `[0x020D749C,0x020D76B0)`:532 bytes,
133 ARM starts, no literal pool. Current physical offset `0x000DB49C`.
All eight retail/base1.1/V4/r4 images match full body SHA-256:
`d3785eb030614f3050cb9ef747e3a173e534c40ef5ffa3d75c95acd6fa778e9c`.
The following ExecuteAsync prologue is excluded. Older compressed images require
section decoding; the reader does not invent direct physical offsets for them.
No overlay/autoload lifetime, Plus insertion, data or padding is attributed here.

Source counterpart: `lib/NitroSDK/src/fs/FS_archive_prefix.c::FSi_NextCommand`
at [reference commit cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
File SHA-256 `d359268374ed97b359e4344a820c892382fd23f8923d2895a828175662ae3f2d`;
definition SHA-256 `3a6aa7886dc38416168646a09ce716fc12e68ef77737186854a71dedbd335b39`.
Receipts include18 original headers and definition hashes for canceling,
suspending, suspended, running and file-sync inline tests.

The [recovered assembly](../../features/trainer-strategy/sorgenti/fs-next.S)
has no installer. Object SHA-256
`a158b6550dd32c5db8cd4eea6636aea5a7e275dc5305216d5cc44efaa347c21d`.
Clang21 executable SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`;
ARMv5TE/ARM946E-S/ARM flags and commands are recorded. FSFile72/align4,
FSArchive92/align4 and pointer4 match the pinned headers. This recipe uses the
existing default filesystem ABI flags; no OSThread structure is dereferenced or
qualified here. The earlier [Wakeup aggregate-ABI limitation](native-os-wakeup-source-rom-1.3.2.md#layout-is-part-of-the-evidence)
remains local to that recipe. Original MW C codegen/compiler remains unavailable. The current full-replay receipt gates admit the tested compiler identity above; substituting another compiler requires separate qualification.
Independent ELF text extraction rejects relocations; physical ROM, ndspy and all
532 recovered bytes agree.

### Original caller bridge and state

The parent checkpoint is the actual native Release/Wakeup return fetch
`0x020D7760`. Execute `LDR r0,[r4,#8]` there, then original BL at `0x020D7764`
to Next. Bridge8 bytes `080094e54cffffeb`, SHA-256
`b28aff89430ec51b1e3f555180a3bd25dfde0b309462f6d3994bf77a52a0afb0`.
The original ExecuteSync ELF slice independently confirms the bridge and CMP
return gate `0x020D7768` (`000050e3`), stopped before execution.

TOP=`0x023BEEC0`, file=`0x023BEDD0`, archive=`0x021E3654`, SP=TOP−312.
The observed checkpoint supplies full16 registers. The bridge changes only R0
to the file's actual arc pointer and LR to `0x020D7768`; the collector observes
the resulting full16 at Next entry, without forcing it.

FSArchive fields: flag28, list.next36, stat_q20, **proc84, proc_flag88**.
`flag=0x13` means REGISTER1/LOADED2/RUNNING`0x10`; CANCELING`0x20`,
SUSPENDING`0x40` and SUSPEND8 are absent. `proc_flag=0` excludes IDLE`0x400`
and ACTIVATE`0x200` callbacks. These callback masks belong to **proc_flag**,
not flag. The list is empty. This is the earlier declared source fixture, not
natural boot initialization or native card completion. Cancellation, nonempty
file handling, sync wakeup, suspend and callbacks are not executed.

### Reuse stack bytes without inventing a capture

Installed prologue PUSH `{r3-r9,lr}` saves32 bytes, then SUB SP,#72 reserves the
temporary FSFile. Peak104 places the frame at TOP−416. The72 local bytes are
not read/written on this path. Only the PUSH32 and archive flag store write data.
The caller's live312 bytes remain unchanged. The lower40 bytes in the earlier
352-byte frame are dead and can be reused; freezing that whole frame would be
incorrect. Saved-register preimages come from those observed earlier bytes.

The parent separately recorded frame352 plus guard56:408 bytes. The additional
8 local-prefix bytes and new guard56 form64 bytes outside that observed span.
The tool reconstructs the earlier isolated4MiB image from fillA5, original four
code bodies, LDR gate, actual frame/guard/archive, and **requires the observed
parent whole-RAM digest**. It retains all parent bytes/code and adds Next,
original BL/CMP. The64 bytes are reconstructed and whole-hash verified, not a
new raw capture. `fill39` changes **only those64 bytes** as a declared input
variation. This is bench RAM, not a natural game capture.

Hypothetical complete-caller peak736 exceeds its old608-byte ownership bound.
No earlier caller mask is enlarged and no complete upstream caller is qualified.

## I metodi e gli strumenti da usare

Start at [Linking source to an exact ROM](../test-bench.md#linking-source-to-an-exact-rom)
for the complete-ROM composition route and retained-native versus owned Plus
builds. Commands below run from repository root. Use a project Python environment
with ndspy, Capstone, Unicorn2.1.4 and Clang ARM support. Source/native imports
also require Unicorn in CPU-free preparation. The exporter alone is stdlib-only.
Keep ROMs, raw RAM, saves, BIOS, extracted data and command receipts private.

First reproduce the complete [Release/Wakeup parent](native-fs-release-wakeup-source-rom-1.3.2.md).
Its replay config has string paths `parent_config,field_contract,report,raw_dir`.
A valid parent probe is rejected before heavy preparation. The complete native
parent source/raw/OFF/counter/frozen chain is then authenticated separately.
Freeze the earlier caller/empty-archive invariants before the new guest:

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_fs_next_contract.py \
  --parent-report "$COMPOSITION_REPORT" --json "$PRIVATE/next-fields.json"

python3 source/features/trainer-strategy/tools/compila_fs_next.py \
  --reference "$REFERENCE" --cc "$CLANG" --uscita "$PRIVATE/next-recipe"

python3 source/features/trainer-strategy/tools/rileggi_fs_next.py \
  --retail "$RETAIL_EN" --base "$BASE_EN" --v4 "$V4_EN" --rom "$ROM_EN" \
  --language EN --recipe-dir "$PRIVATE/next-recipe" --json "$PRIVATE/next-lineage-en.json"
python3 source/features/trainer-strategy/tools/rileggi_fs_next.py \
  --retail "$RETAIL_IT" --base "$BASE_IT" --v4 "$V4_IT" --rom "$ROM_IT" \
  --language IT --recipe-dir "$PRIVATE/next-recipe" --json "$PRIVATE/next-lineage-it.json"

python3 source/features/trainer-strategy/tools/attribuisci_fs_next.py \
  --parent-config "$COMPOSITION_REPLAY_CONFIG" --recipe-dir "$PRIVATE/next-recipe" \
  --field-contract "$PRIVATE/next-fields.json" --prepare-only --json "$PRIVATE/next-prepare.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_next.py \
  --parent-config "$COMPOSITION_REPLAY_CONFIG" --recipe-dir "$PRIVATE/next-recipe" \
  --field-contract "$PRIVATE/next-fields.json" \
  --raw-dir "$PRIVATE/next-raw" --json "$PRIVATE/next-report.json.gz"
```

All outputs must be fresh/private and outside `source/`. `--probe` selects one
group/normal policy and is mutually exclusive with `--prepare-only`. Guest runs
require `--raw-dir`. Retain argv, exit codes, input/source/tool hashes and budget
receipts. Here the original16-cell contract predates Next-body inspection, compilation
and guest execution; the later public exporter reproduces all16 cells but uses
honest chronology guidance rather than claiming that export itself proves time.
Known prior inputs/sources are not a blind experiment.

Preparation rechecks the exact current ROMs, Next ELF532, original ExecuteSync
ELF bridge/CMP and retained code. Six initialized code chunks preserve the parent;
only four chunks (bridge, Next, Disable, Restore) are executable in this test.
The unused mapped Release/Wakeup code does not grant permission to execute it.
Ninety-one runtime source identities are snapshotted before the probe and checked
afterwards. Unicorn2.1.4 CPU17 is its Cortex-A15 backend: it checks the admitted instruction semantics, not ARM946 silicon, timing or IRQ delivery. The assembler target ARM946E-S and the host guest backend are separate identities. Grouping requires literal complete initialized4MiB equality plus
entry16, entryPC, CPU17 and Unicorn2.1.4. Sixteen provenance links yield four
states, not16 independent trials.

### Conditional store and falsifiers

Normal empty/running path:62 full register contexts including the two bridge
instructions,62 unique starts,9 stores (PUSH8 + flag store),17 reads,63 hooks
including return fetch,104-byte peak. IRQ leaves are actual native20/24-byte
bodies. R0=NULL, R1=`0x6000009F`, R2=`0x6000001F`, LR=`0x020D76A4`,
CPSR=`0x6000001F`; callee-saved/SP and caller312 are preserved. Normal native STR
`0x020D7640` changes flag word`0x13→3`. No modeled callee or host state write
occurs during guest execution. Live instruction bytes, PC/word owners, frame,
guard and the absolute whole4MiB readback are checked without exclusions.

`not_running` changes only initial archive byte28 from`0x13` to3. It is a declared
source-valid input variation, not the captured parent state or an SDK failure.
It skips six PCs `0x020D7638..0x020D764C`:56 contexts,8 stores,15 reads,57 hooks.
It should converge on **the same full16, frame416, archive92 and absolute final
RAM hash** as normal. A correct final state cannot establish that the RUNNING
store occurred. Disguise positive policy plus initial archive/hash metadata in a
receipt copy; retained actual steps57 versus63 must still reject it.

The skipped rotated-immediate TST#`0x400` forces C=0 only in normal. Full context
checks retain that flag difference until CMP `0x020D767C` converges. It is not
masked away. A second CPU-free receipt mutation preserves NULL but changes the
post-archive flag back to`0x13`, with a consistent forged whole-image digest.
Both native state checking and the earlier frozen archive contract must reject it.
No additional register-shadow guest probe is used.

```sh
python3 -I -S -B -m unittest discover \
  -s source/features/trainer-strategy/test -p 'test_fs_next_freeze.py'
SGP_FS_NEXT_RECIPE_DIR="$PRIVATE/next-recipe" \
SGP_FS_NEXT_REPLAY_CONFIG="$PRIVATE/next-replay.json" \
python3 -m unittest discover \
  -s source/features/trainer-strategy/test -p 'test_fs_next*.py'
```

Private replay config has string paths `parent_config,recipe_dir,field_contract,
report,raw_dir`. Replay binds every raw record to its report, full policy grid,
source/proof/fixtures/groups, OFF/counter and each provenance-cell frozen proof,
without running a guest. Missing private inputs produce explicit skips, not
qualification. Portable tests check config/types, complete parent versus probe,
live312/dead-stack ownership, guard provenance, conditional path counts, rotated
carry and independent contract export. Original fixtures remain read-only.

### Results and coverage

Recovered binary correspondence, source/header/layout identities and eight-image
lineage pass. The first native probe and independent raw/streaming hash review
pass: actual bridge delivery, caller312, RUNNING clear and64-byte provenance are
checked. The16-run native campaign passes across four states and all four
policies, with64 frozen proofs and four exact OFF pairs. All four not-running
controls converge on the same final absolute RAM and full16 as normal while
omitting the conditional store. Fifteen tests pass with zero skips using own
private inputs (13 portable obligations, two private obligations). Campaign
11.636s/876642304 bytes peak OS RSS; CPU-free replay/tests13.040s/875429888 bytes.
Final independent raw review verifies16 records,32 whole-image hashes by streaming,
64 frozen proofs,64-byte fill variation and conditional carry differences, with
no open findings. Source equivalence is limited to the empty running and
declared not-running paths. Original MW C rebuild, callbacks, cancel/suspend,
nonempty work, natural boot/card completion, complete upstream ExecuteSync,
constructor/caller, hardware timing/IRQ delivery and SAVE/cold remain unproved.
Host test costs do not establish a game speedup or resource saving.
