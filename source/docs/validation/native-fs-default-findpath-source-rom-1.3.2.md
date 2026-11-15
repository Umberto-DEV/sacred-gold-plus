# Native default FindPath prefix: zero models and preserved stack provenance

**Verified host scope:** seven guest runs, two literal input states and 56
comparisons with frozen parent input fields. Two OFF pairs, two causal PUSH
controls and one 104-byte stack-fill control pass. Only the seven-instruction
prefix executes; the nested Translate call is stopped before its first instruction.
No filesystem service model or FSResult is produced by this case.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish the default handler from the higher Find wrapper and a compiled
prefix from the complete component. Start from the actual caller's entry
before its old model, then reconstruct the whole checkpoint forward. Preserve
the uninitialized stack instead of filling new windows to satisfy an oracle.
Freeze the actual input before writing the new predictor or compiling. Check
native write preimages even when a host fault gives identical final CPU/RAM.
Treat a larger observed stack footprint as evidence, without extending the
game's reservation or claiming a resource saving.

## Il materiale più grezzo da cui partire

Use your own complete [native Send/Translate campaign](native-fs-send-translate-native-source-rom-1.3.2.md),
raw files and four-key replay configuration. The current r4 EN input is
152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
localized IT is 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both are IPKE revision 0. Retail Italian IPKI is a different input. Keep ROMs,
extracted code/data, RAM records, captures, saves and BIOS outside the public tree.

The counterpart is `lib/NitroSDK/src/fs/FS_command_default.c::FSi_FindPathCommand`
at reference
[`cb614ad23449d5852b40321dc409c4143872b35c`](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
The source file SHA-256 is
`040f053d87d157231bcd051731eee8bf27768a9103940b6c4016f9cf703ca513`;
the selected definition SHA-256 is
`7d98d8f3ab08dd0ffcdb4c0cece74e5d9e4fd42aa57d4dac6bf8330113116a61`.
Use a clean standalone checkout at that pin. The newer PRET references remain
separate knowledge sources; see the [reference method](../test-bench.md#using-newer-pret-references).

### Component identity and insertion

| Component | RAM address | Current physical ROM offset | Size | SHA-256 |
| --- | --- | --- | ---: | --- |
| Complete retained default FindPath owner | `0x020D6DB0` | `0x000DADB0` | 484 | `70727f66b05763ecfc2b1819f4580f5e0aa029b4cd6cc269776d722fa560e63e` |
| Reconstructed prefix | `0x020D6DB0` | `0x000DADB0` | 28 | `e2b54d82ad94489b669926c98c67c430df38f882e24e68ae646f660686de0233` |

These are retained main ARM9 bytes. Physical and independently decoded reads
agree in both current languages. Retail→base1.1→V4→current comparisons match
both extents in all eight images. This proves byte identity in those windows,
not historical activation. Historical compressed-image physical offsets remain
absent where the reader cannot independently establish them.

The complete owner has 121 decoded ARM starts and ends before the next function
at `0x020D6F94`. Only the 28-byte prefix is reconstructed and executed here.
The recovered [assembly](../../features/trainer-strategy/sorgenti/fs-default-findpath-prefix.S)
has no installer; it does not replace bytes in the ROM. The independent ELF
reader checks ELF32 ARM, section bounds, a single `.text`, exact size/hash and
absence of text relocations. The observed prefix object SHA-256 is
`bb4d30498674de52d7cd15a27a31b134db887b1f92ca78e83efd478862ea5a20`.
This is recovered assembly correspondence, not original Metrowerks C code
generation or a rebuild of the complete default function.

### Caller, ABI and resource lifetime

The outer native Translate dispatches command 4 through table slot 4 to
`0x020D6DB0`; this differs from the higher Find wrapper at `0x020D7FC0`.
At the actual default entry, R0=file, R1=handler address, SP=TOP−336,
LR=`0x020D6984`, CPSR=`0x6000001F`. File status is `0x45`, stored command is 4,
error is BUSY2, and archive flags are `0x213`: the outer Translate is active.

The prefix performs PUSH of r3–r10/LR, allocates 148 local bytes, loads the
path pointer and directory flag, and calls Translate with R1=SEEKDIR2. The
source assignment `arg.seekdir.pos = arg.findpath.pos` addresses the same union
storage at offset 48 and emits no field write. The exact native load PCs are
`0x020D6DBC` for file+60 and `0x020D6DC4` for file+64. No path character is read.
The BL at `0x020D6DC8` targets `0x020D68C0`, with LR=`0x020D6DCC`; both the
disassembler and signed ARM PC+8 branch arithmetic verify that target.

At the stopped nested call, R0 is still file, R1 is 2, SP=TOP−520,
R5 is the path pointer, R6 is the directory flag, R9 is file, and CPSR remains
`0x6000001F`. The stored `FILE.command` remains 4. This is a call boundary, not
a return context: no FSResult/BOOL or completed default-handler ABI is proved.
The nested Translate's original PUSH is checked as a stopped gate and excluded
from execution.

### Stack provenance

TOP is `0x023BEEC0`. PUSH36 followed by SUB148 adds 184 bytes from this entry.
All nine stores are at TOP−372..TOP−336, already inside the parent's captured
416-byte frame. The local 148 bytes remain untouched. Extending the view to
frame520 plus guard56 exposes 104 bytes beyond the parent's frame416+guard56:

| New frame region | Provenance and permitted effect |
| --- | --- |
| Lower guard, TOP−576..TOP−520 | 56 additional bytes from the authenticated whole ancestor; preserved |
| Frame offsets 0..48 | 48 additional ancestor bytes; uninitialized locals, preserved |
| Frame offsets 48..104 | Earlier captured guard56; preserved |
| Frame offsets 104..148 | Earlier captured frame; uninitialized locals, preserved |
| Frame offsets 148..184 | Earlier captured frame; exactly nine native PUSH word stores |
| Frame offsets 184..520 | Earlier captured frame; preserved |

The parent did not capture a whole-RAM hash at default entry. Reconstruct it
from the observed Send initial image and 24 actual/source-matched native writes,
checking every preimage, full entry16 and captured owner windows. Only then
overlay the retained 484-byte default component in place of the old four-byte
gate, recording the code-image delta. No new stack fill is added. The extra104
bytes happen to be A5 in these fixtures; that is a property of the authenticated
ancestor, not a source guarantee or natural boot-state observation.

## I metodi e gli strumenti da usare

Use the project Python environment with ndspy4.2.0, Capstone distribution5.0.9
and Unicorn2.1.4. CPU17 supplies Cortex-A15 instruction semantics; no ARM946
silicon timing or IRQ delivery is inferred. The freezer uses only the standard
library. The qualified compiler is Clang21, SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
with `--target=armv5te-none-eabi -mcpu=arm946e-s -marm`.

Define `PRIVATE` as a fresh private directory outside `source/`, `CLANG` as
the compiler, and `HGSS_REFERENCE` as the clean pinned checkout. Use the completed
Send/Translate campaign's report and configuration. Freeze before the new
compiler/oracle/guest; exporting the same fields later proves equality, not
the earlier chronology.

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_fs_default_findpath_contract.py \
  --parent-report "$PRIVATE/send-translate/matrix.json.gz" \
  --json "$PRIVATE/default-fields.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_default_findpath.py \
  --parent-config "$PRIVATE/send-translate/replay-config.json" --export-components \
  --json "$PRIVATE/default-components.json"
python3 -B source/features/trainer-strategy/tools/compila_fs_default_findpath.py \
  --uscita "$PRIVATE/default-recipe" --cc "$CLANG" --reference "$HGSS_REFERENCE"
```

The builder checks 18 original headers and ARM32 layouts: FSFile72,
FSDirPos12, FSFindPathInfo24, FSDirEntry148 with name offset20, path/directory
flag/result offsets60/64/68, union position offset48 and SEEKDIR2/READDIR3.
For the eight-image lineage, run the independent reader with each language's
own inputs and identity receipts:

```sh
python3 -B source/features/trainer-strategy/tools/rileggi_fs_default_findpath.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" --language EN \
  --recipe-dir "$PRIVATE/default-recipe" --json "$PRIVATE/default-lineage-en.json"
```

Repeat with IT inputs and `--language IT`. To prepare without CPU, then run the
finite native campaign:

```sh
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_default_findpath.py \
  --parent-config "$PRIVATE/send-translate/replay-config.json" \
  --recipe-dir "$PRIVATE/default-recipe" --reference "$HGSS_REFERENCE" \
  --component-receipt "$PRIVATE/default-components.json" \
  --field-contract "$PRIVATE/default-fields.json" --prepare-only \
  --json "$PRIVATE/default-prepare.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_default_findpath.py \
  --parent-config "$PRIVATE/send-translate/replay-config.json" \
  --recipe-dir "$PRIVATE/default-recipe" --reference "$HGSS_REFERENCE" \
  --component-receipt "$PRIVATE/default-components.json" \
  --field-contract "$PRIVATE/default-fields.json" \
  --raw-dir "$PRIVATE/default-raw" --json "$PRIVATE/default.json.gz"
```

Outputs must be fresh, outside `source/`, with report separate from the raw
directory. Preparation reauthenticates the complete ancestor chain and original
recipe/layout/readbacks without another compiler or CPU. Archive its source
identities before the guest. The collector admits only the seven prefix ARM
starts, with two exact native read owners, the nine PUSH word stores and a
32-callback cap. Raw records are saved before the verdict.

### Counterexamples and success criteria

Sixteen historical origins reduce to two literal CPU/RAM interactions; the
earlier default-result0/1 policy no longer exists in this zero-model prefix.
Each interaction gets normal, OFF and `prepush` runs. One representative also
gets a `lower39` run, giving seven guests and 56 frozen **input** comparisons.
No old native prefix output exists to freeze. Activation and output correctness
are separate obligations of the new source oracle and actual raw evidence.

`prepush` is an explicit host fault after recording entry but before executing
the native PUSH. It writes the same nine saved words without changing SP or PC.
Initial CPU/RAM, final CPU/RAM, native flow, reads and counts then converge,
while every native PUSH preimage changes. The positive run has zero host writes;
the fault has nine. Erasing the policy and host ledger must still fail the
native-store comparison. This fault is not an SDK service model or failure path.

`lower39` changes only the 104 newly exposed bytes before the guest starts:
TOP−576..TOP−472. The earlier captured472 bytes remain intact. All native CPU,
flow, reads and store preimages stay equal; the modified bytes remain39 and
whole-RAM hashes differ. This independently checks the absence of a dependency
on those uninitialized bytes and disambiguates the new guard from the old A5
guard. No normalization of differing whole hashes is allowed. OFF preserves
complete CPU/RAM/checkpoints with zero trace projections.

For replay without another guest, use a seven-string JSON object with exactly
`parent_config`, `recipe_dir`, `reference`, `component_receipt`, `field_contract`,
`report`, `raw_dir`. Paths resolve from the invocation directory. The first
points to the parent's four-key configuration; the remaining keys describe the
new inputs and outputs above.

```sh
SGP_FS_DEFAULT_FINDPATH_RECIPE_DIR="$PRIVATE/default-recipe" \
SGP_FS_DEFAULT_FINDPATH_REPLAY_CONFIG="$PRIVATE/default-replay.json" \
  python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_default_findpath_*.py' -v
```

Without private inputs, object/raw-dependent tests explicitly skip. Public
tests cover protected outputs, ELF extent/call identity, all captured input
registers/bytes, causal prefix reconstruction, ABI/stack/writer controls,
literal grouping under reporting-hash collisions and CLI admission. The private
replay rejects forged stopped registers, native preimages and added stack bytes
while forbidding another guest. Source and standard-library freezer tests are
also available through the Class A runner.

### Observations and limits

Each selected path executes seven native contexts, nine native stores and two
reads, with eight code callbacks including the stopped gate and a 184-byte peak.
Fifteen tests pass without skips in 17.312 seconds (913752064-byte OS peak RSS;
10.533 seconds inside unittest). No host writes or service models occur in the normal run. All 56 frozen input
comparisons pass, together with the two OFF pairs, two prepush pairs and lower39
control. The matrix takes 16.880 seconds with 914112512-byte OS peak RSS on this
host. These are host qualification costs, not Nintendo DS performance measures.
Independent raw review verifies 116 current/snapshotted runtime sources, all
seven raw files, 14 streaming whole-image hashes and the 56 input comparisons.

Only entry provenance, these seven instructions and the stopped call ABI are
qualified. Nested Translate, SeekDir/ReadDir, FNT/card access, path parsing and
results, ID/property output, full default return, higher callers and natural
filesystem activation remain open. The older 608-byte ownership boundary is
unchanged; a hypothetical larger caller stack cannot inherit this isolated
qualification. There is no gameplay, ROM/save/ABI/ID/default change or measured
resource saving. Hardware SAVE/cold-restart acceptance remains separate.

The subsequent [nested SEEKDIR dispatch case](native-fs-nested-seekdir-source-rom-1.3.2.md) follows the stopped call to table slot2’s original handler, retaining zero service models and distinct actual/projected input verdicts. It stops before SeekDir execution.
